## Why

Pages created via `upload_confluence.py` render with narrow (fixed-width)
layout and tables have no column width control. This makes programmatically
created pages look worse than manually-created ones. The fix is small
(verified experimentally) but impacts every page the Confluence skill creates.

## What Changes

- Default page width changes from narrow (`fixed-width`) to wide
  (`full-width`) for all pages created/updated via `upload_confluence.py`
- Tables in storage format get `data-layout="full-width"` attribute
- Tables get `<colgroup>` column width support via frontmatter configuration
- CLI gains `--width` flag; frontmatter gains `confluence.width` and
  `confluence.table.colwidths` options
- Equal column distribution as safe default when no colwidths specified

## Capabilities

### New Capabilities

- `page-formatting`: Page width control and table column width formatting
  for Confluence pages created via storage format upload

### Modified Capabilities

(None - roundtrip editing uses MCP/ADF which does not touch page width
content properties)

## Impact

- `plugins/confluence/skills/confluence/scripts/upload_confluence.py` -
  renderer changes + CLI/frontmatter options
- `plugins/confluence/skills/confluence/SKILL.md` - document new options
- `plugins/confluence/README.md` - document formatting capabilities
