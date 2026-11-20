# Design

## Context

Working tree is now `/Users/pen/Desktop/Bentstraw` on `sandbox`, synced from `~/dev/bentstraw`. What exists: Astro 5 static (`output: 'static'`), three pages, PGlite file at `data/bentstraw/`, Orama rebuild, seed bundles under `data/seed/`, Python scrapers, a Caddyfile aimed at Let's Encrypt. Origin `151.241.100.47` is Debian 13 (trixie), 5 cores, 7.7 GiB RAM, 188 GiB free, hostname `workflows.harvy.dev`, sshd only. SSH with `~/.ssh/prod_penny` as root works after a known_hosts refresh. Reference HTML lives in `Reference Site Templates/` and stays untracked.

Bosbase's published installer is Docker Compose plus `pgvector/pgvector:pg16`. That path is forbidden. Bosbase itself only needs `SASSPB_POSTGRES_URL`. PGlite plus a wire socket satisfies that without a Postgres server.

## Goals / Non-Goals

**Goals:**

- One site tree, one origin, Bosbase as system of record, Orama as the public search index.
- Origin TLS that Cloudflare Full (strict) accepts while the DNS record stays proxied.
- Colly ingest that downloads images and backs off when the box is hot.

**Non-Goals:**

- Selling icons, copying ThemeForest kits, or storing full source articles.
- Docker, Podman, or a Postgres server on the origin.
- A social graph beyond signup, login, votes, and view counts. Follows and comments wait.
- Replacing Orama with Bosbase vector search. Both exist. Orama is what the search box hits.

## Decisions

### 1. Astro server, not static

`llms.txt` must be generated on page load from current Bosbase content. Static export cannot do that.

