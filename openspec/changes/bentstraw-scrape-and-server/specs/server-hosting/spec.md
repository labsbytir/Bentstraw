# server-hosting

## Purpose

Serve bentstraw.com behind Cloudflare with valid SSL.

## ADDED Requirements

### Requirement: Cloudflare-compatible origin SSL

The origin SHALL present a certificate valid for Cloudflare Full Strict (Let's Encrypt via Caddy or Cloudflare Origin CA), auto-renewed, and SHALL redirect HTTP to HTTPS.

#### Scenario: Strict TLS

- **WHEN** Cloudflare proxies bentstraw.com in Full Strict mode
- **THEN** origin handshake succeeds and pages load with no cert error.

### Requirement: No containers or external DB

The origin SHALL run Astro static + PGlite file-backed on disk with systemd/Caddy only — no Docker, no Postgres.

#### Scenario: Reboot

- **WHEN** the host reboots
- **THEN** the site service restarts automatically and serves the last built `dist/`.
