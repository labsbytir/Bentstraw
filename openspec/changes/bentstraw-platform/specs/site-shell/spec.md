# Spec Delta

## Purpose

Gives every Bentstraw page one brutalist shell and a stable route tree so browse, search, quiz, and stats do not drift from the reference layouts.

## ADDED Requirements

### Requirement: Brutalist shell tokens

Every public page SHALL use a black background, foreground `#e8e8e8`, muted `#9a9a9a`, 1px borders, Fira Code, and a top nav. No second type family and no light theme.

#### Scenario: Home renders the shell

- **WHEN** a visitor opens `/`
- **THEN** the page background is black, the typeface is Fira Code, and the nav includes Bentstraw, Quiz, Search, and Stats.

### Requirement: Route tree

The site SHALL expose `/`, `/search/`, `/quiz/`, `/stats/`, `/login/`, and index plus detail routes for prompts, skills, repos, models, mcp, and icons.

#### Scenario: Detail route exists

- **WHEN** a visitor opens `/mcp/<id>/` for a stored MCP server
- **THEN** the response is that server's detail page, not the home page.

### Requirement: Reference structure, not copied templates

Browse pages SHALL use a search field plus a card grid. Detail pages SHALL use a title, a short blurb, source attribution, and a variant or install block. The site SHALL NOT ship ThemeForest, Glama, or Dashboard Icons HTML as page source.

#### Scenario: Grid browse

- **WHEN** a visitor opens `/prompts/`
- **THEN** the page shows a search field and a grid of cards, each with a name and a one-line blurb.

### Requirement: Attribution banner

Icon and logo pages SHALL show that marks belong to their owners and are listed for reference, not sold or endorsed.

#### Scenario: Icon detail banner

- **WHEN** a visitor opens an icon detail page
- **THEN** the page states the mark belongs to its owner and is shown only to refer to that product.
