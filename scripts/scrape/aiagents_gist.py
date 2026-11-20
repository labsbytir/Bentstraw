"""Scrape the miku ai-agents gist -> data/seed/agent-skills-gist.json (kind skills).

Source: https://gist.github.com/miku/27a0afe81198e11269419978d3b4c8f7
Self-contained fetch (httpx + asyncio, concurrency <= 8, timeout 30s,
2 retries). Decodo proxy ONLY from env (DECODO_USER/DECODO_PASS/
DECODO_ENDPOINT), fallback direct. Never commit creds.
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import httpx

GIST_PAGE = "https://gist.github.com/miku/27a0afe81198e11269419978d3b4c8f7"
RAW_URLS = [
    "https://gist.githubusercontent.com/miku/27a0afe81198e11269419978d3b4c8f7/raw/ai-agents.md",
    GIST_PAGE,
]
TIMEOUT = 30.0
RETRIES = 2
CONCURRENCY = 8
UA = {"User-Agent": "Mozilla/5.0 (compatible; bentstraw-bot/1.0; +https://bentstraw.com)"}

OUT = Path(__file__).resolve().parents[2] / "data" / "seed" / "agent-skills-gist.json"

KEYWORD_TAGS = {
    "browser": "browser", "brows": "browser", "web": "browser",
    "code": "code", "coding": "code", "developer": "code",
    "sales": "sales", "marketing": "marketing", "seo": "marketing",
    "multi-agent": "multi-agent", "collaborat": "multi-agent",
    "no-code": "no-code", "drag-and-drop": "no-code",
    "research": "research", "writ": "research",
    "financ": "finance", "stock": "finance",
    "robot": "robotics", "meeting": "productivity",
    "data": "data", "analytic": "data", "crm": "crm",
    "video": "video", "image": "video", "blockchain": "crypto",
    "desktop": "desktop", "automation": "automation",
    "open-source": "open-source", "open source": "open-source",
    "enterprise": "enterprise",
}


def proxy_from_env():
    user = os.environ.get("DECODO_USER")
    pw = os.environ.get("DECODO_PASS")
    ep = os.environ.get("DECODO_ENDPOINT")
    if user and pw and ep:
        return f"http://{user}:{pw}@{ep}"
    return None


async def fetch(client, url):
    last = None
    for _ in range(RETRIES + 1):
        try:
            r = await client.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.text
            last = f"http {r.status_code}"
        except Exception as e:  # noqa: BLE001 - retry then fall through
            last = str(e)
    print(f"warn: fetch failed {url}: {last}", file=sys.stderr)
    return None


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "agent"


def tags_for(name, desc, category):
    text = f"{name} {desc} {category}".lower()
    tags = {"agents", "skill"}
    for kw, tag in KEYWORD_TAGS.items():
        if kw in text:
            tags.add(tag)
    return sorted(tags)


def parse_table(md):
    rows = []
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "name":
            continue
        m = re.match(r"\[(.+?)\]\((https?://[^)]+)\)", cells[0])
        if not m:
            continue
        name, url = m.group(1).strip(), m.group(2).strip()
        desc = re.sub(r"\s+", " ", cells[1]).strip()
        category = re.sub(r"\s+", " ", cells[2]).strip()
        if not name or not desc:
            continue
        rows.append((name, url, desc, category))
    return rows


async def main():
    proxy = proxy_from_env()
    print(f"proxy: {'decodo-env' if proxy else 'direct'}")
    async with httpx.AsyncClient(headers=UA, proxies={"all://": proxy} if proxy else None, follow_redirects=True) as client:
        md = None
        for url in RAW_URLS:
            md = await fetch(client, url)
            if md and "| Name" in md:
                break
            md = None
        if md is None:
            print("error: could not fetch gist markdown", file=sys.stderr)
            sys.exit(1)
    rows = parse_table(md)
    seen = set()
    out = []
    for name, url, desc, category in rows:
        slug = slugify(name)
        if slug in seen:
            continue
        seen.add(slug)
        blurb = desc[:160]  # excerpt only, no copying beyond source snippet
        out.append({
            "id": f"skills/{slug}",
            "kind": "skills",
            "name": f"{name} skill",
            "blurb": blurb,
            "url": url,
            "tags": tags_for(name, desc, category),
            "past": False,
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} rows -> {OUT}")
    browser = [r for r in out if "browser" in r["tags"]]
    print(f"browser-tagged rows: {len(browser)}")


if __name__ == "__main__":
    asyncio.run(main())
