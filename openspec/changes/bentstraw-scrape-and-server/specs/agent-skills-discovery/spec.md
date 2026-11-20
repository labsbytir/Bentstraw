# agent-skills-discovery

## Purpose

Let visitors find agent skills, repos, and upcoming AI models.

## ADDED Requirements

### Requirement: Skill/repo/model entries are searchable

Entries SHALL have id, kind (`skills`|`repos`|`models`), name, blurb, source URL, and tags, and SHALL appear in search and on the home grid.

#### Scenario: Find a browser skill

- **WHEN** a visitor searches "browser"
- **THEN** the agent-browser skill entry appears.

### Requirement: Past/future labeling

Each entry SHALL be labeled past (forgotten) or future (upcoming) and the quiz SHALL be able to filter on it.

#### Scenario: Quiz filters past

- **WHEN** quiz picks "forgotten past"
- **THEN** only past-labeled entries rank top.
