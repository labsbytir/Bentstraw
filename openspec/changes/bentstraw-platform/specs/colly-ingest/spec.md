# Spec Delta

## Purpose

Fills the catalog by crawling the named sources with Colly, one fresh proxy call per URL, and stores text plus images without melting the origin.

## ADDED Requirements

### Requirement: Colly is the crawler

Ingest SHALL use Colly. A Python fetcher SHALL NOT be the production crawler.

#### Scenario: Binary identity

- **WHEN** an operator runs the ingest command with `-h`
- **THEN** the help text names Colly and the Go module path.

### Requirement: Proxy round-robin

Each fetched URL SHALL use the next Decodo port in `10001` through `10015`, then wrap. Two consecutive URL fetches SHALL NOT be required to share a port. Credentials SHALL be read from the environment, never from the repo.

#### Scenario: Fifteen fetches

- **WHEN** the crawler fetches 15 URLs in order
- **THEN** each port from 10001 to 10015 is used once.

### Requirement: Concurrency ceiling and backoff

Each proxy port SHALL allow at most 1000 in-flight requests. The crawler SHALL also keep a global cap and SHALL lower it when origin CPU stays above 80 percent or available memory drops below 1 GiB.

#### Scenario: Origin pressure

- **WHEN** origin available memory is below 1 GiB during a crawl
- **THEN** the crawler reduces in-flight requests before starting the next batch.

### Requirement: Image download

The crawler SHALL download image bytes referenced by a record and store them with that record. A hotlink-only icon SHALL NOT count as ingested.

#### Scenario: Icon image

- **WHEN** a source page has an icon image URL
- **THEN** the stored record has a file whose bytes match the download, or the record is marked failed rather than silently hotlinked.

### Requirement: Source list

The crawler SHALL cover promptden prompts, youmind prompts, promptbase free text prompts, the ai-agents gist, aiagentslist agents, aiagentslist MCP servers, and Glama MCP servers.

#### Scenario: Glama row

- **WHEN** a Glama server page is crawled successfully
- **THEN** the catalog gains or updates one MCP record with name, blurb, source URL, and install snippet when the page has one.

### Requirement: Directory posture

Stored text SHALL be a short blurb plus source link, not a full copy of the source page. Each card SHALL keep attribution.

#### Scenario: Long source page

- **WHEN** a source page is longer than the blurb limit
- **THEN** the stored content is the blurb and the URL, not the full article body.
