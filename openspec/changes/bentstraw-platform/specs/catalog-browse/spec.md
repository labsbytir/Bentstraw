# Spec Delta

## Purpose

Lets a visitor browse and open one record for each catalog kind: prompts, skills, repos, models, MCP servers, and icons.

## ADDED Requirements

### Requirement: Kind indexes

Each kind index SHALL list stored records for that kind only, with name, blurb, and kind label.

#### Scenario: MCP index excludes prompts

- **WHEN** a visitor opens `/mcp/`
- **THEN** every card is an MCP server and no prompt-only record appears.

### Requirement: Stable record identity

Each record SHALL have an id of `kind/source/slug`. Re-ingest of the same id SHALL update the record instead of inserting a duplicate.

#### Scenario: Re-ingest upserts

- **WHEN** the same MCP server id is ingested twice with a new blurb
- **THEN** the catalog contains one record and the detail page shows the new blurb.

### Requirement: Detail fields

A detail page SHALL show name, blurb, source URL, license when known, and kind-specific extras: install snippet for MCP, quiz tags for skills, and SVG/PNG/WebP links for icons when those files were stored.

#### Scenario: MCP install block

- **WHEN** a visitor opens an MCP detail page whose record has an install snippet
- **THEN** the page shows that snippet as copyable text and a link to the source.

### Requirement: Missing record

A detail URL with no stored record SHALL return 404 and SHALL NOT invent a card.

#### Scenario: Unknown id

- **WHEN** a visitor opens `/skills/does-not-exist/`
- **THEN** the response status is 404.
