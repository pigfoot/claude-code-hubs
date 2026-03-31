---
name: confluence
description: Confluence doc management. Use for Confluence URLs (/wiki/x/... short URLs), reading/uploading/downloading/searching/creating/updating pages, Markdown→ADF conversion, and syncing docs to Confluence.
---

# Confluence Skill

## Critical Rules

- **DO NOT use MCP for page uploads** — size limit ~10-20KB. Use `upload_confluence.py` instead.
- **DO NOT use MCP for structural modifications** — AI tool delays cause 650x slowdown (~13min vs ~1s). Use REST API scripts.
- **DO NOT create temporary analysis scripts** (`/tmp/analyze_*.py`). Use existing `analyze_page.py`.
- **DO NOT write inline scripts to manipulate ADF JSON** — use the structural scripts which handle ADF marks correctly.
- **DO NOT use raw XML/HTML** for images. Use markdown syntax: `![alt](path.png)`.
- **DO NOT forget diagram conversion** — pre-convert Mermaid/PlantUML to PNG/SVG before upload.
- MCP is fine for **reading pages** and **simple text edits** (Method 6).

## Architecture

```
New page:     Markdown → markdown_to_adf.py (pre-processor + mistune) → ADF JSON → REST API v2
Edit page:    REST API v2 GET ADF → Method 6 JSON diff/patch → REST API v2 PUT ADF
Download:     REST API v2 GET ADF → adf_to_markdown.py → readable Markdown (display only)
Structural:   Direct REST API scripts (add_table_row.py, add_panel.py, etc.) → ~1s each
Attachment:   v1 REST API (no v2 equivalent)
Page width:   v1 REST API property (no v2 equivalent)
MCP fallback: markdown_to_adf() → ADF JSON → MCP createPage(contentFormat="adf")
```

Key points:

- **Method 6 roundtrip** never goes through Markdown — ADF in, ADF out
- `adf_to_markdown.py` is display-only (for Claude to read), not a data conversion step
- `markdown_to_adf.py` includes a pre-processor that fixes emoji lines (✅/❌) and `[ ]` checkboxes
- MCP upload: always use `contentFormat: "adf"`, NOT `"markdown"` (MCP markdown merges emoji lines)
- Upload priority: REST API v2 ADF (primary) → MCP ADF (fallback, no API token)

## Decision Matrix

All `.py` scripts run with: `uv run --managed-python scripts/SCRIPT_NAME.py`

| Task | Tool | Speed | Notes |
|------|------|-------|-------|
| Analyze page structure | `analyze_page.py` | <1s | Shows all components |
| Edit text (preserve macros) | MCP Method 6 | Interactive | Recommended for existing pages |
| Add table row | `add_table_row.py` | ~1s | 650x faster than MCP |
| Add list item | `add_list_item.py` | ~1s | Bullet or numbered |
| Add panel | `add_panel.py` | ~1s | info/note/warning/success |
| Insert section | `insert_section.py` | ~1s | Heading + content |
| Add code line | `add_to_codeblock.py` | ~1s | Insert into code block |
| Add blockquote | `add_blockquote.py` | ~1s | Citations |
| Add horizontal rule | `add_rule.py` | ~1s | Section divider |
| Add image | `add_media.py` | ~2-5s | Upload + embed |
| Add image group | `add_media_group.py` | ~3-8s | Multiple images |
| Upload attachment | `upload_attachment.py` | ~2-8s | Any file type |
| Add nested expand | `add_nested_expand.py` | ~1s | Expand inside expand |
| Add status label | `add_status.py` | ~1s | TODO/DONE/IN PROGRESS |
| Add @mention | `add_mention.py` | ~1s | Notify users |
| Add date | `add_date.py` | ~1s | Inline timestamp |
| Add emoji | `add_emoji.py` | ~1s | Visual expressions |
| Add inline card | `add_inline_card.py` | ~1s | Rich URL preview |
| Upload new/replace page | `upload_confluence.py` | ~5-10s | Markdown → ADF → v2 API |
| Download page | `download_confluence.py` | ~5-10s | ADF → readable Markdown |
| Read/search pages | MCP tools | Fast | OK for reading |
| Small page create (<10KB) | MCP create (ADF) | Slow | Use contentFormat="adf" |
| Markdown ↔ Wiki | `convert_markdown_to_wiki.py` | Fast | Format conversion |

