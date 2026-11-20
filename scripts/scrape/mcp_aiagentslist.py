"""Scrape https://aiagentslist.com/mcp-servers -> data/seed/mcp-aiagentslist.json.

Self-contained httpx+asyncio fetch (universal.py is owned by another agent):
concurrency <= 8, timeout 30s, retries 2. Decodo proxy ONLY from env
(DECODO_USER/DECODO_PASS/DECODO_ENDPOINT), fallback to direct on failure.
Never print or persist credentials.

Rows: {id:"mcp/<slug>", kind:"mcp", name, blurb, url, install, tags, past:false}
Usage: python3 scripts/scrape/mcp_aiagentslist.py [--max-pages N] [--limit N]
"""

import asyncio
import json
import os
import re
import sys
from html import unescape
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BASE = "https://aiagentslist.com"
LISTING = BASE + "/mcp-servers"
UA = {"User-Agent": "Mozilla/5.0 (compatible; BentstrawBot/1.0; +https://bentstraw.com)"}
TIMEOUT = 30.0
RETRIES = 2
CONCURRENCY = 8
SLUG_RE = re.compile(r"^/mcp-servers/([a-z0-9-]+)$")
SKIP = {"categories", "servers"}


def proxy_url():
    user = os.environ.get("DECODO_USER", "")
    pw = os.environ.get("DECODO_PASS", "")
    ep = os.environ.get("DECODO_ENDPOINT", "")
    if user and pw and ep and "$" not in ep:
        return f"http://{user}:{pw}@{ep}"
    return None


async def fetch(client, sem, url):
    for attempt in range(RETRIES + 1):
        try:
            async with sem:
                r = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
            if r.status_code == 200 and r.text:
                return r.text
        except Exception:
            pass
        await asyncio.sleep(1)
    return None


def listing_slugs(html):
    soup = BeautifulSoup(html, "html.parser")
    slugs = []
    for a in soup.find_all("a", href=True):
        m = SLUG_RE.match(a["href"])
        if m and m.group(1) not in SKIP and m.group(1) not in slugs:
            slugs.append(m.group(1))
    return slugs


def total_pages(html):
    m = re.search(r"totalPages:(\d+)", html)
    return int(m.group(1)) if m else 1


def pick_install(soup):
    pres = [unescape(p.get_text()) for p in soup.find_all("pre")]
    codes = [unescape(c.get_text()) for c in soup.find_all("code")]
    blobs = pres + [c for c in codes if len(c) > 20]
    if not blobs:
        return ""
    for b in blobs:
        if '"mcpServers"' in b:
            return b.strip()[:2000]
    for b in blobs:
        if re.search(r"\b(npx|uvx)\b", b) and "mcp" in b.lower():
            return b.strip()[:2000]
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        if re.search(r"install|config|quickstart|usage|setup|getting started", h.get_text(), re.I):
            for sib in h.find_all_next(["pre", "code"]):
                t = unescape(sib.get_text()).strip()
                if t:
                    return t[:2000]
            break
    for b in blobs:
        if re.search(r"\b(pip install|npm i|npm install|docker (run|pull))\b", b):
            return b.strip()[:2000]
    return ""


def parse_detail(slug, html):
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else slug
    meta = soup.find("meta", attrs={"name": "description"})
    blurb = (meta.get("content", "").strip() if meta else "")[:500]
    if not blurb:
        p = soup.find("p")
        blurb = p.get_text(strip=True)[:500] if p else ""
    tags = ["mcp"]
    for a in soup.find_all("a", href=True):
        m = re.match(r"^/mcp-servers/categories/([a-z0-9-]+)$", a["href"])
        if m and m.group(1) not in tags:
            tags.append(m.group(1))
    return {
        "id": f"mcp/{slug}",
        "kind": "mcp",
        "name": name,
        "blurb": blurb,
        "url": urljoin(BASE, f"/mcp-servers/{slug}"),
        "install": pick_install(soup),
        "tags": tags,
        "past": False,
    }


async def main():
    args = sys.argv[1:]
    max_pages = int(args[args.index("--max-pages") + 1]) if "--max-pages" in args else None
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None

    proxy = proxy_url()
    sem = asyncio.Semaphore(CONCURRENCY)
    slugs = []
    async with httpx.AsyncClient(headers=UA, proxies=proxy) as client:
        first = await fetch(client, sem, LISTING)
        if first is None and proxy:
            async with httpx.AsyncClient(headers=UA) as direct:
                first = await fetch(direct, sem, LISTING)
        if not first:
            print("listing page 1 failed", file=sys.stderr)
            return 1
        n = total_pages(first)
        if max_pages:
            n = min(n, max_pages)
        slugs = listing_slugs(first)
        pages = await asyncio.gather(
            *[fetch(client, sem, f"{LISTING}?page={p}") for p in range(2, n + 1)]
        )
        for html in pages:
            if html:
                for s in listing_slugs(html):
                    if s not in slugs:
                        slugs.append(s)
        if limit:
            slugs = slugs[:limit]
        print(f"pages={n} slugs={len(slugs)}", file=sys.stderr)

        async def one(slug):
            html = await fetch(client, sem, urljoin(BASE, f"/mcp-servers/{slug}"))
            if html is None and proxy:
                async with httpx.AsyncClient(headers=UA) as direct:
                    html = await fetch(direct, sem, urljoin(BASE, f"/mcp-servers/{slug}"))
            if not html:
                return None
            try:
                return parse_detail(slug, html)
            except Exception:
                return None

        rows = [r for r in await asyncio.gather(*[one(s) for s in slugs]) if r]

    out = os.path.join(os.path.dirname(__file__), "../../data/seed/mcp-aiagentslist.json")
    out = os.path.normpath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    with_install = sum(1 for r in rows if r["install"])
    print(f"wrote {len(rows)} rows ({with_install} with install) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
