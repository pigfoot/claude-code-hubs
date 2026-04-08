# rest-cql-search Specification

## Purpose

TBD

## Requirements

### Requirement: Execute CQL search via REST API

The system SHALL execute a Confluence Query Language (CQL) search using the REST API v1 and return formatted results.

#### Scenario: Basic CQL query

- **WHEN** `search_cql.py 'title ~ "API docs"'` is invoked
- **THEN** the script returns a formatted list of matching pages with titles, IDs, spaces, and URLs

#### Scenario: CQL with limit

- **WHEN** `search_cql.py 'space = "DEV"' --limit 20` is invoked
- **THEN** at most 20 results are returned

#### Scenario: No results

- **WHEN** a valid CQL query matches no pages
- **THEN** the script outputs "No results found" and exits with code 0

#### Scenario: Invalid CQL syntax

- **WHEN** a syntactically invalid CQL query is submitted
- **THEN** the script outputs the API error message and exits with a non-zero code

### Requirement: JSON output mode

The system SHALL support JSON output for programmatic consumption by other tools.

#### Scenario: JSON format flag

- **WHEN** `search_cql.py 'CQL' --format json` is invoked
- **THEN** the script outputs a JSON array of result objects with structured fields

### Requirement: Confidence analysis integration

The system SHALL analyze CQL search result quality using `smart_search.SmartSearch`
and surface precision warnings when confidence is low.

#### Scenario: Low confidence result

- **WHEN** CQL results have confidence < 0.6
- **THEN** the output includes a suggestion to try Rovo AI search for better semantic results

#### Scenario: High confidence result

- **WHEN** CQL results have confidence >= 0.6
- **THEN** no suggestion is shown and results are returned directly
