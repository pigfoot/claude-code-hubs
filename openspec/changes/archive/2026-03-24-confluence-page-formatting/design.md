## Context

`upload_confluence.py` uses `atlassian-python-api` to create/update
Confluence pages via storage format (XHTML). Currently pages default to
narrow layout, and tables have no width or column control.

Experiments on page 2337112322 confirmed:
- `full_width=True` parameter works on `create_page()` / `update_page()`
- `<table data-layout="full-width">` works in storage format
- `<colgroup><col style="width: Npx;">` sets proportional column widths

Research details: `docs/plans/008-confluence-page-formatting/research.md`

## Goals / Non-Goals

**Goals:**
- Pages created via `upload_confluence.py` default to full-width layout
- Tables default to full-width with optional column width control
- Users can configure widths via CLI flags and frontmatter
- Changes are backward-compatible (existing pages update normally)

**Non-Goals:**
- Compact mode (frontend-only preference, no API)
- ADF-based table width control (separate scripts, different format)
- Table cell alignment beyond what Markdown provides
- Max-width support (new Feb 2026 feature, API value unconfirmed)

## Decisions

### Decision 1: Default page width = full-width

Pass `full_width=True` to both `create_page()` and `update_page()`.

Override via `--width narrow` CLI flag or `confluence.width: narrow`
in frontmatter.

**Why not narrow as default**: Most programmatically-generated pages
contain tables or data that benefit from wider layout. The user's
existing manually-formatted pages all use full-width.

### Decision 2: Default table layout = full-width

Render `<table data-layout="full-width">` for all tables.

Override via `--table-layout default` CLI flag or
`confluence.table.layout: default` in frontmatter.

**Alternatives considered**:
- `wide` — less common, `full-width` matches reference pages
- `default` — too narrow for data tables, defeats the purpose

### Decision 3: Column widths via frontmatter ratios

When `confluence.table.colwidths` is set in frontmatter, generate
`<colgroup>` with proportional pixel values. Example:

```yaml
confluence:
  table:
    colwidths: [12, 10, 40, 38]
```

Generates (assuming 1280px total):
```xml
<colgroup>
  <col style="width: 153.6px;" />
  <col style="width: 128px;" />
  <col style="width: 512px;" />
  <col style="width: 486.4px;" />
</colgroup>
```

**When no colwidths specified**: No `<colgroup>` generated. Confluence
auto-distributes equally. This is the safe default.

**Why ratio values, not pixels**: Users think in proportions (12:10:40:38),
not absolute pixels. The script converts to pixels using 1280px as the
reference width (matching the AI Community page).

**Why per-file, not per-table**: Most Markdown files uploaded to
Confluence have one table structure repeated. Per-table config would
require non-standard Markdown extensions.

### Decision 4: Colwidths apply to ALL tables in the file

When frontmatter specifies `colwidths`, it applies to every table in
the Markdown file. Tables with different column counts than the
`colwidths` array length get no `<colgroup>` (graceful fallback).

**Why**: Simple, predictable. The primary use case (cron pipeline pages)
has one table per page.

### Decision 5: Renderer changes are additive

The `ConfluenceStorageRenderer` changes:
- `table()` — add `data-layout` attribute
- No changes to `table_cell()`, `table_head()`, `table_body()`,
  `table_row()`

The renderer needs access to colwidths config. Pass it via constructor:

```python
renderer = ConfluenceStorageRenderer(
    table_layout="full-width",
    colwidths=[12, 10, 40, 38]  # or None
)
```

## Risks / Trade-offs

**[Existing pages become full-width on update]** → Expected behavior.
If user wants narrow, use `--width narrow`. Full-width is the better
default for data-heavy pages.

**[colwidths mismatch with table columns]** → Graceful fallback: if
colwidths array length != column count, skip colgroup for that table.
Log a warning.

**[thead vs tbody structure]** → Current renderer uses `<thead>` for
header rows. Confluence Cloud may expect headers in `<tbody>` with
`<th>` tags. Test confirms current `<thead>` approach works, so no
change needed. Monitor for issues.
