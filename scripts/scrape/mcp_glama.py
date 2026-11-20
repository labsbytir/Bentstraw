"""Scrape Glama MCP registry -> data/seed/mcp-glama.json.

Full-listing mechanism: Glama's /mcp/servers HTML only renders ~150 links with
no ?page= pagination and no __NEXT_DATA__, but /sitemap.xml indexes 13
mcp-servers sub-sitemaps (10k URLs each, ~130k total) of the form
/mcp/servers/<owner>/<repo>. We enumerate slugs from those, then fetch a
bounded sample of detail pages.

Rows: {id:"mcp/<slug>", kind:"mcp", name, blurb, url, install, tags, past:false}
Dedupes against data/seed/mcp-aiagentslist.json ids (Glama rows lose on clash).

Usage:
  python3 scripts/scrape/mcp_glama.py [--page-range 1-13] [--limit 450]
                                      [--out data/seed/mcp-glama.json] [--resume]

HTTP via universal.fetch_many (timeout 30s, retries 2, proxy ONLY from env
DECODO_USER/DECODO_PASS/DECODO_ENDPOINT, fallback to direct). Batches of <=8
to cap concurrency. --resume skips slugs already present in --out.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from universal import fetch_many  # noqa: E402

BASE = "https://glama.ai"
SITEMAP_INDEX = BASE + "/sitemap.xml"
BATCH = 8  # concurrency cap

SERVER_RE = re.compile(r"https://glama\.ai/mcp/servers/([^/\s\"'<>]+)/([^/\s\"'<>]+)")
LOC_RE = re.compile(r"<loc>(.*?)</loc>")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(
    r'<meta\s+(?:content="([^"]*)"\s+name="description"|name="description"\s+content="([^"]*)")',
    re.S,
)
RAWCODE_RE = re.compile(r'<pre><code class="raw-code">(.*?)</code></pre>', re.S)


def batched(xs: list[str]) -> list[list[str]]:
    return [xs[i : i + BATCH] for i in range(0, len(xs), BATCH)]


def fetch_capped(urls: list[str]) -> list[str]:
    """fetch_many in batches of <=8, with direct fallback for proxy failures."""
    out: list[str] = []
    for chunk in batched(urls):
        pages = fetch_many(chunk)
        if any(not p for p in pages) and os.getenv("DECODO_USER"):
            # proxy may be down: retry failures direct (env stripped for this call)
            saved = {k: os.environ.pop(k, None) for k in ("DECODO_USER", "DECODO_PASS", "DECODO_ENDPOINT")}
            try:
                retry = fetch_many([u for u, p in zip(chunk, pages) if not p])
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
            it = iter(retry)
            pages = [p if p else next(it) for p in pages]
        out.extend(pages)
    return out


def slugify(owner: str, repo: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", f"{owner}-{repo}".lower()).strip("-")


def parse_detail(url: str, html: str) -> dict | None:
    if not html:
        return None
    m = SERVER_RE.search(url)
    if not m:
        return None
    slug = slugify(m.group(1), m.group(2))
    t = TITLE_RE.search(html)
    name = unescape(t.group(1).strip()).split(" by ")[0].split(" | ")[0][:200] if t else slug
    d = DESC_RE.search(html)
    blurb = unescape((d.group(1) or d.group(2) or "").strip())[:500] if d else ""
    install = ""
    for code in RAWCODE_RE.findall(html):
        text = unescape(re.sub(r"<[^>]+>", "", code)).strip()
        if '"mcpServers"' in text:
            install = text[:2000]
            break
        if not install and re.search(r"\b(npx|uvx|pip install|npm (i|install)|docker (run|pull))\b", text):
            install = text[:2000]
    return {
        "id": f"mcp/{slug}",
        "kind": "mcp",
        "name": name or slug,
        "blurb": blurb,
        "url": url,
        "install": install,
        "tags": ["mcp"],
        "past": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Glama MCP scraper (sitemap-driven, resumable).")
    ap.add_argument("--page-range", default="1-13", help="Sitemap file numbers, e.g. 1-5 (tasks 4/5/6 shards)")
    ap.add_argument("--limit", type=int, default=450, help="Max NEW detail pages to fetch (0=no cap)")
    ap.add_argument("--out", default="data/seed/mcp-glama.json")
    ap.add_argument("--resume", action="store_true", help="Skip slugs already present in --out")
    args = ap.parse_args()

    a, b = (int(x) for x in args.page_range.split("-"))
    out = Path(args.out)

    done: dict[str, dict] = {}
    if args.resume and out.exists():
        for r in json.loads(out.read_text()):
            done[r["id"]] = r
        print(f"resume: {len(done)} rows already saved")

    existing_ids = set()
    ai_path = Path("data/seed/mcp-aiagentslist.json")
    if ai_path.exists():
        existing_ids = {r["id"].lower() for r in json.loads(ai_path.read_text())}
        print(f"dedupe: {len(existing_ids)} aiagentslist ids loaded")

    sm_urls = [f"{BASE}/sitemaps/mcp-servers/{i}.xml" for i in range(a, b + 1)]
    print(f"fetching {len(sm_urls)} sitemap files...", flush=True)
    slugs: list[tuple[str, str]] = []  # (slug, url), round-robined across files
    seen: set[str] = set()
    per_file: list[list[tuple[str, str]]] = []
    for xml in fetch_capped(sm_urls):
        cur: list[tuple[str, str]] = []
        for loc in LOC_RE.findall(xml or ""):
            m = SERVER_RE.match(loc.strip())
            if not m:
                continue
            slug = slugify(m.group(1), m.group(2))
            rid = f"mcp/{slug}"
            if rid in seen or rid in done or rid.lower() in existing_ids:
                continue
            seen.add(rid)
            cur.append((slug, loc.strip()))
        per_file.append(cur)
    # round-robin so a capped run samples every sitemap file (all thirds)
    i = 0
    while any(i < len(c) for c in per_file):
        for c in per_file:
            if i < len(c):
                slugs.append(c[i])
        i += 1
    print(f"candidate new slugs: {len(slugs)} (range {a}-{b})", flush=True)

    if args.limit:
        slugs = slugs[: args.limit]
    urls = [u for _, u in slugs]
    print(f"fetching {len(urls)} detail pages...", flush=True)
    rows: list[dict] = list(done.values())
    n_ok = n_install = 0
    for i, chunk in enumerate(batched(urls)):
        for url, html in zip(chunk, fetch_capped(chunk)):
            r = parse_detail(url, html)
            if r:
                rows.append(r)
                n_ok += 1
                n_install += bool(r["install"])
        print(f"  batch {i + 1}/{(len(urls) + BATCH - 1) // BATCH}: rows={n_ok}", flush=True)

    # final dedupe on id (first wins), keep resume rows
    uniq: dict[str, dict] = {}
    for r in rows:
        uniq.setdefault(r["id"], r)
    rows = list(uniq.values())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"wrote {len(rows)} rows ({n_install} new with install) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
