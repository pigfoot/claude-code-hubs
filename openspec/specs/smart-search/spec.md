# smart-search Specification

## Purpose

TBD - created by archiving change 005-confluence-smart-routing. Update Purpose after archive.

## Requirements

### Requirement: Confidence Scoring

The system MUST calculate a confidence score for search results.

#### Scenario: High confidence with title matches

- **Given** a search query `"WRS documentation"`
- **And** 3 or more results have the query in the title
- **When** confidence is calculated
- **Then** the score is >= 0.9

#### Scenario: Medium confidence with some matches

- **Given** a search query
- **And** 1-2 results have the query in the title
- **When** confidence is calculated
- **Then** the score is between 0.7 and 0.9

#### Scenario: Low confidence with many results

- **Given** a search query
- **And** more than 50 results are returned
- **And** few titles contain the query
- **When** confidence is calculated
- **Then** the score is <= 0.4

#### Scenario: Zero confidence with no results

- **Given** a search query
- **And** no results are returned
- **When** confidence is calculated
- **Then** the score is 0.0

### Requirement: Precision Warning

The system MUST suggest Rovo AI search when CQL search results are imprecise,
and users should be offered the opportunity to authenticate and retry with
semantic search.

#### Scenario: Suggest Rovo for low confidence CQL results

- **WHEN** CQL search results have confidence < 0.6
- **THEN** a suggestion is included in the output
- **AND** the suggestion asks whether the user wants to try Rovo AI search
- **AND** the suggestion notes that Rovo requires Atlassian authentication

#### Scenario: No suggestion for high confidence CQL results

- **WHEN** CQL search results have confidence >= 0.6
- **THEN** no suggestion is included
- **AND** results are returned directly
