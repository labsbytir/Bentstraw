# mcp-discovery

## Purpose

Let visitors browse MCP servers from aiagentslist and Glama.

## ADDED Requirements

### Requirement: MCP entries are searchable

MCP entries SHALL have id `mcp/<slug>`, name, blurb, source URL, install snippet when available, and tags, and SHALL appear in search.

#### Scenario: Find an MCP server

- **WHEN** a visitor searches "filesystem"
- **THEN** matching MCP entries appear with install snippet when the source provides one.

### Requirement: Glama scale

Glama import SHALL be paginated and resumable so a run can stop and continue without re-scraping completed pages.

#### Scenario: Resume

- **WHEN** a Glama run is interrupted
- **THEN** re-running skips pages already saved to disk.
