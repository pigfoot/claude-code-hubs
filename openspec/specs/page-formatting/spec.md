# page-formatting Specification

## Purpose

Page width control and table column width formatting for Confluence
pages created via storage format upload (`upload_confluence.py`).

## Requirements

### Requirement: Page width control

The system SHALL default to full-width page layout when creating or
updating Confluence pages via `upload_confluence.py`.

#### Scenario: Default full-width on create

- **WHEN** user creates a page via `upload_confluence.py` without
  specifying width
- **THEN** the system SHALL pass `full_width=True` to `create_page()`
- **AND** the page SHALL render in full-width layout in Confluence

#### Scenario: Default full-width on update

- **WHEN** user updates a page via `upload_confluence.py` without
  specifying width
- **THEN** the system SHALL pass `full_width=True` to `update_page()`
- **AND** the page SHALL render in full-width layout in Confluence

#### Scenario: Override width via CLI

- **WHEN** user specifies `--width narrow`
- **THEN** the system SHALL pass `full_width=False` to the API call
- **AND** the page SHALL render in narrow (fixed-width) layout

#### Scenario: Override width via frontmatter

- **WHEN** Markdown frontmatter contains `confluence.width: narrow`
- **THEN** the system SHALL pass `full_width=False` to the API call
- **AND** CLI `--width` flag SHALL take precedence over frontmatter

---

### Requirement: Table layout control

The system SHALL render tables with `data-layout="full-width"` by
default in storage format output.

#### Scenario: Default full-width table

- **WHEN** Markdown contains a table and no layout override is specified
- **THEN** the system SHALL render
  `<table data-layout="full-width">` in storage format

#### Scenario: Override table layout via CLI

- **WHEN** user specifies `--table-layout default`
- **THEN** the system SHALL render `<table data-layout="default">`

#### Scenario: Override table layout via frontmatter

- **WHEN** Markdown frontmatter contains
  `confluence.table.layout: default`
- **THEN** the system SHALL render `<table data-layout="default">`
- **AND** CLI `--table-layout` flag SHALL take precedence over
  frontmatter

---

### Requirement: Table column width control

The system SHALL support column width configuration via frontmatter
ratios, generating `<colgroup>` elements in storage format.

#### Scenario: Column widths from frontmatter

- **WHEN** Markdown frontmatter contains
  `confluence.table.colwidths: [12, 10, 40, 38]`
- **THEN** the system SHALL generate a `<colgroup>` with `<col>`
  elements using proportional pixel widths based on 1280px total
- **AND** the rendered table SHALL have
  `<col style="width: 153.6px;" />` for ratio value 12
- **AND** `<col style="width: 128px;" />` for ratio value 10
- **AND** `<col style="width: 512px;" />` for ratio value 40
- **AND** `<col style="width: 486.4px;" />` for ratio value 38

#### Scenario: No column widths specified

- **WHEN** Markdown frontmatter does not contain
  `confluence.table.colwidths`
- **THEN** the system SHALL NOT generate `<colgroup>` elements
- **AND** Confluence SHALL auto-distribute column widths equally

#### Scenario: Column count mismatch

- **WHEN** frontmatter `colwidths` array length does not match the
  number of columns in a table
- **THEN** the system SHALL skip `<colgroup>` generation for that table
- **AND** the system SHALL print a warning message

#### Scenario: Colwidths apply to all matching tables

- **WHEN** frontmatter specifies `colwidths` and the Markdown file
  contains multiple tables
- **THEN** the system SHALL apply `<colgroup>` to every table whose
  column count matches the `colwidths` array length
