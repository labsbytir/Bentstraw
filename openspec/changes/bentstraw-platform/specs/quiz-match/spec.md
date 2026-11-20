# Spec Delta

## Purpose

Matches a visitor to tools and skills with a short quiz whose answers query the same catalog the search box uses.

## ADDED Requirements

### Requirement: Three questions

The quiz SHALL ask exactly three questions and SHALL NOT require an account to see results.

#### Scenario: Finish the quiz

- **WHEN** a visitor answers all three questions
- **THEN** the page shows at least one matching card when the catalog has a related record.

### Requirement: Answers query the catalog

Each completed quiz SHALL search the catalog with the chosen terms and SHALL show name, blurb, and a link to the detail page.

#### Scenario: Agent-tool answer

- **WHEN** the visitor's answers include agent tooling terms present in a skill record
- **THEN** that skill appears in the results with a link to its detail page.

### Requirement: No match

If the catalog has no match, the quiz SHALL say so and SHALL offer the search page. It SHALL NOT invent a tool.

#### Scenario: Nonsense answers

- **WHEN** the answers match no record
- **THEN** the page states that nothing matched and links to `/search/`.