## Workflows

### Reading Pages

1. Resolve URL → page ID:

   ```bash
   uv run --managed-python scripts/url_resolver.py "URL"
   ```

2. Read via MCP:

   ```javascript
   mcp__plugin_confluence_atlassian__getConfluencePage({
     cloudId: "site.atlassian.net", pageId: "PAGE_ID", contentFormat: "markdown"
   })
   ```

### Method 6: Edit Existing Pages (Recommended)

Edits text while preserving all macros. Operates directly on ADF JSON — Markdown is display-only.

**When to use**: Fix typos, improve clarity, update docs on pages with macros.
**Not for**: New pages (use `upload_confluence.py`), massive restructuring.

Usage — natural language:

```
"Edit Confluence page 123456 to fix typos"
"Update API docs on page 789012"
```

Workflow:

1. Read page via MCP → auto-detect macros
2. Safe mode (default): edit outside macros only. Advanced mode: edit inside macros (requires confirmation)
3. Auto-backup to `.confluence_backups/{page_id}/` (keeps last 10)
4. Write back via v2 API (auto-restore on failure)

Implementation: `scripts/mcp_json_diff_roundtrip.py`

### Upload Markdown (New Page / Full Replace)

`upload_confluence.py` converts Markdown → ADF via `markdown_to_adf.py` → uploads via REST API v2.

```bash
# Update existing page
uv run --managed-python scripts/upload_confluence.py doc.md --id PAGE_ID

# Create new page
uv run --managed-python scripts/upload_confluence.py doc.md --space SPACE_KEY --parent-id PARENT_ID

# Auto-detect from frontmatter
uv run --managed-python scripts/upload_confluence.py doc.md

# Options: --dry-run, --title "...", --width narrow, --table-layout default
```

User intent mapping:

- "Upload X under page Y" → `--space` + `--parent-id`
- "Update page 123" → `--id 123`
- "Upload this downloaded file" → no args (frontmatter)

Frontmatter options:

```yaml
---
title: "My Page"
confluence:
  id: "123456"
  width: full           # full (default) or narrow
  table:
    layout: full-width  # full-width (default) or default
    colwidths: [12, 10, 40, 38]
---
```

#### MCP Upload Fallback (No API Token)

Always use `contentFormat: "adf"` with pre-processed ADF. MCP's `"markdown"` mode
merges emoji lines into one paragraph.

```python
from markdown_to_adf import markdown_to_adf
import json
adf_body = markdown_to_adf(markdown_content)
# MCP createConfluencePage with contentFormat="adf", body=json.dumps(adf_body)
```

### Download Page (Display Utility)

Downloads via v2 ADF API → converts to readable Markdown. **Display only** — use Method 6 for roundtrip editing.

```bash
uv run --managed-python scripts/download_confluence.py PAGE_ID
uv run --managed-python scripts/download_confluence.py --download-children PAGE_ID
uv run --managed-python scripts/download_confluence.py --output-dir ./docs PAGE_ID
```

Custom markers in downloaded Markdown:

- `<!-- EXPAND: "title" --> ... <!-- /EXPAND -->`, `<!-- PANEL: type --> ... <!-- /PANEL -->`
- `:shortname:` (emoji), `<!-- MENTION: id "name" -->`, `<!-- CARD: url -->`
- `<!-- STATUS: "text" color -->`, `<!-- DATE: timestamp -->`

These markers are recognized by `upload_confluence.py` for page duplication/migration.

