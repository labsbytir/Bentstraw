"""Scrape aiagentslist.com/agents -> repos + upcoming-models bundles.

- data/seed/repos-agents.json (kind repos): every agent card found.
- data/seed/models-upcoming.json (kind models): cards matching
  model/LLM keywords (all found; source is agents, not models).

Self-contained fetch (httpx + asyncio, concurrency <= 8, timeout 30s,
2 retries). Decodo proxy ONLY from env (DECODO_USER/DECODO_PASS/
DECODO_ENDPOINT), fallback direct. Never commit creds.
past=true only when the agent detail page 404s (clearly dead).
"""
import asyncio
import json
import os
import re
import sys
from html import unescape
from pathlib import Path

import httpx

LISTING = "https://aiagentslist.com/agents"
SITE = "https://aiagentslist.com"
TIMEOUT = 30.0
RETRIES = 2
CONCURRENCY = 8
UA = {"User-Agent": "Mozilla/5.0 (compatible; bentstraw-bot/1.0; +https://bentstraw.com)"}

SEED = Path(__file__).resolve().parents[2] / "data" / "seed"
OUT_REPOS = SEED / "repos-agents.json"
OUT_MODELS = SEED / "models-upcoming.json"

CARD_RE = re.compile(
    r'href="(/agents/[\w-]+)".*?<h3[^>]*>(.*?)</h3>.*?<p[^>]*>(.*?)</p>',
    re.S,
)
EXT_RE = re.compile(r'href="(https?://(?!aiagentslist\.com)[^"]+)"')
MODEL_KW = ("model", "llm", "gpt", "claude", "inference", "foundation",
            "openrouter", "open-source ai", "run open-source", "jan ai", "void")

KEYWORD_TAGS = {
    "code": "code", "coding": "code", "developer": "code", "terminal": "code",
    "sales": "sales", "marketing": "marketing", "seo": "marketing",
    "video": "video", "image": "video", "animation": "video",
    "amazon": "ecommerce", "meeting": "productivity",
    "data": "data", "analytic": "data",
    "financ": "finance", "browser": "browser", "brows": "browser",
    "robot": "robotics", "crm": "crm", "crypto": "crypto",
    "blockchain": "crypto", "desktop": "desktop", "mobile": "mobile",
    "open source": "open-source", "self-hosted": "open-source",
    "free": "free",
}


def proxy_from_env():
    user = os.environ.get("DECODO_USER")
    pw = os.environ.get("DECODO_PASS")
    ep = os.environ.get("DECODO_ENDPOINT")
    if user and pw and ep:
        return f"http://{user}:{pw}@{ep}"
    return None


async def fetch(client, url, sem):
    last = None
    async with sem:
        for _ in range(RETRIES + 1):
            try:
                r = await client.get(url, timeout=TIMEOUT)
                if r.status_code == 200:
                    return (200, r.text)
                last = f"http {r.status_code}"
                if r.status_code == 404:
                    return (404, None)
            except Exception as e:  # noqa: BLE001 - retry then fall through
                last = str(e)
    print(f"warn: fetch failed {url}: {last}", file=sys.stderr)
    return (None, None)


def clean(s):
    return unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def tags_for(name, blurb):
    text = f"{name} {blurb}".lower()
    tags = {"agents", "repos"}
    for kw, tag in KEYWORD_TAGS.items():
        if kw in text:
            tags.add(tag)
    return sorted(tags)


def pick_url(detail_html, slug):
    if not detail_html:
        return f"{SITE}/agents/{slug}", False
    for u in EXT_RE.findall(detail_html):
        u = unescape(u).split("?ref=")[0].split("&amp;")[0]
        if "github.com/" in u and "/login" not in u:
            return u.split("?")[0], False
    for u in EXT_RE.findall(detail_html):
        u = unescape(u).split("?ref=")[0].split("&amp;")[0]
        if not any(x in u for x in ("s3.", "twitter.com", "linkedin.com",
                                    "compoundcontext", "aiagentslist")):
            return u.split("?")[0], False
    return f"{SITE}/agents/{slug}", False


async def main():
    proxy = proxy_from_env()
    print(f"proxy: {'decodo-env' if proxy else 'direct'}")
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(headers=UA, proxies={"all://": proxy} if proxy else None, follow_redirects=True) as client:
        status, listing = await fetch(client, LISTING, sem)
        if not listing:
            print("error: listing fetch failed", file=sys.stderr)
            sys.exit(1)
        cards = []
        seen = set()
        for slug_path, name, blurb in CARD_RE.findall(listing):
            slug = slug_path.split("/")[-1]
            name, blurb = clean(name), clean(blurb)
            if not name or slug in seen:
                continue
            seen.add(slug)
            cards.append((slug, name, blurb))
        print(f"cards found: {len(cards)}")

        details = await asyncio.gather(*[
            fetch(client, f"{SITE}/agents/{slug}", sem) for slug, _, _ in cards
        ])

    repos, models = [], []
    for (slug, name, blurb), (status, html) in zip(cards, details):
        dead = status == 404
        url, _ = pick_url(html, slug)
        base_tags = tags_for(name, blurb)
        repos.append({
            "id": f"repos/{slug}",
            "kind": "repos",
            "name": name,
            "blurb": blurb[:160],
            "url": url,
            "tags": base_tags,
            "past": dead,
        })
        detail_text = ""
        if html:
            m = re.search(r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]+)"', html)
            if m:
                detail_text = clean(m.group(1))
        text = f"{name} {blurb} {detail_text}".lower()
        if any(k in text for k in MODEL_KW):
            mt = sorted(set(base_tags) | {"models", "future"})
            models.append({
                "id": f"models/{slug}",
                "kind": "models",
                "name": name,
                "blurb": blurb[:160],
                "url": url,
                "tags": mt,
                "past": dead,
            })
    SEED.mkdir(parents=True, exist_ok=True)
    OUT_REPOS.write_text(json.dumps(repos, indent=2, ensure_ascii=False) + "\n")
    OUT_MODELS.write_text(json.dumps(models, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(repos)} rows -> {OUT_REPOS}")
    print(f"wrote {len(models)} rows -> {OUT_MODELS}")


if __name__ == "__main__":
    asyncio.run(main())
