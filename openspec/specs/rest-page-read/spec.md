# rest-page-read Specification

## Purpose

TBD

## Requirements

### Requirement: Read page as Markdown

The system SHALL read a Confluence page by ID and output its content as human-readable Markdown via stdout.

#### Scenario: Read by page ID

- **WHEN** `read_page.py PAGE_ID` is invoked
- **THEN** the script outputs a header block (title, ID, space, version) followed by the page body in Markdown

#### Scenario: Read by Confluence URL

- **WHEN** `read_page.py` is invoked with a full Confluence URL or short `/wiki/x/` URL
- **THEN** the URL is resolved to a page ID via `url_resolver` and the page is read

#### Scenario: Missing credentials

- **WHEN** any of `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` is unset
- **THEN** the script exits with a non-zero code and prints which variables are missing

### Requirement: Read page as ADF JSON

The system SHALL read a Confluence page and output its raw ADF content as JSON for programmatic use (e.g., Method 6 editing).

#### Scenario: ADF output mode

- **WHEN** `read_page.py PAGE_ID --format adf` is invoked
- **THEN** the script outputs a JSON object containing `page_id`, `title`, `version`, `space_id`, and `adf` fields

#### Scenario: ADF is valid JSON

- **WHEN** `--format adf` output is parsed
- **THEN** the `adf` field contains a valid Atlassian Document Format object