### Structural Modifications (Direct REST API)

650x faster than MCP (~1s vs ~13min). Example:

```bash
uv run --managed-python scripts/add_table_row.py PAGE_ID \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Elasticsearch Cluster" "@Data Team" "Read-Only" \
  --dry-run
```

Common patterns for structural scripts:

```bash
# Most scripts: PAGE_ID + --after-heading or --at-end + content args + --dry-run
uv run --managed-python scripts/add_panel.py PAGE_ID --after-heading "Setup" --panel-type info --content "Note text" --dry-run
uv run --managed-python scripts/add_list_item.py PAGE_ID --after-heading "TODO" --item "New task" --position end
uv run --managed-python scripts/insert_section.py PAGE_ID --new-heading "New Section" --level 2 --after-heading "Existing"
uv run --managed-python scripts/add_media.py PAGE_ID --image-path "./img.png" --at-end --width 500
uv run --managed-python scripts/add_status.py PAGE_ID --search-text "Status:" --status "TODO" --color blue
uv run --managed-python scripts/add_mention.py PAGE_ID --search-text "Owner:" --user-id "557058..." --display-name "John"
uv run --managed-python scripts/analyze_page.py PAGE_ID [--type codeBlock|table|bulletList]
```

### Search (MCP)

```javascript
mcp__plugin_confluence_atlassian__searchConfluenceUsingCql({
  cloudId: "site.atlassian.net",
  cql: 'space = "DEV" AND text ~ "API"',
  limit: 10
})
```

### Convert Markdown ↔ Wiki Markup

```bash
uv run --managed-python scripts/convert_markdown_to_wiki.py input.md output.wiki
```

### Create/Update Pages via MCP (Small Documents Only)

```javascript
// Create page
mcp__plugin_confluence_atlassian__createConfluencePage({
  cloudId: "site.atlassian.net", spaceId: "SPACE_ID",
  title: "Page Title", contentFormat: "adf", body: JSON.stringify(adfJson)
})

// Update page
mcp__plugin_confluence_atlassian__updateConfluencePage({
  cloudId: "site.atlassian.net", pageId: "PAGE_ID",
  title: "Title", contentFormat: "adf", body: JSON.stringify(adfJson)
})
```

## Editing Existing Pages: Decision Order

1. **Structural scripts** (add_table_row, insert_section, add_panel...) → precise, fast, ~1s
2. **Method 6** (mcp_json_diff_roundtrip) → free-form text editing, fix typos, AI-driven
3. **upload_confluence.py** → full page replacement (last resort)

Always start with `analyze_page.py PAGE_ID` to understand the page structure first.

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Creating temp scripts | Use existing: `analyze_page.py` |
| Using raw XML | Use markdown: `![alt](path.png)` |
| MCP for uploads | Use `upload_confluence.py` |
| Forgetting diagram conversion | Pre-convert Mermaid/PlantUML to PNG/SVG |
| Method 6 for structural changes | Use REST API scripts (add_table_row, etc.) |
| MCP `contentFormat: "markdown"` | Use `contentFormat: "adf"` with pre-processed ADF |
| Ignoring 401 Unauthorized | Run `/mcp` to re-authenticate |

## Image Handling

1. Convert diagrams if needed: `mmdc -i diagram.mmd -o diagram.png` or `plantuml diagram.puml -tpng`
2. Use markdown syntax: `![alt](./path/to/image.png)`
3. Upload: `uv run --managed-python scripts/upload_confluence.py doc.md --id PAGE_ID`

## Checklists

**Upload**: Convert diagrams → Use markdown image syntax → `--dry-run` test → Upload with script → Verify page

**Download**: Get page ID (use `url_resolver.py` for short URLs) → Set output dir → Run download → Verify attachments

## Script Reference

