---
name: confluence
description: Comprehensive Confluence documentation management. Use when asked to "upload to Confluence", "download Confluence pages", "convert Markdown to Wiki Markup", "sync documentation to Confluence", "search Confluence", "create Confluence page", "update Confluence page", "export Confluence", "publish to Confluence", or "Confluence CQL query". Handles Wiki Markup conversion, Mermaid/PlantUML diagrams, image handling, large document uploads without size limits, and Git-to-Confluence sync with mark CLI.
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
uv run {base_dir}/scripts/upload_confluence.py document.md --id PAGE_ID

# For structural modifications (adding table rows, etc.):
uv run {base_dir}/scripts/add_table_row.py PAGE_ID --table-heading "..." --after-row-containing "..." --cells "..." "..." "..."
```

**DO NOT CREATE TEMPORARY ANALYSIS SCRIPTS** - Use existing `analyze_page.py` tool

```bash
# DON'T create one-off scripts like:
/tmp/analyze_gemini_page.py
/tmp/show_all_blocks.py

# DO use the existing tool:
uv run {base_dir}/scripts/analyze_page.py PAGE_ID
uv run {base_dir}/scripts/analyze_page.py PAGE_ID --type codeBlock
```

**Performance Reality**:
- MCP roundtrip for structural changes: ~13 minutes (91% is AI processing delays)
- Python REST API direct: ~1.2 seconds (650x faster)
- Bottleneck: AI tool invocation intervals, NOT MCP network I/O

MCP tools are fine for **reading** pages and **simple text edits** but **fail for structural modifications due to AI processing overhead**.

## Quick Decision Matrix

**NOTE**: All `.py` scripts below must be run with `uv run scripts/SCRIPT_NAME.py`

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

### Quick Selection Guide

**I want to...**
- 🔍 Understand page structure (what components are on the page) → Use **`analyze_page.py`** first
- ✏️ Fix typos or improve wording → Use **Method 6** (preserves macros)
- 📋 Add a row to a table → Use **`add_table_row.py`**
- 📝 Add an item to a bullet list → Use **`add_list_item.py`**
- 💡 Add a warning/info box → Use **`add_panel.py`**
- 📑 Create a new section → Use **`insert_section.py`**
- 💻 Add a line to a code block → Use **`add_to_codeblock.py`**
- 💬 Add a quote/citation → Use **`add_blockquote.py`**
- ➖ Add a divider line → Use **`add_rule.py`**
- 🖼️ Add an image → Use **`add_media.py`** (single) or **`add_media_group.py`** (multiple)
- 🏷️ Add a status badge (TODO/DONE) → Use **`add_status.py`**
- 👤 Mention a user (@name) → Use **`add_mention.py`**
- 📅 Add a date → Use **`add_date.py`**
- 😀 Add an emoji → Use **`add_emoji.py`**
- 🔗 Add a link card → Use **`add_inline_card.py`**
- 📤 Upload a complete document → Use **`upload_confluence.py`**
- 📥 Download for editing → Use **`download_confluence.py`**
- 🔍 Just read/search → Use **MCP tools** directly

## Core Workflows

### 🆕 Method 6: Intelligent Roundtrip Editing (Recommended for Editing Existing Pages)

**Revolutionary Feature**: Edit existing Confluence pages while preserving all macros (expand panels, status badges, page properties, etc.) and allow Claude to intelligently edit text content.

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

1. **Read Page** (via MCP)
   ```
   📖 Reading page 123456...
   ```

2. **Detect Macros** (automatic)
   ```
   🔍 Found 3 macros with editable content:
      - expand: "Advanced Configuration" (127 chars)
      - panel: "Important Notes" (89 chars)
   ```

3. **Choose Mode** (interactive prompt)
   ```
   ⚙️  Choose editing mode:
   [1] Safe Mode (default) - Edit text outside macros (recommended)
   [2] Advanced Mode - Edit macro body content too
   ```

4. **Automatic Backup**
   ```
   💾 Creating backup...
      Backup saved: .confluence_backups/123456/2026-01-23T19-25-02.json
   ```

5. **Claude Editing**
   ```
   🤖 Claude editing based on your instruction...
   🔄 Found 5 text changes
   ```

6. **Write Back to Confluence**
   ```
   📝 Writing changes back to Confluence...
   ✅ Page updated successfully!
   ```

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

#### Backup and Restore

**Automatic Backup** (before each edit):
```
.confluence_backups/
  └── 123456/                    # Page ID
      ├── 2026-01-23T19-25-02.json
      ├── 2026-01-23T18-30-15.json
      └── ...                    # Keeps last 10 backups
