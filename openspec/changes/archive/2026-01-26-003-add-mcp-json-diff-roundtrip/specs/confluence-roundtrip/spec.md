## ADDED Requirements

### Requirement: Roundtrip Page Editing

The system SHALL support reading a Confluence page, allowing Claude to edit the content, and writing the changes back
while preserving macros.

#### Scenario: Edit text on page with macros

- **WHEN** user requests editing a Confluence page that contains macros
- **AND** the edit instruction targets non-macro text content
- **THEN** the system SHALL read the page via MCP in ADF format
- **AND** convert ADF to Markdown for Claude editing
- **AND** apply only text changes back to the original ADF
- **AND** write the patched ADF back via MCP
- **AND** all macros SHALL be preserved unchanged

#### Scenario: Edit text on page without macros

- **WHEN** user requests editing a Confluence page with no macros
- **THEN** the system SHALL complete the edit using the same ADF diff/patch workflow
- **AND** all formatting (headings, lists, code blocks, tables) SHALL be preserved

#### Scenario: No changes detected

- **WHEN** Claude's edit results in no text changes
- **THEN** the system SHALL skip the write operation
- **AND** inform the user that no changes were detected

---

### Requirement: Text Extraction from ADF

The system SHALL extract text nodes with their JSON paths from Atlassian Document Format (ADF).

#### Scenario: Extract text from headings and paragraphs

- **WHEN** ADF contains headings and paragraphs
- **THEN** the system SHALL extract all text nodes
- **AND** each extracted text SHALL include its path for later patching

#### Scenario: Skip macro nodes during extraction

- **WHEN** ADF contains macro nodes (inlineExtension, extension, bodiedExtension)
- **THEN** the system SHALL NOT extract text from inside those nodes
- **AND** the macro nodes SHALL remain untouched

---

### Requirement: ADF to Markdown Conversion

The system SHALL convert ADF to Markdown suitable for Claude editing, with macros represented as placeholders.

#### Scenario: Convert basic formatting

- **WHEN** ADF contains headings, paragraphs, lists, code blocks, and blockquotes
- **THEN** the system SHALL convert them to equivalent Markdown syntax

#### Scenario: Represent macros as placeholders

- **WHEN** ADF contains macro nodes
- **THEN** the system SHALL insert HTML comment placeholders (e.g., `<!-- MACRO: expand -->`)
- **AND** the placeholders SHALL be for visual reference only (not used in patching)

---

### Requirement: Text Change Detection

The system SHALL detect which text nodes were modified by comparing original ADF text with edited Markdown.

#### Scenario: Detect modified text

- **WHEN** a text node's content differs between original ADF and edited Markdown
- **THEN** the system SHALL record the change with path, old text, and new text

#### Scenario: Use fuzzy matching for text identification

- **WHEN** comparing original and edited text
- **THEN** the system SHALL use word overlap heuristic (minimum 30% overlap) to identify matching text
- **AND** handle cases where text is slightly reformatted

---

### Requirement: ADF Patching

The system SHALL apply text changes to the original ADF without modifying macro nodes.

#### Scenario: Apply text changes

- **WHEN** text changes are identified
- **THEN** the system SHALL navigate to each text node by path
- **AND** update only the text content
- **AND** preserve all other node properties and structure

#### Scenario: Preserve macros during patching

- **WHEN** patching ADF with text changes
- **THEN** macro nodes SHALL NOT be modified
- **AND** the patched ADF SHALL be valid for Confluence API

---

### Requirement: MCP Integration

The system SHALL use MCP Atlassian tools for reading and writing Confluence pages.

#### Scenario: Read page via MCP

- **WHEN** reading a Confluence page
- **THEN** the system SHALL use `getConfluencePage` with `contentFormat: "adf"`
- **AND** parse the ADF JSON from the response

#### Scenario: Write page via MCP

- **WHEN** writing changes back
- **THEN** the system SHALL use `updateConfluencePage` with the patched ADF body
- **AND** the system SHALL NOT require managing API tokens (MCP handles OAuth)

---

### Requirement: Optional Macro Body Editing

The system SHALL support optional editing of text inside macro bodies with user confirmation.

#### Scenario: Detect editable macro body content

- **WHEN** ADF contains macros with text content inside them (e.g., expand panels, info boxes)
- **THEN** the system SHALL detect these macro bodies
- **AND** report count and types to the user
- **AND** show preview of the content (first 50 characters per macro)

#### Scenario: User confirms macro body editing

- **WHEN** user confirms editing macro body content
- **THEN** the system SHALL extract text from inside macro nodes
- **AND** include them in the Markdown shown to Claude
- **AND** apply text changes back to macro body nodes via JSON patching
- **AND** preserve all macro structure and properties

#### Scenario: User declines macro body editing

- **WHEN** user declines editing macro body content
- **THEN** the system SHALL skip macro bodies entirely
- **AND** only edit content outside macros
- **AND** proceed with safe mode editing

#### Scenario: No macro bodies detected

- **WHEN** page has no macros with editable body content
- **THEN** the system SHALL proceed without asking
- **AND** edit normally

---

### Requirement: Backup and Rollback

The system SHALL provide backup and rollback capability for all edit operations.

#### Scenario: Create backup before editing

- **WHEN** starting any page edit operation
- **THEN** the system SHALL create a backup containing:
  - Original ADF JSON content
  - Page version number
  - Page metadata (ID, title, spaceId)
  - Timestamp
- **AND** store backup in `.confluence_backups/{page_id}/{timestamp}.json`
- **AND** inform user that backup was created

#### Scenario: Auto-rollback on write failure

- **WHEN** writing patched ADF to Confluence fails
- **THEN** the system SHALL automatically load the backup
- **AND** verify the page was not partially updated
- **AND** inform user that rollback was performed
- **AND** show the error that caused the failure

#### Scenario: Manual rollback request

- **WHEN** user requests manual rollback for a page
- **THEN** the system SHALL list available backups with timestamps
- **AND** allow user to select which backup to restore
- **AND** restore the selected backup via MCP
- **AND** confirm successful restoration

#### Scenario: Backup retention

- **WHEN** page has more than 10 backups (default limit)
- **THEN** the system SHALL delete oldest backups
- **AND** keep only the most recent 10
- **AND** respect `CONFLUENCE_BACKUP_LIMIT` environment variable if set

---

### Requirement: Safe Defaults

The system SHALL use safe defaults that minimize risk while allowing advanced users to opt-in to more powerful features.

#### Scenario: Default mode is safe

- **WHEN** user runs an edit without specifying options
- **THEN** the system SHALL default to safe mode:
  - Skip macro body content
  - Create backup automatically
  - Require explicit confirmation for destructive operations

#### Scenario: Advanced mode opt-in

- **WHEN** user explicitly opts into advanced features
- **THEN** the system SHALL enable requested features
- **AND** show clear warnings about increased risk
- **AND** ensure backup is created