All scripts: `uv run --managed-python scripts/SCRIPT_NAME.py`

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_page.py` | Analyze page structure, suggest tools | `PAGE_ID [--type codeBlock\|table\|...]` |
| `add_table_row.py` | Add table row (~1s) | `PAGE_ID --table-heading "..." --after-row-containing "..." --cells "..." "..."` |
| `add_list_item.py` | Add bullet/numbered list item | `PAGE_ID --after-heading "..." --item "..." [--position start\|end]` |
| `add_panel.py` | Add info/warning/note/success panel | `PAGE_ID --after-heading "..." --panel-type info --content "..."` |
| `insert_section.py` | Insert heading + content | `PAGE_ID --new-heading "..." --level 2 [--after-heading "..."]` |
| `add_to_codeblock.py` | Add line to code block | `PAGE_ID --search-text "..." --add-line "..." [--position after]` |
| `add_blockquote.py` | Add blockquote | `PAGE_ID --quote "..." [--after-heading "..."\|--at-end]` |
| `add_rule.py` | Add horizontal rule | `PAGE_ID [--after-heading "..."\|--at-end]` |
| `add_media.py` | Upload + embed image | `PAGE_ID --image-path "./img.png" [--after-heading "..."\|--at-end] [--width 500]` |
| `add_media_group.py` | Multiple images in row | `PAGE_ID --images "./img1.png" "./img2.png" [--after-heading "..."\|--at-end]` |
| `upload_attachment.py` | Upload any file type | `PAGE_ID --file "./report.pdf" --at-end` |
| `add_nested_expand.py` | Nested expand panel | `PAGE_ID --parent-expand "Details" --title "More" --content "..."` |
| `add_status.py` | Add status label | `PAGE_ID --search-text "..." --status "TODO" [--color blue]` |
| `add_mention.py` | Add @mention | `PAGE_ID --search-text "..." --user-id "557058..." [--display-name "John"]` |
| `add_date.py` | Add inline date | `PAGE_ID --search-text "..." --date "2026-03-15"` |
| `add_emoji.py` | Add emoji | `PAGE_ID --search-text "..." --emoji ":smile:"` |
| `add_inline_card.py` | Add URL preview card | `PAGE_ID --search-text "..." --url "https://..."` |
| `upload_confluence.py` | Upload Markdown as page | `doc.md --id PAGE_ID` or `doc.md --space KEY --parent-id ID` |
| `download_confluence.py` | Download page as Markdown | `PAGE_ID [--download-children] [--output-dir ./docs]` |
| `convert_markdown_to_wiki.py` | Markdown ↔ Wiki Markup | `input.md output.wiki` |
| `mcp_json_diff_roundtrip.py` | Method 6 text editing | Used internally by Method 6 workflow |

All structural scripts support `--dry-run` for preview.

Scripts that accept text input (`add_list_item`, `add_panel`, `add_blockquote`, `insert_section`,
`add_nested_expand`) support **markdown inline syntax** which is auto-converted to ADF marks:

- `` `code` `` → code mark, `**bold**` → strong mark, `*italic*` → em mark, `~~strike~~` → strike mark

Example: `--item '`"compat"`- **REQUIRED** for all models'` correctly renders as code + bold in Confluence.

## When NOT to Use Scripts

- Simple page reads → MCP directly
- Small content, no images (<10KB) → MCP may work
- Jira issues → Use Jira-specific tools

## Prerequisites

- **`uv`** — all scripts use PEP 723 inline metadata
- **Env vars**: `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` (for REST API scripts)
- **MCP**: Atlassian MCP Server with Confluence credentials (for reading/Method 6)
- Optional: `mark` CLI (Git-to-Confluence sync), Mermaid CLI (diagram rendering)

## References

- [Wiki Markup Guide](references/wiki_markup_guide.md) - Syntax reference
- [CQL Reference](references/cql_reference.md) - Query language
- [Mention Account ID Lookup](references/mention-account-id-lookup.md) - Find user IDs
- [Troubleshooting](references/troubleshooting.md) - Common errors and fixes