```

**Manual Restore** (if needed):
```
"Rollback Confluence page 123456 to previous backup"
```
System will list available backups for you to choose which version to restore.

**Automatic Restore** (on write failure):
If Confluence update fails, system automatically restores from backup, no manual handling needed.

#### Technical Details (for reference)

- Uses ADF (Atlassian Document Format) JSON diff/patch technology
- Macro nodes completely untouched, structure guaranteed unchanged
- Uses word overlap heuristic (30%) to identify text changes
- OAuth authentication (no need to manage API tokens)
- Core implementation: `scripts/mcp_json_diff_roundtrip.py`

### Upload Markdown to Confluence

**CRITICAL**: Use absolute path to script WITHOUT `cd` command.

```bash
# Update existing page
uv run {base_dir}/scripts/upload_confluence.py document.md --id 780369923

# Create new page
uv run {base_dir}/scripts/upload_confluence.py document.md --space DEV --parent-id 123456

# Preview first (recommended)
uv run {base_dir}/scripts/upload_confluence.py document.md --id 780369923 --dry-run
```

### Structural Modifications (Fast Method) 🚀

**Purpose**: Directly modify table structures (add rows, modify layout, etc.), avoiding MCP's AI processing delays.

**Performance Comparison**:
- MCP Roundtrip via Claude: ~13 minutes (AI processing delays)
- Python REST API Direct: **~1.2 seconds** (650x speedup)

**Why So Fast?**
- Avoids AI tool invocation delays (accounts for 91% of time)
- Direct REST API, no intermediate files
- Pure Python operation, no token generation overhead

#### Add Table Row

```bash
# Basic usage
uv run {base_dir}/scripts/add_table_row.py PAGE_ID \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Location" "Access" "Privilege" "Auth" "Issues"

# Real example
uv run {base_dir}/scripts/add_table_row.py 2117534137 \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Elasticsearch Cluster - Production" "@Data Engineering Team" "Read-Only" "API Key + IP Whitelist" "Daily snapshots to S3"

# Dry run preview (recommended to run first)
uv run {base_dir}/scripts/add_table_row.py 2117534137 \
  --table-heading "Access Control Inventory" \
  --after-row-containing "GitHub" \
  --cells "Test" "Test" "Test" "Test" "Test" \
  --dry-run
```

**Parameter Description**:
- `PAGE_ID`: Confluence page ID (from URL)
- `--table-heading`: Heading text before the table
- `--after-row-containing`: Text in first cell of row to insert after
- `--cells`: New row's cell contents (space-separated)
- `--dry-run`: Preview mode, doesn't actually update

**Prerequisites**:
- Environment must be configured: `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`
- Uses ADF (Atlassian Document Format) operations
- Direct REST API v2, no MCP dependency

**Applicable Scenarios**:
- ✅ Add table rows
- ✅ Batch structural modifications
- ✅ Automation scripts
- ✅ Operations requiring fast execution

**Not Applicable**:
- ❌ Text editing (use Method 6 - mcp_json_diff_roundtrip.py)
- ❌ Editing that requires preserving macros (use Method 6)

#### Add List Item

```bash
# Add to bullet list
uv run {base_dir}/scripts/add_list_item.py PAGE_ID \
  --after-heading "Requirements" \
  --item "New security requirement" \
  --position end

# Add to numbered list at start
uv run {base_dir}/scripts/add_list_item.py PAGE_ID \
  --after-heading "Steps" \
  --item "Initial setup phase" \
  --position start \
  --list-type numbered
```

**Parameters**:
- `--after-heading`: Heading text before the list
- `--item`: Text content for the new list item
- `--position`: `start` or `end` (default: end)
- `--list-type`: `bullet` or `numbered` (default: bullet)

#### Add Panel

```bash
# Add warning panel
uv run {base_dir}/scripts/add_panel.py PAGE_ID \
  --after-heading "Overview" \
  --panel-type warning \
  --content "Important: Review access controls quarterly"

# Add info panel
uv run {base_dir}/scripts/add_panel.py PAGE_ID \
  --after-heading "Setup" \
  --panel-type info \
  --content "This feature requires admin privileges"
```

**Parameters**:
- `--after-heading`: Heading to insert panel after
- `--panel-type`: `info`, `warning`, `note`, or `success`
- `--content`: Text content for the panel

**Panel Types**:
- `info` (blue) - General information
- `warning` (yellow) - Important warnings
- `note` (gray) - Side notes
- `success` (green) - Success messages

#### Insert Section

```bash
# Insert new section with content
uv run {base_dir}/scripts/insert_section.py PAGE_ID \
  --after-heading "Overview" \
  --new-heading "Security Considerations" \
  --level 2 \
  --content "This section describes security measures..."

