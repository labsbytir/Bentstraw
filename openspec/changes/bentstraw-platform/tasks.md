# Tasks

## 1. Workspace and host

- [x] 1.1 Add `Reference Site Templates/` to `.gitignore` and verify `git status` does not list those HTML files as staged
- [x] 1.2 Add `Host bentstraw` to `~/.ssh/config` (HostName `151.241.100.47`, User root, IdentityFile `~/.ssh/prod_penny`, IdentitiesOnly yes) and verify `ssh bentstraw 'hostname'` prints `workflows.harvy.dev`
- [x] 1.3 Extend `~/.config/bentstraw/proxy.env` with `DECODO_PORTS=10001-10015` and verify the file mode stays `600` and the password is not in the repo (`git grep -n oj1Ahfo` returns nothing)

## 2. Astro server shell

- [x] 2.1 Switch `astro.config.mjs` to `output: 'server'` with `@astrojs/node` standalone and `@astrojs/react`, install deps, and verify `npm run build` exits 0
- [x] 2.2 Add `src/layouts/Base.astro` with the nav and tokens from design.md and verify `/` renders black background, Fira Code, and links to Quiz, Search, Stats, and each kind index
- [x] 2.3 Add shared kind index and detail routes for prompts, skills, repos, models, mcp, and icons, and verify an unknown id returns 404
- [x] 2.4 Add the owner-attribution line on icon and MCP detail and verify it is present in the rendered HTML

## 3. Bosbase on PGlite

- [x] 3.1 Add `deploy/pglite-server.mjs` that serves PGlite on `127.0.0.1:5432` from a data dir argument, and verify a local `psql` or node client can `SELECT 1`
- [x] 3.2 Extract the Bosbase binary with Podman on the Mac (not on the origin) into `deploy/bin/` gitignored, copy the run command into `deploy/systemd/bosbase.service`, and verify the unit file sets `SASSPB_POSTGRES_URL` to the localhost socket with `sslmode=disable`
- [x] 3.3 Add Bosbase collections `items` and file bucket `media`, plus LLM document collection `catalog`, via `scripts/bosbase-schema.ts`, and verify a second insert of the same id updates instead of duplicating
- [x] 3.4 Point seed ingest at Bosbase instead of the local-only table, and verify `npm run seed` reports a count greater than 0 against a running local Bosbase

## 4. Search, quiz, stats, llms.txt

- [x] 4.1 Rebuild Orama from Bosbase `items` and verify a search for a seeded name returns that id
- [x] 4.2 Keep the three-question quiz reading that index and verify a no-match path links to `/search/`
- [x] 4.3 Add `/stats/` with a Recharts island of kind counts, views, and ingest age, and verify a zero-row database returns 200 and total 0
- [x] 4.4 Add request-time `/llms.txt` and `/{kind}/{id}/llms.txt` and verify a stored detail companion is `text/plain` and includes the blurb, and a missing id returns 404 text/plain

## 5. Colly ingest

- [x] 5.1 Create `scraper/` Go module with Colly, round-robin ports 10001-10015, env credentials, and verify 15 sequential fetch-slot assignments use each port once (unit test, no live crawl)
- [x] 5.2 Add the global cap (start 32) and the MemAvailable / load backoff, and verify a unit test lowers the cap when available memory is below 1 GiB
- [x] 5.3 Implement source adapters for the seven named sources, blurb cap 600, image bytes stored to Bosbase `media`, and verify a fixture HTML page yields one record plus a stored file key or `image_status=failed`
- [x] 5.4 Add `deploy/scrape-monitor.sh` that prints load, MemAvailable, and in-flight count every 15 seconds, and verify a 45-second run prints at least two samples

## 6. Origin

- [~] 6.1 BLOCKED: PGlite socket server does not support extended query protocol (prepared statements). Bosbase (Go pgx) requires prepared statements. Even with default_query_exec_mode=simple_protocol, Bosbase hangs after creating _migrations table. Node, Caddy, and PGlite are installed on the origin. Bosbase binary runs but cannot initialize its schema through PGlite's wire protocol.
- [ ] 6.2 Issue a Cloudflare Origin CA cert for `bentstraw.com` and `www.bentstraw.com`, install it for Caddy, set the zone SSL mode to Full (strict), keep A records proxied to `151.241.100.47`, and verify `curl -fsS https://bentstraw.com/` returns the home page
- [ ] 6.3 Deploy the Astro server and seeded catalog, and verify `https://bentstraw.com/llms.txt` is text/plain and names Bentstraw
- [ ] 6.4 Run Colly at global cap 32 with the monitor attached, and verify the monitor never shows MemAvailable under 1 GiB without a following cap drop in the crawler log

## Workflow follow-up

- Archive `bentstraw-platform` after origin HTTPS and one successful ingest are verified.
- Leave `bentstraw-scrape-and-server` in place until this change's ingest replaces it, then archive that change too.
