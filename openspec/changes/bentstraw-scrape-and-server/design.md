# Design

## Architecture

Universal Python scraper (`scripts/scrape/universal.py`) owns HTTP (httpx + asyncio, concurrency 16, per-host 1 rps, robots.txt respect, Decodo proxy from env) and writes raw JSON per source to `data/raw/<source>/`. One small adapter per source normalizes to `data/seed/<bundle>.json` rows `{id,kind,name,blurb,url,tags,past}`. Existing `scripts/seed.ts` loads rows into PGlite; `scripts/build-index.ts` rebuilds Orama. Server: Caddy (auto LE cert, valid for Cloudflare Full Strict) reverse-proxies local Astro `dist/` via `caddy file-server`, PGlite stays an on-disk build input (no socket needed until dynamic counters land).

## Interfaces

- `fetch_many(urls) -> list[html]` — universal.py; concurrency 16, timeout 30s, retries 2, proxy from `DECODO_USER`/`DECODO_PASS` env only.
- `normalize_<source>(raw) -> rows` — one function per adapter; row keys exactly `id,kind,name,blurb,url,tags,past`.
- Glama adapter takes `--page-range a-b` and `--resume` (skips saved pages).

## Decisions

- Python, not Colly (Go needs explicit approval per repo language rule).
- Blurb-only excerpts + source links (no paywall copying).
- Glama split into 3 page-range bundles so 3 subagents work without merge conflicts.
- Proxy creds never touch disk/repo; `.gitignore` covers `data/raw/`, `.env`.