# Insert at end of page
uv run {base_dir}/scripts/insert_section.py PAGE_ID \
  --new-heading "Appendix" \
  --level 2 \
  --content "Additional reference materials..."
```

**Parameters**:
- `--after-heading`: Heading to insert after (omit to insert at end)
- `--new-heading`: Text for the new heading
- `--level`: Heading level 1-6 (default: 2)
- `--content`: Paragraph text (optional)

#### Add Line to Code Block

```bash
# Add install command after existing line
uv run {base_dir}/scripts/add_to_codeblock.py PAGE_ID \
  --search-text "brew install uv" \
  --add-line "brew install node" \
  --position after

# Add command before existing line
uv run {base_dir}/scripts/add_to_codeblock.py PAGE_ID \
  --search-text "npm install" \
  --add-line "npm install --save-dev jest" \
  --position before
```

**Parameters**:
- `--search-text`: Text to search for in code blocks
- `--add-line`: Line to add
- `--position`: `before` or `after` (default: after)

**Use Cases**:
- Add installation commands to setup scripts
- Insert additional configuration lines
- Add dependencies to package manager commands

### Download Confluence to Markdown

```bash
# Single page
uv run {base_dir}/scripts/download_confluence.py 123456789

# With child pages
uv run {base_dir}/scripts/download_confluence.py --download-children 123456789

