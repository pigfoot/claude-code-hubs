# url-resolution Specification

## Purpose

TBD - created by archiving change 005-confluence-smart-routing. Update Purpose after archive.

## Requirements

### Requirement: Short URL Decoding

The system MUST decode Confluence TinyUI short URLs to page IDs.

#### Scenario: Decode valid short URL

- **Given** a Confluence short URL `https://site.atlassian.net/wiki/x/ZQGBfg`
- **When** the URL resolver processes the URL
- **Then** the page ID `2122383717` is extracted
- **And** the result type is `page_id`

#### Scenario: Handle URL-safe Base64 characters

- **Given** a short URL code containing `-` or `_` characters
- **When** the URL resolver decodes the code
- **Then** characters are converted to standard Base64 (`+` and `/`)
- **And** decoding succeeds

### Requirement: Full URL Parsing

The system MUST extract page IDs from full Confluence URLs.

#### Scenario: Parse full page URL

- **Given** a URL `https://site.atlassian.net/wiki/spaces/SPACE/pages/123456789/Title`
- **When** the URL resolver processes the URL
- **Then** the page ID `123456789` is extracted
- **And** the result type is `page_id`

#### Scenario: Parse URL with query parameters

- **Given** a URL with query parameters after the page ID
- **When** the URL resolver processes the URL
- **Then** only the page ID is extracted
- **And** query parameters are ignored

### Requirement: Direct Page ID Input

The system MUST accept direct page IDs as input.

#### Scenario: Accept numeric page ID

- **Given** input `123456789` (numeric string)
- **When** the URL resolver processes the input
- **Then** the value is returned as-is
- **And** the result type is `page_id`

#### Scenario: Accept page ID as integer

- **Given** input `123456789` (integer)
- **When** the URL resolver processes the input
- **Then** the value is converted to string
- **And** the result type is `page_id`

### Requirement: Unknown Format Handling

The system MUST handle unrecognized URL formats gracefully.

#### Scenario: Unrecognized URL format

- **Given** a URL that doesn't match known patterns
- **When** the URL resolver processes the URL
- **Then** the result type is `unknown`
- **And** the original value is preserved
- **And** no error is raised
