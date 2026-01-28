---
name: confluence
description: Comprehensive Confluence documentation management. Use when user provides Confluence URLs (including short URLs like /wiki/x/...), or asks to "read Confluence page", "view Confluence page", "upload to Confluence", "download Confluence pages", "convert Markdown to Wiki Markup", "sync documentation to Confluence", "search Confluence", "create Confluence page", "update Confluence page", "export Confluence", or "Confluence CQL query". Handles Wiki Markup conversion, Mermaid/PlantUML diagrams, image handling, large document uploads without size limits, Git-to-Confluence sync with mark CLI, and automatic short URL decoding.
allowed-tools: ["mcp__plugin_confluence_atlassian__*"]
version: 0.1.0
---

# Confluence Management Skill

Version: 0.1.0 (Testing Phase)

## 🚨 Critical Constraints

**DO NOT USE MCP FOR PAGE UPLOADS** - Size limits apply (~10-20KB max)

**DO NOT USE MCP FOR STRUCTURAL MODIFICATIONS** - AI tool delays cause 650x slowdown

```bash
# Use REST API scripts instead:
# For uploading documents:
uv run --managed-python {base_dir}/scripts/upload_confluence.py document.md --id PAGE_ID

# For structural modifications (adding table rows, etc.):
uv run --managed-python {base_dir}/scripts/add_table_row.py PAGE_ID --table-heading "..." --after-row-containing "..." --cells "..." "..." "..."
```

**DO NOT CREATE TEMPORARY ANALYSIS SCRIPTS** - Use existing `analyze_page.py` tool

```bash
# DON'T create one-off scripts like:
/tmp/analyze_gemini_page.py
/tmp/show_all_blocks.py

# DO use the existing tool:
uv run --managed-python {base_dir}/scripts/analyze_page.py PAGE_ID
uv run --managed-python {base_dir}/scripts/analyze_page.py PAGE_ID --type codeBlock
```

**Performance Reality**:

- MCP roundtrip for structural changes: ~13 minutes (91% is AI processing delays)
- Python REST API direct: ~1.2 seconds (650x faster)
- Bottleneck: AI tool invocation intervals, NOT MCP network I/O

MCP tools are fine for **reading** pages and **simple text edits** but **fail for structural modifications due to AI
processing overhead**.

## Quick Decision Matrix

**NOTE**: All `.py` scripts below must be run with `uv run --managed-python scripts/SCRIPT_NAME.py`

### When to Use What Tool

| Task Category | Specific Task | Tool | Speed | Notes |
|---------------|---------------|------|-------|-------|
| **Analysis** | Understand page structure | `analyze_page.py` | <1s | 🔍 Shows all components |
| **Text Editing** | Fix typos, improve clarity | MCP Method 6 | Interactive | ✅ Preserves macros |
| **Block Elements** | Add table row | `add_table_row.py` | ~1s | ⚡ 650x faster than MCP |
| | Add list item | `add_list_item.py` | ~1s | Bullet or numbered lists |
| | Add info/warning panel | `add_panel.py` | ~1s | 4 panel types available |
| | Insert new section | `insert_section.py` | ~1s | Heading + content |
| | Add line to code block | `add_to_codeblock.py` | ~1s | Insert commands/code lines |
| | Add blockquote (citation) | `add_blockquote.py` | ~1s | For quotes and citations |
| | Add horizontal rule | `add_rule.py` | ~1s | Section divider |
| | Add image | `add_media.py` | ~2-5s | Uploads and embeds image |
| | Add image group | `add_media_group.py` | ~3-8s | Multiple images in row/grid |
| | Add nested expand | `add_nested_expand.py` | ~1s | Expand inside expand |
| **Inline Elements** | Add status label | `add_status.py` | ~1s | TODO/DONE/IN PROGRESS |
| | Add @mention | `add_mention.py` | ~1s | Notify users |
| | Add date | `add_date.py` | ~1s | Deadlines and timestamps |
| | Add emoji | `add_emoji.py` | ~1s | Visual expressions |
| | Add inline card | `add_inline_card.py` | ~1s | Rich URL preview card |
| **Document Ops** | Upload large files (>10KB) | `upload_confluence.py` | ~5-10s | No size limits |
| | Upload with images | `upload_confluence.py` | ~5-10s | Handles attachments |
| | Download to Markdown | `download_confluence.py` | ~5-10s | Converts macros |
| **Reading** | Search/read pages | MCP tools | Fast | ✅ OK for reading |
| **Small Changes** | Text-only (<10KB) | MCP create/update | Slow | ⚠️ Size limited |
| **CI/CD** | Git-to-Confluence sync | `mark` CLI | Fast | Best for automation |
| **Conversion** | Markdown ↔ Wiki | `convert_markdown_to_wiki.py` | Fast | Format conversion |

