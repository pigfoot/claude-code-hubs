## MODIFIED Requirements

### Requirement: Markdown to ADF conversion

The system SHALL convert Markdown (with custom markers) to ADF JSON suitable for the Confluence v2 API.
This conversion is used for **new page uploads only**, not for roundtrip editing of existing pages.

#### Scenario: Convert standard markdown to ADF nodes

- **WHEN** markdown contains headings, paragraphs, lists, code blocks, blockquotes, horizontal rules, and tables
- **THEN** the system SHALL produce valid ADF JSON with correct node types and attributes
- **AND** generate unique `localId` attributes for nodes that require them

#### Scenario: Convert inline formatting to ADF marks

- **WHEN** markdown contains `**bold**`, `*italic*`, `` `code` ``, `[link](url)`, `~~strike~~`, `<u>underline</u>`
- **THEN** the system SHALL produce ADF text nodes with corresponding marks

#### Scenario: Parse expand markers into ADF expand nodes

- **WHEN** markdown contains `<!-- EXPAND: "title" -->` ... `<!-- /EXPAND -->` blocks
- **THEN** the system SHALL produce `{"type": "expand", "attrs": {"title": "...", "localId": "..."}}` ADF nodes
- **AND** recursively parse the content between markers as ADF children
- **AND** restore breakout marks if present in the marker attributes

#### Scenario: Parse emoji shortnames into ADF emoji nodes

- **WHEN** markdown contains `:shortName:` patterns (e.g., `:ms_teams:`)
- **THEN** the system SHALL produce `{"type": "emoji", "attrs": {"shortName": ":shortName:"}}` ADF nodes

#### Scenario: Parse mention markers into ADF mention nodes

- **WHEN** markdown contains `<!-- MENTION: id "text" -->` markers
- **THEN** the system SHALL produce `{"type": "mention", "attrs": {"id": "...", "text": "..."}}` ADF nodes

#### Scenario: Parse inline card markers into ADF inlineCard nodes

- **WHEN** markdown contains `<!-- CARD: url -->` markers
- **THEN** the system SHALL produce `{"type": "inlineCard", "attrs": {"url": "..."}}` ADF nodes

#### Scenario: Parse panel markers into ADF panel nodes

- **WHEN** markdown contains `<!-- PANEL: type -->` ... `<!-- /PANEL -->` blocks
- **THEN** the system SHALL produce `{"type": "panel", "attrs": {"panelType": "..."}}` ADF nodes
- **AND** recursively parse the content between markers as ADF children

#### Scenario: Parse status markers into ADF status nodes

- **WHEN** markdown contains `<!-- STATUS: "text" color -->` markers
- **THEN** the system SHALL produce `{"type": "status", "attrs": {"text": "...", "color": "...", "style": "bold"}}` ADF nodes

#### Scenario: Parse multiple inline markers on one line

- **WHEN** markdown contains multiple inline markers on a single line (e.g., `<!-- STATUS: "A" green --> <!-- STATUS: "B" red -->`)
- **THEN** the system SHALL parse each marker individually
- **AND** produce separate ADF nodes for each marker
- **AND** SHALL NOT merge multiple markers into a single node

#### Scenario: Parse date markers into ADF date nodes

- **WHEN** markdown contains `<!-- DATE: timestamp -->` markers
- **THEN** the system SHALL produce `{"type": "date", "attrs": {"timestamp": "..."}}` ADF nodes

#### Scenario: Restore unknown node type markers

- **WHEN** markdown contains `<!-- ADF:type {...attrs} -->` pass-through markers
- **THEN** the system SHALL reconstruct the original ADF node from the preserved JSON

#### Scenario: Handle marker-free markdown

- **WHEN** markdown contains no custom markers (manually written markdown for new page upload)
- **THEN** the system SHALL produce valid ADF JSON from standard markdown elements only
- **AND** not fail or warn about missing markers

### Requirement: Roundtrip fidelity

The system SHALL maintain fidelity when converting ADF → Markdown → ADF for supported element types.
This roundtrip is relevant for **display purposes** (showing ADF content as readable Markdown) and for
**new page uploads** (Markdown → ADF). The primary roundtrip editing workflow (Method 6) operates
directly on ADF JSON and does not use this conversion path.

#### Scenario: Standard elements roundtrip

- **WHEN** an ADF document containing headings, paragraphs, lists, code blocks, tables,
  and blockquotes is converted to Markdown and back
- **THEN** the resulting ADF SHALL be structurally equivalent to the original
- **AND** text content SHALL be identical

#### Scenario: Confluence-specific elements roundtrip

- **WHEN** an ADF document containing expand, emoji, mention, inlineCard, panel, status,
  and date nodes is converted to Markdown and back
- **THEN** the resulting ADF SHALL contain all original Confluence-specific nodes
- **AND** node attributes (title, shortName, id, url, panelType, color, timestamp) SHALL be preserved

#### Scenario: Nested structures roundtrip

- **WHEN** an ADF document containing nested elements
  (e.g., panel inside expand, list inside panel) is converted to Markdown and back
- **THEN** the nesting structure SHALL be preserved
- **AND** all elements at every nesting level SHALL be present in the output

## REMOVED Requirements

### Requirement: Upload Markdown to ADF via v2 API

**Reason**: The Storage Format fallback path (`--legacy` flag and marker-free fallback to v1 API) is being removed. All uploads SHALL use ADF v2 exclusively. The scenarios for legacy/fallback behavior are replaced by the simplified requirement below.

**Migration**: Remove `--legacy` flag. All markdown uploads go through `markdown_to_adf.py` → v2 API regardless of marker presence.
