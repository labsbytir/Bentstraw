# Proposal

## Why

Bentstraw is a search-first social discovery platform for forgotten past and tomorrow's tech, and the live origin is still empty. The catalog, quiz, and static pages exist only on a laptop checkout. bentstraw.com is proxied by Cloudflare and must be served from `151.241.100.47` with origin TLS that Full (strict) accepts, with Bosbase as the system of record and no Docker.

## What Changes

- Move the working tree to `/Users/pen/Desktop/Bentstraw` and replace the three-page static shell with a real site tree: home, search, quiz, stats, auth, and per-kind browse plus detail for prompts, skills, repos, models, MCP servers, and icons.
- Run Bosbase as a binary (not a container) on the origin, backed by file-backed PGlite speaking the Postgres wire protocol. Bosbase owns auth, file storage, realtime, vector, data APIs, memory cache, and LLM documents.
- Keep Orama as the public site search index, hydrated from Bosbase. Do not replace Orama with pgvector-only search.
- Add a Recharts island for catalog stats (counts by kind, views, scrape freshness).
- Generate a per-page `llms.txt` on each page load from that page's content. This requires Astro server output, not a pure static build.
- Replace the Python scrapers with a Go Colly crawler. Each URL gets a fresh Decodo proxy call, round-robin across 15 proxy ports. Download images into Bosbase storage. Monitor origin load and back off. Proxy credentials stay in `~/.config/bentstraw/proxy.env`, never in git.
- Issue a Cloudflare Origin CA certificate for `bentstraw.com` and `www.bentstraw.com`, install it on Caddy, set the zone SSL mode to Full (strict). Do not use HTTP-01 Let's Encrypt behind the orange cloud.
- Skin stays the existing brutalist tokens (`#000` / `#e8e8e8` / Fira Code). Reference HTML files constrain information architecture only. Do not vendor ThemeForest or third-party page source into the repo.

## Capabilities

### New Capabilities

- `site-shell`: brutalist layout, nav, and page tree that follow the reference HTML structure without copying commercial templates.
- `catalog-browse`: browse and detail pages for prompts, skills, repos, models, MCP servers, and icons, including downloaded image variants.
- `site-search`: Orama full-text search over the Bosbase catalog, with a later vector mode once embeddings exist.
- `quiz-match`: three-question match that returns tools and skills from the same index.
- `content-stats`: Recharts charts of catalog counts, views, and scrape freshness.
- `page-llms`: request-time `llms.txt` for the page that was just loaded.
- `bosbase-platform`: PGlite-backed Bosbase for auth, storage, realtime, vector, data APIs, memory cache, and LLM documents.
- `colly-ingest`: Colly crawl with per-URL proxy round-robin, image download, and origin load monitoring.
- `origin-hosting`: Debian origin at `151.241.100.47`, Caddy, Cloudflare Origin CA, Full (strict), no Docker.

### Modified Capabilities

- None. Main specs are empty. The in-flight change `bentstraw-scrape-and-server` is superseded by this change for hosting, search, and ingest behavior.

## Impact

- Code: `src/pages`, `src/layouts`, `src/components`, `scraper/` (Go), `deploy/`, `scripts/seed.ts`, `astro.config.mjs`.
- Systems: origin `151.241.100.47` (Debian 13, 5 cores, 7.7 GiB RAM, hostname `workflows.harvy.dev`), Cloudflare zone `bentstraw.com`, Decodo ISP proxy ports `10001`–`10015`.
- Dependencies: Astro server + `@astrojs/node` + `@astrojs/react`, `recharts`, `bosbase`, `@electric-sql/pglite`, `@electric-sql/pglite-socket`, `@orama/orama`, Colly. Go is allowed only for the scraper, because it was explicitly requested.
- Secrets: proxy user/password and `BS_ENCRYPTION_KEY` are env-only. The proxy password already pasted in chat must not be committed.