# Custom output directory
uv run {base_dir}/scripts/download_confluence.py --output-dir ./docs 123456789
```

### Convert Markdown to Wiki Markup

```bash
uv run {base_dir}/scripts/convert_markdown_to_wiki.py input.md output.wiki
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
   uv run {base_dir}/scripts/upload_confluence.py document.md --id PAGE_ID
   ```

### Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Creating temp scripts: `/tmp/analyze_*.py` | Use existing: `analyze_page.py` |
| Using raw XML: `<ac:image>...` | Use markdown: `![alt](path.png)` |
| Using MCP for uploads | Use `upload_confluence.py` |
| Forgetting to convert diagrams | Pre-convert Mermaid/PlantUML to PNG/SVG |

## Checklists

### Upload Checklist

```
Upload Progress:
- [ ] Diagrams converted to PNG/SVG (if Mermaid/PlantUML present)
- [ ] All images use markdown syntax: ![alt](path)
- [ ] No raw Confluence XML in markdown
- [ ] All image files verified to exist
- [ ] Dry-run tested: `--dry-run`
- [ ] Upload executed with script (NOT MCP)
- [ ] Page URL verified accessible
```

### Download Checklist

```
Download Progress:
- [ ] Page ID obtained from Confluence URL
- [ ] Credentials configured in .env file
- [ ] Output directory specified
- [ ] --download-children flag set (if hierarchy needed)
- [ ] Download completed successfully
- [ ] Attachments downloaded to {Page}_attachments/
- [ ] Frontmatter contains correct metadata
```

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `confluence_search` | Search using CQL or text |
| `confluence_get_page` | Retrieve page by ID or title |
| `confluence_create_page` | Create new page (⚠️ size limited) |
| `confluence_update_page` | Update existing page (⚠️ size limited) |
| `confluence_delete_page` | Delete page |
| `confluence_get_page_children` | Get child pages |
| `confluence_add_label` | Add label to page |
| `confluence_get_labels` | Get page labels |
| `confluence_add_comment` | Add comment to page |
| `confluence_get_comments` | Get page comments |

## Utility Scripts

**IMPORTANT**: All Python scripts must be run with `uv run` to ensure correct dependency management.

**ADF Coverage**: 15 structural modification tools covering 16/19 ADF node types (84% coverage, ~98% practical coverage)
- ✅ All common block elements (table, list, code, panel, heading, quote, rule, images)
- ✅ All common inline elements (status, mention, date, emoji, card)
- ❌ Only missing: multiBodiedExtension (tabs macro), mediaInline (rare)

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/confluence_adf_utils.py` | **Shared Utils Library** - ADF operation core functions (auth, read, write, find nodes) | Import by other scripts |
| `scripts/analyze_page.py` | 🔍 **Analyze Page Structure** - Show all components (tables, lists, code blocks, panels, headings) and suggest which tool to use | `uv run scripts/analyze_page.py PAGE_ID [--type codeBlock\|table\|bulletList\|...]` |
| `scripts/add_table_row.py` | ⚡ **Fast Add Table Row** (~1.2s vs MCP 13min) | `uv run scripts/add_table_row.py PAGE_ID --table-heading "..." --after-row-containing "..." --cells "..." "..."` |
| `scripts/add_list_item.py` | 📋 Add bullet/numbered list items | `uv run scripts/add_list_item.py PAGE_ID --after-heading "..." --item "..." [--position start\|end]` |
| `scripts/add_panel.py` | 💡 Add info/warning/note/success panels | `uv run scripts/add_panel.py PAGE_ID --after-heading "..." --panel-type info --content "..."` |
| `scripts/insert_section.py` | 📑 Insert new section (heading + content) | `uv run scripts/insert_section.py PAGE_ID --new-heading "..." --level 2 [--after-heading "..."]` |
| `scripts/add_to_codeblock.py` | 💻 Add line to code block | `uv run scripts/add_to_codeblock.py PAGE_ID --search-text "..." --add-line "..." [--position after]` |
| `scripts/add_blockquote.py` | 💬 Add blockquote (citation) | `uv run scripts/add_blockquote.py PAGE_ID --quote "..." [--after-heading "..."\|--at-end]` |
| `scripts/add_rule.py` | ➖ Add horizontal rule (divider) | `uv run scripts/add_rule.py PAGE_ID [--after-heading "..."\|--at-end]` |
| `scripts/add_media.py` | 🖼️ Add image (uploads and embeds) | `uv run scripts/add_media.py PAGE_ID --image-path "./img.png" [--after-heading "..."\|--at-end] [--width 500]` |
| `scripts/add_status.py` | 🏷️ Add status label (TODO/DONE/etc.) | `uv run scripts/add_status.py PAGE_ID --search-text "..." --status "TODO" [--color blue]` |
| `scripts/add_mention.py` | 👤 Add @mention (notify user) | `uv run scripts/add_mention.py PAGE_ID --search-text "..." --user-id "557058..." [--display-name "John"]` |
| `scripts/add_date.py` | 📅 Add date (inline timestamp) | `uv run scripts/add_date.py PAGE_ID --search-text "..." --date "2026-03-15"` |
| `scripts/add_emoji.py` | 😀 Add emoji | `uv run scripts/add_emoji.py PAGE_ID --search-text "..." --emoji ":smile:"` |
| `scripts/add_media_group.py` | 🖼️🖼️ Add image group (multiple images) | `uv run scripts/add_media_group.py PAGE_ID --images "./img1.png" "./img2.png" [--after-heading "..."\|--at-end]` |
| `scripts/add_nested_expand.py` | 📂 Add nested expand panel | `uv run scripts/add_nested_expand.py PAGE_ID --parent-expand "Details" --title "More" --content "..."` |
| `scripts/add_inline_card.py` | 🔗 Add inline card (URL preview) | `uv run scripts/add_inline_card.py PAGE_ID --search-text "..." --url "https://..."` |
| `scripts/upload_confluence.py` | 📝 Upload Markdown (supports large files, images) | `uv run scripts/upload_confluence.py doc.md --id PAGE_ID` |
| `scripts/download_confluence.py` | 📥 Download as Markdown (with attachments) | `uv run scripts/download_confluence.py PAGE_ID` |
| `scripts/convert_markdown_to_wiki.py` | 🔄 Markdown ↔ Wiki Markup conversion | `uv run scripts/convert_markdown_to_wiki.py input.md output.wiki` |
| `scripts/mcp_json_diff_roundtrip.py` | ✏️ Intelligent text editing (preserves macros) | Used by Method 6, see above |

## Prerequisites

**Required:**
- **`uv` package manager** - All scripts use PEP 723 inline metadata, must run with `uv run`
- Atlassian MCP Server (`mcp__atlassian`) with Confluence credentials (for MCP tools)
- Environment variables: `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN` (for REST API scripts)

**Optional:**
- `mark` CLI: Git-to-Confluence sync (`brew install kovetskiy/mark/mark`)
- Mermaid CLI: Diagram rendering (`npm install -g @mermaid-js/mermaid-cli`)

## References

- [Wiki Markup Guide](references/wiki_markup_guide.md) - Complete syntax reference
- [CQL Reference](references/cql_reference.md) - Confluence Query Language syntax
- [Troubleshooting](references/troubleshooting.md) - Common errors and fixes

## When NOT to Use Scripts

- Simple page reads → Use MCP directly
- No images/diagrams, small content (<10KB) → MCP may work
- Jira issues → Use Jira-specific tools
