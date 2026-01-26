# Capability: Smart Search

Detect search result precision and suggest alternatives when results may be low quality.

## ADDED Requirements

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

The system MUST warn users when search results may be imprecise.

#### Scenario: Suggest CQL for low confidence
- **Given** search results with confidence < 0.6
- **When** results are returned to the user
- **Then** a suggestion is included
- **And** the suggestion mentions CQL as an alternative
- **And** a CQL preview query is provided

#### Scenario: No warning for high confidence
- **Given** search results with confidence >= 0.6
- **When** results are returned to the user
- **Then** no suggestion is included
- **And** results are returned directly

### Requirement: CQL Preview Generation

The system MUST generate a CQL query preview for the user.

#### Scenario: Generate title and text search CQL
- **Given** a search query `"API documentation"`
- **When** CQL preview is generated
- **Then** the preview is `title ~ "API documentation" OR text ~ "API documentation"`

#### Scenario: Escape special characters in CQL
- **Given** a search query with special characters
- **When** CQL preview is generated
- **Then** special characters are properly escaped
