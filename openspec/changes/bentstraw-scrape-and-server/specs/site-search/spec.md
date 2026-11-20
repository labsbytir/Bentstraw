# site-search

## Purpose

One search box over everything, updating as you type.

## ADDED Requirements

### Requirement: Instant client search

Typing in search SHALL filter the Orama index client-side with no page reload, showing up to 20 hits.

#### Scenario: Type to filter

- **WHEN** a visitor types "embeddings"
- **THEN** matching cards appear without navigation.

### Requirement: Secrets never ship

Search artifacts SHALL contain no proxy credentials or private keys.

#### Scenario: Artifact scan

- **WHEN** scanning `public/orama.json` and built pages
- **THEN** no `DECODO` credential strings are present.