Locked guides (the other session's retrieved transcript did not contain a separate Astro URL list; these are the guides that match server islands, React charts, and request-time text):

- https://docs.astro.build/en/guides/server-islands/
- https://docs.astro.build/en/guides/integrations-guide/react/
- https://docs.astro.build/en/guides/integrations-guide/node/
- https://docs.astro.build/en/guides/middleware/
- https://docs.astro.build/en/guides/endpoints/
- https://docs.astro.build/en/guides/routing/

`astro.config.mjs` sets `output: 'server'` and `@astrojs/node` in standalone mode. Search-as-you-type stays a client island over `public/orama.json`. Stats is a React island (`recharts`) with `server:defer` only if the chart data is already in the HTML; the first version renders the chart from props passed by the page, no deferred fetch required.

Alternative rejected: keep static and write `llms.txt` at build time. Fails the "on page load" requirement the moment a scrape lands.

### 2. Site tree

```
src/layouts/Base.astro          # nav, tokens, footer, attribution slot
src/pages/index.astro
src/pages/search.astro
src/pages/quiz.astro
src/pages/stats.astro
src/pages/login.astro
src/pages/llms.txt.ts           # GET /llms.txt
src/pages/prompts/index.astro
src/pages/prompts/[id].astro
src/pages/prompts/[id]/llms.txt.ts
src/pages/skills/...            # same pair
src/pages/repos/...
src/pages/models/...
src/pages/mcp/...
src/pages/icons/...
src/components/Card.astro
src/components/Grid.astro
src/components/StatsCharts.tsx  # recharts
src/lib/bosbase.ts
src/lib/llms.ts
scraper/                        # Go module, Colly only
deploy/Caddyfile
deploy/systemd/*.service
Reference Site Templates/       # local reference, gitignored
```

Kind routes share one data loader. Do not copy six page implementations.

### 3. Reference adherence

Skin stays the tokens already in `src/styles.css`. Structure is borrowed, markup is ours.

Dashboard Icons browse (`Browse Icons & Logos`): search field, then a grid of cells. Each cell is a mark plus a name. Detail (`Posthog Icon & Logo - SVG, PNG, WebP`) adds variant links (SVG, PNG, WebP) and a light/dark note. Target markup:

```html
<nav class="top">
  <a class="brand" href="/">Bentstraw</a>
  <a href="/prompts/">Prompts</a>
  <a href="/skills/">Skills</a>
  <a href="/repos/">Repos</a>
  <a href="/models/">Models</a>
  <a href="/mcp/">MCP</a>
  <a href="/icons/">Icons</a>
  <a href="/quiz/">Quiz</a>
  <a href="/search/">Search</a>
  <a href="/stats/">Stats</a>
</nav>
<input id="q" placeholder="search" />
<div class="grid">
  <a class="card" href="/icons/dashboard-icons/posthog/">
    <img alt="" src="/files/icons/posthog.svg" />
    <h3>Posthog</h3>
  </a>
</div>
```

Glama registry (`Open-Source MCP Servers`) is a card grid: name, official badge, one-line blurb. Lucy Memory detail adds install snippet plus Overview. Target:

```html
<article class="card">
  <h1>Lucy Memory</h1>
  <p class="meta">mcp · source</p>
  <p>short blurb, not the full readme</p>
  <pre class="install">npx ...</pre>
  <p class="meta">icons and names belong to their owners — listed to refer, not to sell</p>
</article>
```

skills.sh (`Next.js skills`, `find-skills`): mono uppercase labels, name, one-line description, install-ish meta. Same `.card` plus a `.meta` line. Do not import their CSS variables.

Brutal ThemeForest kit: confirms heavy rules and big type. Do not copy Elementor markup, buy-now buttons, or the kit's palette. Black and Fira already win.

Breton digital print: product grid with image hover. Use it only as a reminder that icon cells are image-first. Do not copy WooCommerce classes.

### 4. Bosbase on PGlite

On the origin, under `/opt/bentstraw`:

- `pglite.service` — Bun or Node runs `@electric-sql/pglite` file-backed at `/opt/bentstraw/pglite` with the `vector` extension if the build provides it, and `@electric-sql/pglite-socket` on `127.0.0.1:5432`.
- `bosbase.service` — binary extracted once on the Mac with Podman (`podman create` + `podman cp` from `docker.io/bosbase/bosbase:latest`), copied to the origin, never installed via Docker there. Env:

```
SASSPB_POSTGRES_URL=postgres://postgres@127.0.0.1:5432/pbosbase?sslmode=disable
BS_ENCRYPTION_KEY=<openssl rand -hex 16, file mode 600, not in git>
WASM_ENABLE=true
```

Admin UI stays on `127.0.0.1:8090`. Caddy proxies `/api/`, `/_/`, and `/files/` to it. Public pages are the Astro node server on `127.0.0.1:4321`.

Collections:

- `items` — id `kind/source/slug`, name, blurb, tags, source_url, license, install, views, ingested_at.
- Bosbase file bucket `media` — image bytes, key `icons/<id>/<variant>`.
- LLM documents collection `catalog`, id equal to `items.id`, content `name + blurb`, metadata kind, source_url, license.

Orama rebuild reads `items` and writes `public/orama.json`, then the Astro server reads that file. Votes require `pb.collection('users').authWithPassword` session. Anonymous detail views increment `views` through a Bosbase hook or a single update from the page loader.

Memory cache: Bosbase's built-in cache for repeat `items` reads. Do not add Redis.

Alternative rejected: keep the laptop PGlite as the only database and rsync it. Breaks auth, storage, and realtime, and fights the "Bosbase for all features" order.

### 5. Orama and charts

Search schema stays `{ id, kind, name, blurb, tags }`. Vector mode waits until a 384-dim local embedding is actually produced. Do not call OpenAI from the search box.

`/stats/` loads counts with one grouped query and passes `{ kind, count, views, ageHours }[]` into `StatsCharts.tsx`. Recharts: monochrome, white and gray on black, no gradient. Guide: https://recharts.github.io/

### 6. llms.txt

`src/lib/llms.ts` builds the body. Route handlers call it on each request. Detail body is name, kind, blurb, source URL, license. No HTML. Cache-Control: `no-cache` so a fresh scrape shows up on the next load.

### 7. Colly

Go module `scraper/` using `github.com/gocolly/colly/v2`. Explicit Go exception: the user ordered Colly. The rest of the site stays TypeScript.

Proxy: `http://USER:PASS@isp.decodo.com:PORT`. Ports `10001`–`10015`. Round-robin index increments per URL, including retries. Credentials from `DECODO_USER` and `DECODO_PASS` (already in `~/.config/bentstraw/proxy.env`). Never log the password.

Limits: per-port semaphore 1000 (the proxy's cap). Global cap starts at 32 on this 5-core box and drops by half when `/proc/meminfo` MemAvailable < 1 GiB or load average > 4. A supervisor loop on the origin prints load, MemAvailable, and in-flight count every 15 seconds during a crawl. Images: Colly downloads the bytes, POSTs them to Bosbase storage, stores the file key on the item. Failed image means the item is marked `image_status=failed`, not hotlinked.

Sources, in order: promptden, youmind, promptbase free text, ai-agents gist, aiagentslist agents, aiagentslist MCP, Glama sitemaps. Blurb cap 600 characters. Keep the source URL.

The existing Python adapters may be read for selectors. They are not the runner.

### 8. Origin TLS

Cloudflare Origin CA certificate for `bentstraw.com` and `www.bentstraw.com`, 15-year, installed at `/etc/ssl/bentstraw/`. Caddy uses `tls /etc/ssl/bentstraw/origin.pem /etc/ssl/bentstraw/origin.key`. Zone SSL mode Full (strict). A records for `@` and `www` stay proxied (orange cloud) to `151.241.100.47`.

Why not Let's Encrypt HTTP-01: the orange cloud answers the challenge, so the origin never sees it. DNS-01 would work but Origin CA is the certificate Cloudflare documents for proxied origins and does not depend on a public CA renewal loop.

Caddy routes:

- `/api/*`, `/_/`, `/files/*` → `127.0.0.1:8090`
- everything else → `127.0.0.1:4321`

Firewall: 22, 80, 443 only.

### 9. SSH host entry

Local `~/.ssh/config` gains:

```
Host bentstraw
  HostName 151.241.100.47
  User root
  IdentityFile ~/.ssh/prod_penny
  IdentitiesOnly yes
```

This replaces the stale `vps-remote` address for this box. Do not delete other hosts.

## Risks / Trade-offs

- [PGlite wire socket rejects a Bosbase migration] → first boot is the test; pin the Bosbase binary that booted, do not auto-pull.
- [Bosbase activation check phones home to `ve.bosbase.com`] → if the binary refuses to start without it, record the error and stop. Do not bypass a license check.
- [15 × 1000 connections would kill a 7.7 GiB box] → 1000 is the proxy cap, not the target. Global cap starts at 32.
- [Origin CA is not publicly trusted] → correct behind Cloudflare. Direct-to-IP HTTPS will warn. That is expected.
- [Glama HTML is JS-heavy] → sitemap plus detail HTML first; if a field is empty, store the URL and mark the field missing. Do not launch a browser farm.
- [ThemeForest HTML is commercial] → reference only, gitignored, never copied into `src/`.

## Migration Plan

1. Commit this change on `sandbox` and push.
2. Add the SSH host entry. Confirm `ssh bentstraw` lands on Debian 13.
3. Install Bun or Node, Caddy, and the Bosbase binary. Start PGlite, then Bosbase, then Astro.
4. Issue Origin CA, set Full (strict), point proxied A records at `151.241.100.47`.
5. Seed existing JSON bundles into Bosbase, rebuild Orama, then start Colly with the global cap at 32.
6. Rollback: stop the three systemd units and revert the A record. Data dirs `/opt/bentstraw/pglite` and Bosbase `pb_data` stay on disk.

## Open Questions

- None that change the specs. Embedding dimension stays unset until a local 384-dim model is actually running. Quiz question copy can be rewritten without a spec change as long as there are three questions and results come from the catalog.
