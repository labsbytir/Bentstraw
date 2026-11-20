# Spec Delta

## Purpose

Shows catalog health as charts so an operator can see what the scrape added and what visitors open.

## ADDED Requirements

### Requirement: Kind counts

The stats page SHALL chart the number of records per kind: prompt, skill, repo, model, mcp, icon.

#### Scenario: Chart matches counts

- **WHEN** an operator opens `/stats/`
- **THEN** each kind's bar equals the stored count for that kind.

### Requirement: Views and freshness

The stats page SHALL chart view totals and the age of the newest ingest per kind.

#### Scenario: Fresh ingest

- **WHEN** a kind was ingested in the last hour
- **THEN** that kind's freshness mark shows under one hour.

### Requirement: Empty catalog

With zero records the stats page SHALL render empty charts and a zero total, not an error page.

#### Scenario: Fresh database

- **WHEN** no records exist
- **THEN** `/stats/` returns 200 and shows a total of 0.
