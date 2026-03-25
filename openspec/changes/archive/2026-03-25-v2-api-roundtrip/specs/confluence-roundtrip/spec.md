## ADDED Requirements

### Requirement: Download pages via v2 API in ADF format

The system SHALL download Confluence pages using the v2 REST API and convert ADF to Markdown with custom markers.

#### Scenario: Download page with Confluence-specific elements

- **WHEN** user runs `download_confluence.py PAGE_ID`
- **THEN** the system SHALL fetch the page via v2 API (`/wiki/api/v2/pages/{id}?body-format=atlas_doc_format`)
- **AND** SHALL convert ADF JSON to Markdown using the `adf_to_markdown` module
- **AND** the resulting Markdown SHALL contain custom markers for expand, emoji, mention, inlineCard, panel, status, and date nodes
- **AND** SHALL write the Markdown file with YAML frontmatter (id, space, version, url)

#### Scenario: Download page with attachments

- **WHEN** the page contains media/image references
- **THEN** the system SHALL download attachment files to `{page_id}_attachments/` directory
- **AND** the Markdown SHALL reference attachments with relative paths

### Requirement: Upload Markdown to ADF via v2 API

The system SHALL upload Markdown files (with custom markers) to Confluence by converting to ADF JSON and using the v2 REST API.

#### Scenario: Upload markdown with markers to existing page

- **WHEN** user runs `upload_confluence.py document.md --id PAGE_ID`
- **AND** the markdown contains custom markers (`<!-- EXPAND: -->`, `:emoji:`, etc.)
- **THEN** the system SHALL convert Markdown to ADF JSON using the `markdown_to_adf` module
- **AND** SHALL upload via v2 API (`PUT /wiki/api/v2/pages/{id}` with `body-format=atlas_doc_format`)
- **AND** all Confluence-specific elements SHALL be restored from markers

#### Scenario: Upload marker-free markdown (backward compatibility)

- **WHEN** user runs `upload_confluence.py document.md --id PAGE_ID`
- **AND** the markdown contains no custom markers
- **THEN** the system SHALL fall back to the current Storage format renderer
- **AND** SHALL upload via v1 API with Storage representation
- **AND** existing behavior SHALL be preserved

#### Scenario: Create new page with markers

- **WHEN** user runs `upload_confluence.py document.md --space SPACE_KEY --parent-id PARENT_ID`
- **AND** the markdown contains custom markers
- **THEN** the system SHALL convert to ADF JSON and create the page via v2 API

#### Scenario: Legacy flag for old behavior

- **WHEN** user runs `upload_confluence.py document.md --id PAGE_ID --legacy`
- **THEN** the system SHALL use the v1 API Storage format path regardless of marker presence

## MODIFIED Requirements

### Requirement: ADF to Markdown Conversion

The system SHALL convert ADF to Markdown suitable for Claude editing, with Confluence-specific elements represented as round-trippable markers instead of lossy placeholders.

#### Scenario: Convert basic formatting

- **WHEN** ADF contains headings, paragraphs, lists, code blocks, and blockquotes
- **THEN** the system SHALL convert them to equivalent Markdown syntax

#### Scenario: Represent Confluence-specific elements as round-trippable markers

- **WHEN** ADF contains expand, emoji, mention, inlineCard, panel, status, or date nodes
- **THEN** the system SHALL insert HTML comment markers that preserve element type and attributes
- **AND** the markers SHALL be parseable back into ADF nodes during upload
- **AND** content inside block markers (expand, panel) SHALL be recursively converted to Markdown
