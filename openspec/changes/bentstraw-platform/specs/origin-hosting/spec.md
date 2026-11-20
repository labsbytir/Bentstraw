# Spec Delta

## Purpose

Serves bentstraw.com from the Debian origin behind Cloudflare with a certificate Cloudflare Full (strict) accepts.

## ADDED Requirements

### Requirement: Origin address

Production SHALL be the host `151.241.100.47`, SSH user `root`, key `prod_penny`. The site hostname SHALL be `bentstraw.com`.

#### Scenario: SSH identity

- **WHEN** an operator connects with `prod_penny` to `151.241.100.47`
- **THEN** the login is root on that host.

### Requirement: Cloudflare-compatible origin TLS

The origin SHALL present a certificate Cloudflare trusts for `bentstraw.com` and `www.bentstraw.com`. The zone SSL mode SHALL be Full (strict). HTTP-01 Let's Encrypt behind the proxied (orange-cloud) record SHALL NOT be the certificate source.

#### Scenario: Proxied HTTPS

- **WHEN** a client requests `https://bentstraw.com/` through Cloudflare
- **THEN** the response is the Bentstraw home page and the zone SSL mode is Full (strict).

### Requirement: Edge only on 80 and 443

The public firewall SHALL allow 22, 80, and 443. Bosbase `8090` and PGlite `5432` SHALL listen on localhost only.

#### Scenario: Port scan from outside

- **WHEN** a remote host connects to `151.241.100.47:8090`
- **THEN** the connection is refused or filtered.

### Requirement: Restart survival

Bosbase, PGlite, and Caddy SHALL be systemd units that start on boot and restart on failure.

#### Scenario: Reboot

- **WHEN** the origin reboots
- **THEN** `https://bentstraw.com/` answers without a manual start.