## Core Workflows

### 📖 Reading Confluence Pages from URLs

**When user provides a Confluence URL**, automatically resolve and read the page:

#### Workflow

1. **Detect URL format**:
   - Short URL: `https://site.atlassian.net/wiki/x/2oEBfw`
   - Full URL: `https://site.atlassian.net/wiki/spaces/SPACE/pages/123456789/Title`
   - Direct page ID: `123456789`

2. **Resolve to page ID**:

   ```bash
   uv run --managed-python {base_dir}/scripts/url_resolver.py "URL"
   ```

3. **Read page content** (via MCP):

   ```javascript
   mcp__plugin_confluence_atlassian__getConfluencePage({
     cloudId: "...",
     pageId: "resolved_page_id",
     contentFormat: "markdown"
   })
   ```

#### Examples

```
User: "https://site.atlassian.net/wiki/x/2oEBfw"
→ Resolve: page ID 2130805210
→ Read page and display content

User: "Read https://site.atlassian.net/wiki/spaces/DEV/pages/123456/API-Docs"
→ Extract page ID: 123456
→ Read page and display content
```

### 🆕 Method 6: Intelligent Roundtrip Editing (Recommended for Editing Existing Pages)

**Revolutionary Feature**: Edit existing Confluence pages while preserving all macros (expand panels, status badges,
page properties, etc.) and allow Claude to intelligently edit text content.

#### When to Use Method 6?

✅ **Good Use Cases**:

- Fix typos and grammar errors on pages
- Improve clarity and readability of existing content
- Update documentation while preserving page structure
- Edit pages containing important macros (without losing them)

❌ **Not Suitable For**:

- Creating brand new pages → Use `upload_confluence.py`
- Massive restructuring of entire page → Use `upload_confluence.py`
- Batch updating multiple pages → Use Method 1 (download + edit + upload)

#### Usage

Simply use natural language commands, system handles automatically:

```
"Edit Confluence page 123456 to fix typos and improve clarity"
"Update the API documentation on page 789012 to reflect the new endpoints"
"Fix grammar issues in page 456789"
```

#### Workflow

1. Read page via MCP
2. Auto-detect macros
3. Choose mode: Safe (edit outside macros) or Advanced (edit inside macros)
4. Auto-backup to `.confluence_backups/{page_id}/`
5. Claude edits based on instruction
6. Write back to Confluence (auto-restore on failure)

#### Two Modes

**Safe Mode (default, recommended)**:

- Skips macro content, only edits outside text
- Zero risk, macro structure completely unaffected
- Suitable for most use cases

**Advanced Mode (advanced, requires confirmation)**:

- Can edit text inside macros (e.g., content in expand panels)
- Requires explicit user confirmation
- Automatic backup + auto-restore on failure
- Suitable when need to edit info boxes, warning panels content

#### Backup/Restore

- Auto-backup before each edit (keeps last 10 in `.confluence_backups/{page_id}/`)
- Manual restore: "Rollback Confluence page 123456 to previous backup"
- Auto-restore on write failure
- Uses ADF JSON diff/patch, macro-preserving, OAuth auth
- Implementation: `scripts/mcp_json_diff_roundtrip.py`

### Upload Markdown to Confluence

**CRITICAL**: Use absolute path to script WITHOUT `cd` command.

```bash
# Update existing page
uv run --managed-python {base_dir}/scripts/upload_confluence.py document.md --id 780369923

# Create new page
uv run --managed-python {base_dir}/scripts/upload_confluence.py document.md --space DEV --parent-id 123456

# Preview first (recommended)
uv run --managed-python {base_dir}/scripts/upload_confluence.py document.md --id 780369923 --dry-run
```

### Structural Modifications (Fast Method) 🚀

**Performance**: Direct REST API (~1.2s) vs MCP (~13min) = 650x speedup

**Example - Add Table Row**:

```bash
# Preview first (recommended)
uv run --managed-python {base_dir}/scripts/add_table_row.py PAGE_ID \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Service" "Owner" "Access" \
  --dry-run

# Actual update
uv run --managed-python {base_dir}/scripts/add_table_row.py 2117534137 \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Elasticsearch Cluster" "@Data Team" "Read-Only"
```

