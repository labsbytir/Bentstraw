# Spec Delta

## Purpose

Publishes a plain-text llms.txt for the page a visitor just loaded, so an agent can read that page without scraping HTML.

## ADDED Requirements

### Requirement: Companion llms.txt

Each public HTML page SHALL also be available as `llms.txt` under the same path, generated on that request from the page's current content. A build-time-only file SHALL NOT satisfy this.

#### Scenario: Detail companion

- **WHEN** a client requests `/mcp/<id>/llms.txt` for a stored server
- **THEN** the response is `text/plain` and includes that server's name, blurb, and source URL.

### Requirement: Home companion

`/llms.txt` SHALL list the site name, a one-line description, and links to the kind indexes.

#### Scenario: Site root text

- **WHEN** a client requests `/llms.txt`
- **THEN** the body names Bentstraw and links `/prompts/`, `/skills/`, `/repos/`, `/models/`, `/mcp/`, and `/icons/`.

### Requirement: Missing page

A companion for a missing record SHALL return 404 plain text, not HTML.

#### Scenario: Unknown companion

- **WHEN** a client requests `/skills/does-not-exist/llms.txt`
- **THEN** the status is 404 and the content type is `text/plain`.
