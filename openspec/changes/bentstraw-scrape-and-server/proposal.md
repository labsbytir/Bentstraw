# Proposal

## Why

Bentstraw is a social discovery platform for forgotten past + tomorrow's tech. The catalog is empty (8 seed rows); it needs real prompts, agent skills, repos, AI models, and MCP servers, plus its production home on bentstraw.com behind Cloudflare.

## What Changes

- Add universal Python scraper (`scripts/scrape/universal.py`, httpx + asyncio + BeautifulSoup) with robots respect, per-host rate limit, env-based Decodo proxy, concurrency cap 16 (proxy allows 1000; server + target politeness is the binding constraint).
- Add per-source adapters + seed ingest for: promptden, youmind, promptbase marketplace (free/text subset), ai-agents gist, aiagentslist agents, aiagentslist mcp-servers, glama.ai mcp servers (paginated, biggest bundle — split by page ranges).
- Ingest results into PGlite `items` + rebuild Orama `public/orama.json`; quiz + search read the same index.
- Stand up production on bentstraw.com: Cloudflare proxy → origin with SSL valid for Full Strict (Caddy + Let's Encrypt or Cloudflare Origin CA), Astro static served from origin, PGlite file-backed on disk, no Docker, no Postgres.
- **Colly note:** Colly is Go; repo allows TypeScript/Python only, so Python scraper is used unless user explicitly approves Go.

## Capabilities

### New Capabilities

- `prompt-discovery`: browse/search curated prompts from prompt sources.
- `agent-skills-discovery`: browse/search agent skills, repos, upcoming AI models.
- `mcp-discovery`: browse/search MCP servers from aiagentslist + Glama.
- `quiz-match`: quiz answers map to matching tools/skills via Orama search.
- `site-search`: full-text (+ later vector) search over all items via Orama.
- `server-hosting`: bentstraw.com behind Cloudflare proxy with valid origin SSL.

### Modified Capabilities

- None (greenfield change on empty catalog).

## Impact

- New: `scripts/scrape/*`, `data/seed/*.json`, PGlite rows, `public/orama.json`, Astro pages (already exist, content grows).
- Systems: Decodo ISP proxy (env creds, never committed); bentstraw.com DNS/Cloudflare; origin host (Caddy/systemd).