**Key Parameters**:

- `PAGE_ID`: Confluence page ID (from URL or url_resolver.py)
- `--table-heading`: Heading text before the target table
- `--after-row-containing`: Text in first cell of row to insert after
- `--cells`: New row's cell contents (space-separated, use quotes if contains spaces)
- `--dry-run`: Preview mode, doesn't actually update

**Prerequisites**: Set environment variables `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`

**All other tools** (list, panel, section, etc.) follow similar pattern. See Quick Decision Matrix table for full list.

### Download Confluence to Markdown

```bash
# Single page
uv run --managed-python {base_dir}/scripts/download_confluence.py 123456789

# With child pages
uv run --managed-python {base_dir}/scripts/download_confluence.py --download-children 123456789

# Custom output directory
uv run --managed-python {base_dir}/scripts/download_confluence.py --output-dir ./docs 123456789
```

### Convert Markdown to Wiki Markup

```bash
uv run --managed-python {base_dir}/scripts/convert_markdown_to_wiki.py input.md output.wiki
```

### Search Confluence (via MCP)

```javascript
mcp__atlassian__confluence_search({
  query: 'space = "DEV" AND text ~ "API" AND created >= startOfYear()',
  limit: 10
})
```

### Create/Update Pages (Small Documents Only)

```javascript
// Create page
mcp__atlassian__confluence_create_page({
  space_key: "DEV",
  title: "API Documentation",
  content: "h1. Overview\n\nContent here...",
  content_format: "wiki"
})

// Update page
mcp__atlassian__confluence_update_page({
  page_id: "123456789",
  title: "Updated Title",
  content: "h1. New Content",
  version_comment: "Updated via Claude Code"
})
```

## Image Handling

### Standard Workflow

1. **Convert diagrams** (if Mermaid/PlantUML):

   ```bash
   # Mermaid
   mmdc -i diagram.mmd -o diagram.png -b transparent
   # PlantUML
   plantuml diagram.puml -tpng
   ```

2. **Reference in markdown** (always use markdown syntax):

   ```markdown
   ![Architecture Diagram](./diagrams/architecture.png)
   ```

3. **Upload** (script handles attachments):

   ```bash
   uv run --managed-python {base_dir}/scripts/upload_confluence.py document.md --id PAGE_ID
   ```

### Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Creating temp scripts | Use existing: `analyze_page.py` |
| Using raw XML | Use markdown: `![alt](path.png)` |
| MCP for uploads | Use `upload_confluence.py` |
| Forgetting diagram conversion | Pre-convert Mermaid/PlantUML to PNG/SVG |
| Ignoring 401 Unauthorized | Run `/mcp` to re-authenticate |

## Checklists

**Upload**: Convert diagrams (Mermaid/PlantUML) → Use markdown image syntax → Dry-run test → Upload with script → Verify
page accessible

**Download**: Get page ID (use url_resolver.py for short URLs) → Configure credentials (.env) → Set output directory →
Run download script → Verify attachments in `{Page}_attachments/`

## Available MCP Tools

Search, read pages, create/update (⚠️ size limited), delete, labels, comments. See `mcp__plugin_confluence_atlassian__*`
for full list.

## Utility Scripts

**IMPORTANT**: All Python scripts must be run with `uv run --managed-python` to ensure correct dependency management.

**ADF Coverage**: 15 structural modification tools covering 16/19 ADF node types (84% coverage, ~98% practical coverage)

