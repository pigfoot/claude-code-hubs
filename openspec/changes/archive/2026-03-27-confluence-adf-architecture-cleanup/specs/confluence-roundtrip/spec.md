## MODIFIED Requirements

### Requirement: Roundtrip Page Editing

The system SHALL support reading a Confluence page, allowing Claude to edit the content, and writing the changes back
while preserving macros. The roundtrip operates directly on ADF JSON via JSON diff/patch (Method 6).
Markdown is used only as a **display format** for Claude to read page content, NOT as a conversion intermediate.

#### Scenario: Edit text on page with macros

- **WHEN** user requests editing a Confluence page that contains macros
- **AND** the edit instruction targets non-macro text content
- **THEN** the system SHALL read the page via MCP or REST API v2 in ADF format
- **AND** extract text nodes from ADF for Claude to view as readable Markdown
- **AND** apply only text changes back to the original ADF via JSON diff/patch
- **AND** write the patched ADF back via MCP or REST API v2
- **AND** all macros SHALL be preserved unchanged
- **AND** the roundtrip SHALL NOT convert ADF to Markdown and back as a data transformation step

#### Scenario: Edit text on page without macros

- **WHEN** user requests editing a Confluence page with no macros
- **THEN** the system SHALL complete the edit using the same ADF diff/patch workflow
- **AND** all formatting (headings, lists, code blocks, tables) SHALL be preserved

#### Scenario: No changes detected

- **WHEN** Claude's edit results in no text changes
- **THEN** the system SHALL skip the write operation
- **AND** inform the user that no changes were detected

### Requirement: ADF to Markdown Conversion

The system SHALL convert ADF to Markdown suitable for Claude to **view and understand** page content.
This conversion is a **display utility**, not a roundtrip data transformation.
The Markdown output is shown to Claude for comprehension; text changes are applied back to ADF
via JSON diff/patch, not by converting Markdown back to ADF.

#### Scenario: Convert basic formatting

- **WHEN** ADF contains headings, paragraphs, lists, code blocks, and blockquotes
- **THEN** the system SHALL convert them to equivalent Markdown syntax for display

#### Scenario: Represent Confluence-specific elements as readable markers

- **WHEN** ADF contains expand, emoji, mention, inlineCard, panel, status, or date nodes
- **THEN** the system SHALL insert HTML comment markers that indicate element type and attributes
- **AND** content inside block markers (expand, panel) SHALL be recursively converted to Markdown
- **AND** these markers serve as **visual indicators** for Claude, not as data to be parsed back

### Requirement: Download pages via v2 API in ADF format

The system SHALL download Confluence pages using the v2 REST API and convert ADF to Markdown with custom markers.

#### Scenario: Download page with Confluence-specific elements

- **WHEN** user runs `download_confluence.py PAGE_ID`
- **THEN** the system SHALL fetch the page via v2 API (`/wiki/api/v2/pages/{id}?body-format=atlas_doc_format`)
- **AND** SHALL convert ADF JSON to Markdown using the `adf_to_markdown` module
- **AND** the resulting Markdown SHALL contain custom markers for expand, emoji, mention,
  inlineCard, panel, status, and date nodes
- **AND** SHALL write the Markdown file with YAML frontmatter (id, space, version, url, format: adf)

#### Scenario: Download page with attachments

- **WHEN** the page contains media/image references
- **THEN** the system SHALL download attachment files to `{page_id}_attachments/` directory
- **AND** the Markdown SHALL reference attachments with relative paths

### Requirement: Upload Markdown as new page via ADF v2 API

The system SHALL upload Markdown files to Confluence by converting to ADF JSON
and using the v2 REST API. This is for **new page creation** from Markdown source files.

#### Scenario: Upload markdown with markers to existing page

- **WHEN** user runs `upload_confluence.py document.md --id PAGE_ID`
- **THEN** the system SHALL convert Markdown to ADF JSON using the `markdown_to_adf` module
- **AND** SHALL upload via v2 API (`PUT /wiki/api/v2/pages/{id}` with `representation: atlas_doc_format`)
- **AND** all Confluence-specific elements SHALL be restored from markers

#### Scenario: Upload markdown without markers to existing page

- **WHEN** user runs `upload_confluence.py document.md --id PAGE_ID`
- **AND** the markdown contains no custom markers
- **THEN** the system SHALL convert Markdown to ADF JSON using the `markdown_to_adf` module
- **AND** SHALL upload via v2 API with ADF representation
- **AND** the system SHALL NOT fall back to Storage Format v1 API

#### Scenario: Create new page from markdown

- **WHEN** user runs `upload_confluence.py document.md --space SPACE_KEY --parent-id PARENT_ID`
- **THEN** the system SHALL convert to ADF JSON and create the page via v2 API

## REMOVED Requirements

### Requirement: Upload Markdown to ADF via v2 API

**Reason**: The original requirement included fallback to Storage Format v1 API for marker-free markdown and a `--legacy` flag. These paths are removed. All uploads now use ADF v2 exclusively.

**Migration**: Remove `--legacy` flag from `upload_confluence.py`. Remove `ConfluenceStorageRenderer` and v1 Storage Format upload logic. All markdown uploads go through `markdown_to_adf.py` → v2 API.
