# prompt-discovery

## Purpose

Let visitors browse and search curated prompts.

## ADDED Requirements

### Requirement: Prompt entries are searchable

Prompt entries SHALL have id, title, blurb, source URL, and tags, and SHALL appear in site search results by title, blurb, or tag.

#### Scenario: Find a marketing prompt

- **WHEN** a visitor searches "seo"
- **THEN** matching prompt entries from promptden/youmind/promptbase appear with title, blurb, and source link.

### Requirement: Source attribution

Each prompt entry SHALL link to its original source page and SHALL NOT copy full paywalled content — blurb only.

#### Scenario: Attribution present

- **WHEN** viewing a prompt card
- **THEN** a source link to the origin site is shown.
