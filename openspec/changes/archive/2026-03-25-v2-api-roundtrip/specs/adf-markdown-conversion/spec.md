## ADDED Requirements

### Requirement: ADF to Markdown conversion

The system SHALL convert Atlassian Document Format (ADF) JSON to Markdown, preserving Confluence-specific elements using custom markers.

#### Scenario: Convert standard block elements

- **WHEN** ADF contains paragraph, heading, bulletList, orderedList, codeBlock, blockquote, rule, or table nodes
- **THEN** the system SHALL convert them to their standard Markdown equivalents
- **AND** preserve heading levels, list nesting, code language attributes, and table structure

#### Scenario: Convert text marks to inline formatting

- **WHEN** ADF text nodes contain marks (strong, em, code, link, strike, underline)
- **THEN** the system SHALL convert them to Markdown inline formatting:
  - `strong` → `**text**`
  - `em` → `*text*`
  - `code` → `` `text` ``
  - `link` → `[text](url)`
  - `strike` → `~~text~~`
  - `underline` → `<u>text</u>`

#### Scenario: Convert expand panels with markers

- **WHEN** ADF contains an `expand` node with title and content
- **THEN** the system SHALL output `<!-- EXPAND: "title" -->` before the content
- **AND** output `<!-- /EXPAND -->` after the content
- **AND** preserve breakout marks as attributes: `<!-- EXPAND: "title" breakout="wide" width="1800" -->`
- **AND** recursively convert the expand's content children

#### Scenario: Convert emojis inline

- **WHEN** ADF contains an `emoji` node with `shortName` attribute
- **THEN** the system SHALL output `:shortName:` inline (e.g., `:ms_teams:`)

#### Scenario: Convert mentions with markers

- **WHEN** ADF contains a `mention` node with `id` and `text` attributes
- **THEN** the system SHALL output `<!-- MENTION: id "text" -->` inline (e.g., `<!-- MENTION: 622a2c71 "@Michael Fu" -->`)

#### Scenario: Convert inline cards with markers

- **WHEN** ADF contains an `inlineCard` node with `url` attribute
- **THEN** the system SHALL output `<!-- CARD: url -->` inline

#### Scenario: Convert panels with markers

- **WHEN** ADF contains a `panel` node with `panelType` attribute and content
- **THEN** the system SHALL output `<!-- PANEL: panelType -->` before the content
- **AND** output `<!-- /PANEL -->` after the content
- **AND** recursively convert the panel's content children

#### Scenario: Convert status labels with markers

- **WHEN** ADF contains a `status` node with `text` and `color` attributes
- **THEN** the system SHALL output `<!-- STATUS: "text" color -->` inline

#### Scenario: Convert date nodes with markers

- **WHEN** ADF contains a `date` node with `timestamp` attribute
- **THEN** the system SHALL output `<!-- DATE: timestamp -->` inline

#### Scenario: Convert media nodes

- **WHEN** ADF contains a `mediaSingle` node wrapping a `media` node
- **THEN** the system SHALL output `![alt](filename)` using the media's filename attribute
- **AND** track the attachment reference for upload

#### Scenario: Handle unknown node types gracefully

- **WHEN** ADF contains a node type not explicitly handled
- **THEN** the system SHALL output `<!-- ADF:type {...attrs} -->` as a pass-through marker
- **AND** preserve the node's JSON attributes for roundtrip

#### Scenario: Handle nested structures

- **WHEN** ADF contains nested elements (e.g., expand inside panel, list inside expand)
- **THEN** the system SHALL recursively convert all nested content
- **AND** maintain correct marker nesting order

---

### Requirement: Markdown to ADF conversion

The system SHALL convert Markdown (with custom markers) to ADF JSON suitable for the Confluence v2 API.

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

#### Scenario: Parse date markers into ADF date nodes

- **WHEN** markdown contains `<!-- DATE: timestamp -->` markers
- **THEN** the system SHALL produce `{"type": "date", "attrs": {"timestamp": "..."}}` ADF nodes

#### Scenario: Restore unknown node type markers

- **WHEN** markdown contains `<!-- ADF:type {...attrs} -->` pass-through markers
- **THEN** the system SHALL reconstruct the original ADF node from the preserved JSON

#### Scenario: Handle marker-free markdown

- **WHEN** markdown contains no custom markers (old-style download or manually written)
- **THEN** the system SHALL produce valid ADF JSON from standard markdown elements only
- **AND** not fail or warn about missing markers

---

### Requirement: Roundtrip fidelity

The system SHALL maintain fidelity when converting ADF → Markdown → ADF for supported element types.

#### Scenario: Standard elements roundtrip

- **WHEN** an ADF document containing headings, paragraphs, lists, code blocks, tables, and blockquotes is converted to Markdown and back
- **THEN** the resulting ADF SHALL be structurally equivalent to the original
- **AND** text content SHALL be identical

#### Scenario: Confluence-specific elements roundtrip

- **WHEN** an ADF document containing expand, emoji, mention, inlineCard, panel, status, and date nodes is converted to Markdown and back
- **THEN** the resulting ADF SHALL contain all original Confluence-specific nodes
- **AND** node attributes (title, shortName, id, url, panelType, color, timestamp) SHALL be preserved

#### Scenario: Nested structures roundtrip

- **WHEN** an ADF document containing nested elements (e.g., panel inside expand, list inside panel) is converted to Markdown and back
- **THEN** the nesting structure SHALL be preserved
- **AND** all elements at every nesting level SHALL be present in the output
