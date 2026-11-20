# Spec Delta

## Purpose

Gives visitors one search box over the whole catalog, backed by an Orama index rebuilt from the system of record.

## ADDED Requirements

### Requirement: Typed search

Typing in the search box SHALL return matching cards without a full page reload, up to 20 hits, from the current Orama index.

#### Scenario: Type to filter

- **WHEN** a visitor types a name that exists in the index
- **THEN** matching cards appear without navigation.

### Requirement: Empty query

An empty search box SHALL show no hit list and SHALL NOT error.

#### Scenario: Clear the box

- **WHEN** a visitor deletes the query
- **THEN** the hit list is empty.

### Requirement: Index matches catalog

The Orama index SHALL include every public catalog record's id, kind, name, blurb, and tags. A rebuild SHALL replace the previous index atomically.

#### Scenario: New row is searchable

- **WHEN** a record is added and the index is rebuilt
- **THEN** a search for that record's name returns it.

### Requirement: No secrets in the index

Search artifacts SHALL contain no proxy credentials, origin private keys, or encryption keys.

#### Scenario: Index scan

- **WHEN** the published search index is scanned for `DECODO` and `BEGIN PRIVATE KEY`
- **THEN** neither string is present.