- ✅ All common block elements (table, list, code, panel, heading, quote, rule, images)
- ✅ All common inline elements (status, mention, date, emoji, card)
- ❌ Only missing: multiBodiedExtension (tabs macro), mediaInline (rare)

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/confluence_adf_utils.py` | **Shared Utils Library** - ADF operation core functions (auth, read, write, find nodes) | Import by other scripts |
| `scripts/analyze_page.py` | 🔍 **Analyze Page Structure** - Show all components (tables, lists, code blocks, panels, headings) and suggest which tool to use | `uv run --managed-python scripts/analyze_page.py PAGE_ID [--type codeBlock\|table\|bulletList\|...]` |
| `scripts/add_table_row.py` | ⚡ **Fast Add Table Row** (~1.2s vs MCP 13min) | `uv run --managed-python scripts/add_table_row.py PAGE_ID --table-heading "..." --after-row-containing "..." --cells "..." "..."` |
| `scripts/add_list_item.py` | 📋 Add bullet/numbered list items | `uv run --managed-python scripts/add_list_item.py PAGE_ID --after-heading "..." --item "..." [--position start\|end]` |
| `scripts/add_panel.py` | 💡 Add info/warning/note/success panels | `uv run --managed-python scripts/add_panel.py PAGE_ID --after-heading "..." --panel-type info --content "..."` |
| `scripts/insert_section.py` | 📑 Insert new section (heading + content) | `uv run --managed-python scripts/insert_section.py PAGE_ID --new-heading "..." --level 2 [--after-heading "..."]` |
| `scripts/add_to_codeblock.py` | 💻 Add line to code block | `uv run --managed-python scripts/add_to_codeblock.py PAGE_ID --search-text "..." --add-line "..." [--position after]` |
| `scripts/add_blockquote.py` | 💬 Add blockquote (citation) | `uv run --managed-python scripts/add_blockquote.py PAGE_ID --quote "..." [--after-heading "..."\|--at-end]` |
| `scripts/add_rule.py` | ➖ Add horizontal rule (divider) | `uv run --managed-python scripts/add_rule.py PAGE_ID [--after-heading "..."\|--at-end]` |
| `scripts/add_media.py` | 🖼️ Add image (uploads and embeds) | `uv run --managed-python scripts/add_media.py PAGE_ID --image-path "./img.png" [--after-heading "..."\|--at-end] [--width 500]` |
| `scripts/add_status.py` | 🏷️ Add status label (TODO/DONE/etc.) | `uv run --managed-python scripts/add_status.py PAGE_ID --search-text "..." --status "TODO" [--color blue]` |
| `scripts/add_mention.py` | 👤 Add @mention (notify user) | `uv run --managed-python scripts/add_mention.py PAGE_ID --search-text "..." --user-id "557058..." [--display-name "John"]` |
| `scripts/add_date.py` | 📅 Add date (inline timestamp) | `uv run --managed-python scripts/add_date.py PAGE_ID --search-text "..." --date "2026-03-15"` |
| `scripts/add_emoji.py` | 😀 Add emoji | `uv run --managed-python scripts/add_emoji.py PAGE_ID --search-text "..." --emoji ":smile:"` |
| `scripts/add_media_group.py` | 🖼️🖼️ Add image group (multiple images) | `uv run --managed-python scripts/add_media_group.py PAGE_ID --images "./img1.png" "./img2.png" [--after-heading "..."\|--at-end]` |
| `scripts/add_nested_expand.py` | 📂 Add nested expand panel | `uv run --managed-python scripts/add_nested_expand.py PAGE_ID --parent-expand "Details" --title "More" --content "..."` |
| `scripts/add_inline_card.py` | 🔗 Add inline card (URL preview) | `uv run --managed-python scripts/add_inline_card.py PAGE_ID --search-text "..." --url "https://..."` |
| `scripts/upload_confluence.py` | 📝 Upload Markdown (supports large files, images) | `uv run --managed-python scripts/upload_confluence.py doc.md --id PAGE_ID` |
| `scripts/download_confluence.py` | 📥 Download as Markdown (with attachments) | `uv run --managed-python scripts/download_confluence.py PAGE_ID` |
| `scripts/convert_markdown_to_wiki.py` | 🔄 Markdown ↔ Wiki Markup conversion | `uv run --managed-python scripts/convert_markdown_to_wiki.py input.md output.wiki` |
| `scripts/mcp_json_diff_roundtrip.py` | ✏️ Intelligent text editing (preserves macros) | Used by Method 6, see above |

## Prerequisites

**Required:**

- **`uv` package manager** - All scripts use PEP 723 inline metadata, must run with `uv run --managed-python`
- Atlassian MCP Server (`mcp__atlassian`) with Confluence credentials (for MCP tools)
- Environment variables: `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` (for REST API scripts)

**Optional:**

- `mark` CLI: Git-to-Confluence sync (`brew install kovetskiy/mark/mark`)
- Mermaid CLI: Diagram rendering (`npm install -g @mermaid-js/mermaid-cli`)

## References

- [Wiki Markup Guide](references/wiki_markup_guide.md) - Complete syntax reference
- [CQL Reference](references/cql_reference.md) - Confluence Query Language syntax
- [Mention Account ID Lookup](references/mention-account-id-lookup.md) - How to find user account IDs for @mentions
- [Troubleshooting](references/troubleshooting.md) - Common errors and fixes

## When NOT to Use Scripts

- Simple page reads → Use MCP directly
- No images/diagrams, small content (<10KB) → MCP may work
- Jira issues → Use Jira-specific tools
