# Spec Delta

## Purpose

Makes Bosbase the system of record for accounts, files, records, realtime, vectors, and LLM documents, with PGlite as its only database.

## ADDED Requirements

### Requirement: No Docker and no Postgres server

The origin SHALL run Bosbase and PGlite as processes. It SHALL NOT run Docker, Podman, or a standalone Postgres server.

#### Scenario: Process check

- **WHEN** an operator lists listening services on the origin
- **THEN** Bosbase listens on `127.0.0.1:8090` and PGlite's wire socket listens on `127.0.0.1:5432`, and no container runtime is active.

### Requirement: Auth

A visitor SHALL be able to sign up, log in, and log out. Catalog reads SHALL work without an account. Writes of votes and follows SHALL require a session.

#### Scenario: Anonymous read

- **WHEN** a visitor with no session opens a detail page
- **THEN** the page renders. A vote write without a session is rejected.

### Requirement: File storage

Downloaded images and icon variants SHALL be stored in Bosbase file storage and served from the site, not only hotlinked.

#### Scenario: Stored icon

- **WHEN** an icon ingest saved an SVG
- **THEN** the detail page's SVG link returns that file from Bentstraw's origin.

### Requirement: LLM documents

Each public catalog record SHALL also exist as an LLM document whose id equals the catalog id, whose content is name plus blurb, and whose metadata includes kind, source URL, and license.

#### Scenario: Semantic lookup

- **WHEN** an operator queries LLM documents for a phrase in a stored blurb
- **THEN** that record is among the results.

### Requirement: Realtime view counter

A successful detail view SHALL increment that record's view count. The stats page SHALL read the same count.

#### Scenario: Open a detail page

- **WHEN** a visitor opens a detail page once
- **THEN** that record's stored view count increases by one.
