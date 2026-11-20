"""Universal async fetcher: httpx + asyncio, robots respect, per-host 1 rps.

ISP proxy comes ONLY from env — never committed:
  source ~/.config/bentstraw/proxy.env  # proxy user/pass/endpoint
Without proxy env: direct fetch at concurrency 4. With proxy: concurrency 16.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import time
import urllib.parse
import urllib.robotparser as robotparser
from pathlib import Path

import httpx
from bs4 import BeautifulSoup  # noqa: F401  (re-exported for adapters)

TIMEOUT = 30.0
RETRIES = 2
PROXY_CONCURRENCY = 16
DIRECT_CONCURRENCY = 4
HOST_DELAY = 1.0  # per-host min seconds between requests
PROXY_ENV_FILE = Path.home() / ".config" / "bentstraw" / "proxy.env"

_robots_cache: dict[str, robotparser.RobotFileParser | None] = {}
_host_last: dict[str, float] = {}
_host_locks: dict[str, asyncio.Lock] = {}


def load_proxy_env(path: Path = PROXY_ENV_FILE) -> None:
    """Load KEY=VAL lines into os.environ (no overwrite, never written to repo)."""
    try:
        text = path.read_text()
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        if k and v:
            os.environ.setdefault(k, v)


def proxy_url() -> str | None:
    user = os.getenv("DECODO_USER")
    pw = os.getenv("DECODO_PASS")
    ep = os.getenv("DECODO_ENDPOINT")  # e.g. http://proxy-gateway.example:10001
    if user and pw and ep:
        if "://" not in ep:
            ep = "http://" + ep
        scheme, _, host = ep.partition("://")
        return f"{scheme}://{urllib.parse.quote(user, safe='')}:{urllib.parse.quote(pw, safe='')}@{host}"
    return None


def has_proxy() -> bool:
    load_proxy_env()
    return proxy_url() is not None


async def robots_allowed(client: httpx.AsyncClient, url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in _robots_cache:
        rp: robotparser.RobotFileParser | None = None
        try:
            r = await client.get(f"{base}/robots.txt", timeout=10.0)
            if r.status_code == 200:
                rp = robotparser.RobotFileParser()
                rp.parse(r.text.splitlines())
        except Exception:
            rp = None  # unparseable/unreachable -> allow, politeness via rate limit
        _robots_cache[base] = rp
    rp = _robots_cache[base]
    return True if rp is None else rp.can_fetch("*", url)


async def _throttle(host: str) -> None:
    lock = _host_locks.setdefault(host, asyncio.Lock())
    async with lock:
        wait = HOST_DELAY - (time.monotonic() - _host_last.get(host, 0.0))
        if wait > 0:
            await asyncio.sleep(wait)
        _host_last[host] = time.monotonic()


async def fetch_one(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> str:
    async with sem:
        if not await robots_allowed(client, url):
            return ""
        await _throttle(urllib.parse.urlsplit(url).netloc)
        for attempt in range(RETRIES + 1):
            try:
                r = await client.get(url, timeout=TIMEOUT,
                                     headers={"User-Agent": "bentstraw-bot/0.1 (+https://bentstraw.com)"})
                if r.status_code == 200:
                    return r.text
                if r.status_code in (429,) or r.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return ""  # 4xx (exc. 429): don't retry
            except Exception:
                if attempt == RETRIES:
                    return ""
                await asyncio.sleep(2 ** attempt)
        return ""


async def _fetch_all(urls: list[str], concurrency: int, proxy: str | None) -> list[str]:
    sem = asyncio.Semaphore(concurrency)
    kwargs: dict = {"timeout": TIMEOUT, "follow_redirects": True}
    if proxy:
        # httpx>=0.28 uses `proxy=`, older uses `proxies=`
        kwargs["proxy" if httpx.__version__ >= "0.28" else "proxies"] = proxy
    async with httpx.AsyncClient(**kwargs) as client:
        return await asyncio.gather(*(fetch_one(client, u, sem) for u in urls))


def fetch_many(urls: list[str]) -> list[str]:
    """Fetch urls concurrently. Returns html per url ("" on skip/fail), input order."""
    proxy = proxy_url() if has_proxy() else None
    concurrency = PROXY_CONCURRENCY if proxy else DIRECT_CONCURRENCY
    _host_locks.clear()  # locks bind to a loop; never reuse across asyncio.run calls
    return asyncio.run(_fetch_all(urls, concurrency, proxy))


def main() -> None:
    ap = argparse.ArgumentParser(description="Bentstraw universal fetcher (robots-aware, rate-limited).")
    ap.add_argument("--urls", nargs="*", default=[], help="URLs to fetch")
    ap.add_argument("--out", default="", help="Dump raw html to this dir (resume: skip existing files)")
    ap.add_argument("--proxy-env", default=str(PROXY_ENV_FILE), help="Env file with proxy creds (never in repo)")
    args = ap.parse_args()
    load_proxy_env(Path(args.proxy_env))
    print(f"proxy={'on' if proxy_url() else 'off'} concurrency={PROXY_CONCURRENCY if proxy_url() else DIRECT_CONCURRENCY}")
    if not args.urls:
        return
    todo, cached = [], 0
    outdir = Path(args.out) if args.out else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)
    for u in args.urls:
        p = outdir / (urllib.parse.quote_plus(u) + ".html") if outdir else None
        if p and p.exists():
            cached += 1
            todo.append(None)
        else:
            todo.append((u, p))
    pages = fetch_many([u for t in todo if t for u, _ in [t]])
    it = iter(pages)
    ok = 0
    for t in todo:
        if t is None:
            continue
        u, p = t
        html = next(it)
        if html and p:
            p.write_text(html)
        ok += bool(html)
    print(f"fetched={ok} skipped={cached} failed={len(args.urls) - ok - cached}")


if __name__ == "__main__":
    main()
