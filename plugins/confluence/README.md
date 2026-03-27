# Confluence Document Manager

> Professional Confluence document management with **intelligent roundtrip editing** (preserves macros while Claude
> edits), markdown-first workflows, unlimited file sizes, and complete image support

## Design & Research

See [docs/plans/005-confluence-smart-routing/](../../docs/plans/005-confluence-smart-routing/) for:

- **[design.md](../../docs/plans/005-confluence-smart-routing/design.md)** -
  Smart routing architecture (MCP ↔ REST API)
- **[research.md](../../docs/plans/005-confluence-smart-routing/research.md)** - Performance testing & technical
  decisions

## 🚀 Quick Start

### 1. Install Plugin

```bash
claude plugin install --scope user confluence@pigfoot-marketplace
```

### 2. Authenticate with OAuth (One-Time Setup)

**First time only:** After installation, restart Claude Code and run:

```
/mcp
```

This opens an interactive menu:

1. **Select "atlassian"** from the list of MCP servers
2. **Choose "Authenticate"**
3. Browser window opens automatically
4. Sign in to your Atlassian account
5. Grant Confluence access permissions
6. Authentication completes and token is stored securely

**After authentication:** You can directly use Confluence features - no need to run `/mcp` again.

**Note:** If you have multiple MCP servers (e.g., context7, github), `/mcp` shows all of them and you select which one
to authenticate.

**What you can do with MCP (OAuth):**

- ✅ Search pages with CQL queries
- ✅ Read page content
- ✅ Small text updates (<10KB)
- ❌ Large document uploads (use API Token instead)
- ❌ Image attachments (use API Token instead)

### 3. (Optional) Set API Token for Full Features

For unlimited document sizes, image handling, and batch operations:

```bash
# Generate API Token at: https://id.atlassian.com/manage-profile/security/api-tokens
# Then configure (see Installation section for detailed options):

export CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
export CONFLUENCE_USER="your-email@company.com"
export CONFLUENCE_API_TOKEN="your-token-here"
```

### 4. Try It Out

**🧠 Intelligent Roundtrip Editing (Recommended):**

```
Edit Confluence page 123456 to fix typos and improve clarity
```

Claude will detect macros, ask your preference (safe/advanced mode), create backup, edit intelligently, and preserve all
macros!

**🔍 Search with CQL:**

```
Search Confluence for "project documentation"
```

**📝 Upload Markdown (for large files):**

```bash
uv run ~/.claude/plugins/.../scripts/upload_confluence.py document.md --id PAGE_ID
```

## ⚠️ Breaking Changes

### Environment Variable Renamed (v1.0.0+)

**`CONFLUENCE_USERNAME` is no longer supported. Use `CONFLUENCE_USER` instead.**

This change follows industry naming conventions (`DB_USER`, `MYSQL_USER`, `POSTGRES_USER`).

**Migration:**

```bash
# Old (deprecated):
export CONFLUENCE_USERNAME="your-email@company.com"

# New (required):
export CONFLUENCE_USER="your-email@company.com"
```

**Update your configuration:**

- `.env` files: Rename the variable
- Shell exports: Update your `~/.bashrc` or `~/.zshrc`
- CI/CD: Update environment variable settings

## ✨ Key Features

### 🔀 Smart Routing (Auto API Selection)

**Automatically selects the optimal API for each operation.** This plugin intelligently switches between MCP and REST
API based on:

- **Available credentials** - Uses REST API when token is configured, falls back to MCP otherwise
- **Operation type** - Reads vs writes vs Rovo AI search
- **Performance requirements** - REST API for fast writes (~1s), MCP for zero-config simplicity

**Why this is unique:**

- **25x faster writes** with REST API (~1s vs ~26s via MCP)
- **Zero-config fallback** to MCP when no token configured
- **Graceful degradation** - MCP session expires? Silently switches to REST API
- **Best of both worlds** - Easy OAuth setup + optional performance optimization

**What other tools lack:**

- Official Atlassian MCP: Only MCP (slow writes, 55-min token expiry)
- Third-party tools: Only REST API (requires manual setup, no OAuth option)
- This plugin: Combines both with automatic selection

### 🔗 Short URL Resolution

**Decode Confluence TinyUI short URLs locally.** Supports `/wiki/x/ZQGBfg` format via Base64 decoding:

- **Local processing** - No network calls needed (< 10ms)
- **Privacy-preserving** - URL decoded on your machine
- **All formats supported** - Short URLs, full URLs, direct page IDs

### 🎯 Smart Search with Quality Detection

**Detects when Rovo search results may be imprecise.** Calculates confidence score and suggests CQL alternative:

- **Confidence scoring** - Based on title matches and result count
- **Automatic suggestions** - When confidence < 60%, suggests CQL with preview query
- **Bilingual prompts** - Chinese + English for better UX
- **Best of both** - Use Rovo for semantic search, CQL for precision

**Example:**

```
ℹ️  Search precision may be low (confidence: 35%).
   Found 60 results, but only 1 title match(es) for 'API documentation'.

   Consider using CQL search for more precise results:
   title ~ "API documentation" OR text ~ "API documentation"
```

### 🧠 Intelligent Roundtrip Editing (Method 6)

**Edit existing Confluence pages with Claude while preserving macros.** Revolutionary JSON diff/patch approach that:

- **Preserves ALL macros** (expand, status, page properties, etc.) - structure never modified
- **Claude edits ALL text** - including content inside macro bodies
- **Safe Mode (default)**: Skip macro bodies, zero risk
- **Advanced Mode (opt-in)**: Edit macro bodies with interactive confirmation
- **Automatic backup & rollback**: Every edit is backed up, auto-rollback on failure
- **User control**: Interactive prompts let you decide risk/benefit trade-offs

**Why this matters:** Other tools force you to choose between losing macros or losing Claude's intelligence. Method 6
gives you both.

### 📝 Markdown-First Workflows

Write documentation in Markdown locally, publish to Confluence with full formatting preservation. Perfect for teams who
prefer Git-based workflows and want to maintain a single source of truth.

### 📦 Unlimited Document Sizes

Upload documents of any size without MCP's 10-20KB limitation. Uses Confluence REST API directly for reliable large file
handling.

### 📎 Attachment & Image Support

- Upload any file type (images, PDF, Word, Excel, ZIP, etc.) as Confluence attachments
- Display attachments inline as mediaSingle blocks or mediaGroup file cards
- Automatic Markdown image conversion (`![alt](path)` → Confluence attachments)
- Mermaid and PlantUML diagram support (convert to PNG/SVG first)
- Correct Media UUID (`fileId`) handling for ADF media nodes

### 📐 Page Formatting Control

- Default **full-width page layout** for all created/updated pages (override with `--width narrow`)
- Tables render with `data-layout="full-width"` by default (override with `--table-layout default`)
- **Column width ratios** via frontmatter `confluence.table.colwidths` for precise table proportions
- All formatting options configurable via CLI flags or YAML frontmatter

### ⬆️⬇️ Bidirectional Sync

- **New page upload**: Markdown → ADF (via mistune) → Confluence v2 REST API
- **Roundtrip editing**: Confluence v2 ADF → Method 6 (JSON diff/patch) → Confluence v2 ADF
- **Download (display)**: Confluence v2 ADF → readable Markdown for viewing
- Git integration via mark CLI for automated CI/CD publishing

### 🔍 Advanced Search (CQL)

Search across spaces, labels, and content using Confluence Query Language. Find pages by date, author, or custom fields
with precision.

### 🤖 CI/CD Ready

Integrate with GitHub Actions, GitLab CI, or any automation pipeline. Perfect for documentation-as-code workflows.

## 📖 Use Cases

### 1. Content Editor - Intelligent Page Updates

**Pain Point**: Existing Confluence pages have macros (expand panels, status badges, page properties) but need content
updates. Manual editing is tedious, and other tools lose macros during conversion.

**Solution**: Edit with Claude using intelligent roundtrip editing:

```python
# Ask Claude to edit a page
"Edit Confluence page 123456 to fix typos and improve clarity"
```

**What happens:**

1. 🔍 Detects macros on the page (expand, status, etc.)
2. 💬 Asks if you want to edit macro content (optional)
3. 💾 Creates automatic backup
4. 🤖 Claude edits the content intelligently
5. ✅ Macros fully preserved, text updated
6. 🔄 Auto-rollback if anything fails

**Two modes:**

- **Safe Mode** (default): Only edits text outside macros - zero risk
- **Advanced Mode**: Edits macro bodies with your confirmation + backup

✅ Preserves complex page structures
✅ Claude's intelligent editing
✅ Safety through backup/rollback
✅ Works with any page complexity

---

### 2. Documentation Team - Markdown Workflow

**Pain Point**: Team writes docs in Markdown but needs to publish to Confluence for stakeholders.

**Solution**: Write locally in your favorite editor, sync with one command:

```bash
uv run scripts/upload_confluence.py docs/api-guide.md --id 123456
```

✅ Preserves formatting
✅ Handles diagrams automatically
✅ Single source of truth

---

### 2. DevOps Team - CI/CD Publishing

**Pain Point**: Manual copy-paste of release notes to Confluence after every deployment.

**Solution**: Automated pipeline publishing:

```yaml
# .github/workflows/publish-docs.yml
- name: Publish to Confluence
  run: |
    uv run upload_confluence.py CHANGELOG.md --id ${{ secrets.CONFLUENCE_PAGE_ID }}
```

✅ Zero manual work
✅ Always up-to-date
✅ Automated publishing

---

### 3. Product Manager - Rich Content Reports

**Pain Point**: Complex reports with charts and screenshots exceed MCP size limits or require tedious manual image
uploads.

**Solution**: Embed images in Markdown, upload everything at once:

```markdown
# Markdown with images
![Q4 Results](./charts/q4-revenue.png)
![User Growth](./charts/user-growth.png)
```

```bash
# Single command uploads document + all images
uv run scripts/upload_confluence.py report.md --id 789012
```

✅ Batch image handling
✅ No size limits
✅ Professional formatting

---

### 4. Content Maintainer - Bulk Downloads

**Pain Point**: Need to migrate or backup dozens of Confluence pages to local storage.

**Solution**: Download page hierarchies with one command:

```bash
# Download page + all children + attachments
uv run scripts/download_confluence.py --download-children 456789
```

✅ Preserves page structure
✅ Includes attachments
✅ Renders as readable Markdown for viewing and backup

## 🔧 Core Workflows

### Intelligent Roundtrip Editing (Method 6)

**Edit existing pages with Claude while preserving macros.** Method 6 operates
**directly on ADF JSON** — fetching ADF from the v2 REST API, computing a JSON
diff/patch, and writing ADF back. Any Markdown shown to Claude is display-only
(for readability), not a conversion step.

```python
# Natural language editing - Claude understands your intent
"Edit Confluence page 123456 to improve the introduction section"
"Fix typos on page 789012"
"Update the API endpoint documentation on page 456789"
```

**How it works:**

1. **Detection Phase**

   ```
   📖 Reading page 123456...
   🔍 Found 3 macros with editable content:
      - expand: "Advanced Configuration" (127 chars)
      - panel: "Important Notes" (89 chars)
      - status: "In Progress"
   ```

2. **User Choice** (Interactive Prompt)

   ```
   ⚙️  Choose editing mode:

   [1] Safe Mode (default)
       • Edit text outside macros
       • Zero risk to macro structure
       • Recommended for most edits

   [2] Advanced Mode
       • Edit macro body content too
       • Automatic backup created
       • Auto-rollback on failure

   Your choice [1]: _
   ```

3. **Editing & Backup**

   ```
   💾 Backup created: .confluence_backups/123456/2026-01-23T10-30-15.json
   🤖 Claude editing...
   🔄 Computing diff...
   📝 Found 5 text changes
   ✅ Page updated successfully!
   ```

**Rollback if needed:**

```bash
# List available backups
uv run scripts/rollback_confluence.py --list 123456

# Restore from backup
uv run scripts/rollback_confluence.py --restore 123456 2026-01-23T10-30-15
```

**When to use each mode:**

| Scenario | Mode | Why |
|----------|------|-----|
| Fix typos | Safe | Fast, zero risk |
| Rewrite sections | Safe | Preserves structure |
| Edit expand panel content | Advanced | Requires confirmation |
| Edit info/warning boxes | Advanced | Requires confirmation |
| Major restructure | Safe first | Test, then Advanced if needed |

**Safety features:**

- ✅ Automatic backup before every edit
- ✅ Auto-rollback on write failure
- ✅ Macro structure never modified
- ✅ Version history preserved
- ✅ 10 backups kept per page (configurable)

---

### Upload Attachments (Any File Type)

```bash
# Auto mode (default) - images display inline, non-images as file cards
uv run scripts/upload_attachment.py PAGE_ID --file ./screenshot.png --at-end
uv run scripts/upload_attachment.py PAGE_ID --files ./photo.jpg ./report.pdf --at-end

# Attach only (no page body modification)
uv run scripts/upload_attachment.py PAGE_ID --file ./report.pdf --attach-only

# Force specific display mode
uv run scripts/upload_attachment.py PAGE_ID --file ./diagram.pdf --media-single --at-end
uv run scripts/upload_attachment.py PAGE_ID --files ./a.png ./b.png --media-group --at-end

# Dry run
uv run scripts/upload_attachment.py PAGE_ID --file ./doc.pdf --at-end --dry-run
```

Auto mode detects file type: images (png/jpg/gif/svg/webp) → inline
display, non-images (pdf/docx/pptx/zip/txt/...) → file cards. Override
with `--media-single` or `--media-group`.

---

### Upload Markdown to Confluence (New Page / Full Replacement)

Converts Markdown to ADF via `markdown_to_adf.py` (mistune) and uploads via v2 REST API.
Use this for **creating new pages** or **fully replacing** page content. For editing
existing pages while preserving macros, use **Method 6** instead.

**Update existing page:**

```bash
# Basic update
uv run scripts/upload_confluence.py document.md --id 780369923

# Preview before uploading (recommended)
uv run scripts/upload_confluence.py document.md --id 780369923 --dry-run

# Force re-upload all attachments
uv run scripts/upload_confluence.py document.md --id 780369923 --force-reupload
```

**Create new page:**

```bash
# Create in specific space
uv run scripts/upload_confluence.py document.md --space DEV --title "API Guide"

# Create as child page
uv run scripts/upload_confluence.py document.md --space DEV --parent-id 123456
```

**Page width and table formatting:**

```bash
# Full-width page (default) - tables and content use full browser width
uv run scripts/upload_confluence.py document.md --id 780369923

# Narrow page layout
uv run scripts/upload_confluence.py document.md --id 780369923 --width narrow

# Default table layout (narrower tables)
uv run scripts/upload_confluence.py document.md --id 780369923 --table-layout default
```

**Frontmatter for formatting control:**

```yaml
---
confluence:
  id: "780369923"
  width: full                        # full (default) or narrow
  table:
    layout: full-width               # full-width (default) or default
    colwidths: [12, 10, 40, 38]      # column width ratios
---
```

**Tips:**

- Images: Use Markdown syntax `![alt](path/to/image.png)` - script handles uploads automatically
- Mermaid/PlantUML: Convert to PNG/SVG first, then reference as images
- Frontmatter: Add YAML frontmatter for metadata (title, space, parent-id)
- Column widths: Applied to tables matching the colwidths array length; others auto-distribute

---

### Download Confluence to Markdown (Display Utility)

Downloads pages via v2 ADF API and converts to readable Markdown for **viewing purposes**.
For roundtrip editing of existing pages, use Method 6 (JSON diff) instead.

**Single page:**

```bash
# Download page by ID
uv run scripts/download_confluence.py 123456789

# Custom output directory
uv run scripts/download_confluence.py --output-dir ./docs 123456789
```

**Page hierarchy:**

```bash
# Download page + all children
uv run scripts/download_confluence.py --download-children 123456789
```

**Output:**

- Readable Markdown file with frontmatter (page ID, title, space)
- Attachments in `{PageTitle}_attachments/` directory
- ADF elements rendered as readable Markdown with custom markers

---

### Search and Query

**Using MCP (via Claude Code):**

```javascript
// Search by text
mcp__atlassian__confluence_search({
  query: 'text ~ "API documentation"',
  limit: 10
})

// Advanced CQL query
mcp__atlassian__confluence_search({
  query: 'space = "DEV" AND type = "page" AND created >= startOfYear()',
  limit: 20
})

// Get specific page
mcp__atlassian__confluence_get_page({
  page_id: "123456789"
})
```

**CQL Examples:**

- Find recent pages: `space = "DEV" AND created >= -7d`
- Search by label: `label = "api" AND space = "TECH"`
- Find by creator: `creator = "john.doe@company.com"`

See [CQL Reference](skills/references/cql_reference.md) for complete syntax.

---

### Convert Markdown ↔ Wiki Markup

**Markdown to Wiki:**

```bash
uv run scripts/convert_markdown_to_wiki.py input.md output.wiki
```

**Use cases:**

- Generate Wiki Markup for manual paste
- Debug conversion issues
- Preview formatting before upload

See [Wiki Markup Guide](skills/references/wiki_markup_guide.md) for syntax reference.

## 🛠️ Installation

### Prerequisites

**Required:**

- [uv](https://docs.astral.sh/uv/) - Python package runner (for scripts)
- [Claude Code](https://code.claude.com/) - CLI with MCP support
- Atlassian Cloud account with Confluence access

**Optional (for enhanced features):**

- [mark CLI](#optional-mark-cli) - Git-to-Confluence sync
- [Mermaid CLI](#optional-mermaid-cli) - Diagram rendering
- PlantUML - UML diagram generation

---

### Step 1: Install the Plugin

```bash
# Add marketplace (if not already added)
claude plugin marketplace add pigfoot/claude-code-hubs

# Install plugin
claude plugin install --scope user confluence@pigfoot-marketplace
```

**What gets configured automatically:**

- ✅ Atlassian Remote MCP Server (official endpoint)
- ✅ All Python scripts with inline dependencies
- ✅ Skill definitions and references

---

### Step 2: MCP Server Configuration

The plugin automatically configures the **Atlassian Remote MCP Server** (official cloud-based endpoint).

**Automatic configuration** (already done by plugin):

```json
{
  "atlassian": {
    "type": "http",
    "url": "https://mcp.atlassian.com/v1/mcp"
  }
}
```

**Benefits of Remote MCP Server:**

- ✅ No local installation required (no bunx/npx needed)
- ✅ Official Atlassian endpoint with OAuth 2.1
- ✅ Supports Confluence, Jira, and Compass
- ✅ Always up-to-date with latest features

**First use OAuth flow:**

- On first Confluence operation, Claude Code will prompt OAuth login
- Browser opens to Atlassian authorization page
- Grant permissions for Confluence access
- Session stored securely by Claude Code

**OAuth capabilities (via MCP):**

- ✅ Search pages with CQL
- ✅ Read page content
- ✅ Small text-only updates (<10KB)

---

### Step 3: Configure API Token (Recommended)

API Token enables full functionality including large file uploads and image handling.

**Additional capabilities:**

- ✅ Upload large documents (>10KB, no limits)
- ✅ Handle images and attachments
- ✅ Batch operations
- ✅ Offline/CI-CD workflows

**Why both OAuth and API Token?**
MCP uses cloud-based OAuth sessions that local Python scripts cannot access. For full functionality (large uploads,
images), you need API Token credentials.

**Setup:**

1. **Generate API Token:**
   - Visit <https://id.atlassian.com/manage-profile/security/api-tokens>
   - Click "Create API token"
   - Give it a name (e.g., "Claude Confluence Plugin")
   - Copy the token (save it securely - it won't be shown again)

2. **Set environment variables:**

   **Option A: Claude Code Settings (Recommended)**

   This method makes credentials available to all skills in Claude Code.

   **macOS / Linux / WSL / Git Bash:**

   ```bash
   # Replace with your actual values
   CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
   CONFLUENCE_USER="your-email@company.com"
   CONFLUENCE_API_TOKEN="your-token-here"

   # Check if jq is installed
   if ! command -v jq &> /dev/null; then
       echo "Error: jq is required but not installed."
       echo "Install with: brew install jq (Mac) or apt install jq (Linux)"
       exit 1
   fi

   [[ ! -r "${HOME}/.claude/settings.json" ]] && mkdir -p "${HOME}/.claude" && echo "{}" > "${HOME}/.claude/settings.json"

   jq "$(cat <<EOFSETTINGS
   .env.CONFLUENCE_URL="${CONFLUENCE_URL}"
     | .env.CONFLUENCE_USER="${CONFLUENCE_USER}"
     | .env.CONFLUENCE_API_TOKEN="${CONFLUENCE_API_TOKEN}"
   EOFSETTINGS
   )" ${HOME}/.claude/settings.json > /tmp/temp.json && mv -f /tmp/temp.json ${HOME}/.claude/settings.json

   echo "Configuration updated successfully"
   ```

   **Windows PowerShell:**

   ```powershell
   # Replace with your actual values
   $CONFLUENCE_URL = "https://your-company.atlassian.net/wiki"
   $CONFLUENCE_USER = "your-email@company.com"
   $CONFLUENCE_API_TOKEN = "your-token-here"

   # Settings.json setup
   $settingsPath = "$env:USERPROFILE\.claude\settings.json"
   if (-not (Test-Path $settingsPath)) {
       New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude" | Out-Null
       "{}" | Out-File -Encoding utf8 $settingsPath
   }

   $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

   # Ensure env object exists
   if (-not $settings.env) {
       $settings | Add-Member -Type NoteProperty -Name "env" -Value (New-Object PSObject) -Force
   }

   # Add or update environment variables (preserving existing ones)
   $settings.env | Add-Member -Type NoteProperty -Name "CONFLUENCE_URL" -Value $CONFLUENCE_URL -Force
   $settings.env | Add-Member -Type NoteProperty -Name "CONFLUENCE_USER" -Value $CONFLUENCE_USER -Force
   $settings.env | Add-Member -Type NoteProperty -Name "CONFLUENCE_API_TOKEN" -Value $CONFLUENCE_API_TOKEN -Force

   $settings | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $settingsPath

   Write-Host "Configuration updated successfully" -ForegroundColor Green
   ```

   **Option B: Shell Environment Variables**

   ```bash
   # Add to ~/.bashrc, ~/.zshrc, or ~/.profile
   export CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
   export CONFLUENCE_USER="your-email@company.com"
   export CONFLUENCE_API_TOKEN="your-token-here"
   ```

   **Option C: Project .env file**

   ```bash
   # Create .env file in your project directory
   CONFLUENCE_URL=https://your-company.atlassian.net/wiki
   CONFLUENCE_USER=your-email@company.com
   CONFLUENCE_API_TOKEN=your-token-here
   ```

3. **Verify configuration:**

   ```bash
   # Test with a dry-run
   uv run scripts/upload_confluence.py document.md --id PAGE_ID --dry-run
   ```

---

### Optional: mark CLI

**What it provides:**
Git-to-Confluence automatic synchronization for CI/CD workflows.

**Installation:**

**macOS:**

```bash
brew install kovetskiy/mark/mark
```

**Linux:**

```bash
# Download from GitHub releases
curl -LO https://github.com/kovetskiy/mark/releases/latest/download/mark-linux-amd64
chmod +x mark-linux-amd64
sudo mv mark-linux-amd64 /usr/local/bin/mark
```

**Windows:**

```powershell
# Download from GitHub releases
# Visit: https://github.com/kovetskiy/mark/releases
# Download mark-windows-amd64.exe
# Add to PATH manually
```

**Note:** mark CLI is not available in winget. Manual installation required.

**Without mark CLI:**
You can still use all upload/download/convert scripts. You'll just need to run uploads manually instead of automated
Git-based sync.

---

### Optional: Mermaid CLI

**What it provides:**
Converts Mermaid diagrams to PNG/SVG for Confluence upload.

**Installation:**

**macOS:**

```bash
brew install mermaid-cli
```

**Linux:**

```bash
# Using npm
npm install -g @mermaid-js/mermaid-cli

# Or using bun
bun install -g @mermaid-js/mermaid-cli

# Or using snap
sudo snap install mermaid-cli
```

**Windows:**

```powershell
# Using npm
npm install -g @mermaid-js/mermaid-cli

# Or using bun
bun install -g @mermaid-js/mermaid-cli

# Or using Scoop
scoop install mermaid-cli
```

**Usage:**

```bash
# Convert Mermaid to PNG
mmdc -i diagram.mmd -o diagram.png -b transparent
```

**Without Mermaid CLI:**
You can still upload documents with images. You just need to convert Mermaid diagrams manually (e.g., using online
tools) before uploading.

---

### Optional: PlantUML

**What it provides:**
Converts PlantUML diagrams to PNG/SVG for Confluence upload.

**Installation:**

**macOS:**

```bash
brew install plantuml
```

**Linux:**

```bash
sudo apt-get install plantuml
```

**Windows:**

```powershell
# Using Scoop
scoop install plantuml

# Or download JAR file from https://plantuml.com/download
```

**Usage:**

```bash
# Convert PlantUML to PNG
plantuml diagram.puml -tpng
```

**Without PlantUML:**
You can still upload documents. You just need to convert UML diagrams manually before uploading.

## 🤔 FAQ

### When should I use MCP vs Python scripts?

**Use MCP (via Claude Code) for:**

- Quick searches and queries
- Reading page content
- Small text-only updates (<10KB)
- Interactive exploration

**Use Python scripts for:**

- Large documents (>10KB)
- Documents with images/attachments
- Batch operations
- CI/CD pipelines
- Offline operations

### Why do I need both OAuth and API Token?

MCP's OAuth tokens are cloud-based sessions managed by Atlassian's server. Local Python scripts cannot access these
sessions. API tokens provide direct REST API access for full functionality.

### Can I use this without Git?

Yes! All core features (upload, download, convert, search) work without Git. Git integration via mark CLI is optional
for automated synchronization workflows.

### Does this work with Confluence Server (on-premise)?

This plugin is designed for **Atlassian Cloud** only. Confluence Server uses different APIs and authentication methods.

### How do I find my page ID?

**Method 1 - From URL:**

- Open page in browser
- Look at URL: `https://yourcompany.atlassian.net/wiki/spaces/DEV/pages/123456789/Page+Title`
- Page ID is `123456789`

**Method 2 - Via search:**

```javascript
mcp__atlassian__confluence_search({
  query: 'title ~ "Your Page Title"'
})
```

### What happens to existing images when I re-upload?

By default, existing attachments are skipped to save bandwidth. Use `--force-reupload` to replace all images.

## 🐛 Troubleshooting

### "Missing environment variables"

**Cause:** API token credentials not configured.

**Fix:**

```bash
# Verify variables are set
echo $CONFLUENCE_URL
echo $CONFLUENCE_USER
echo $CONFLUENCE_API_TOKEN

# Or check .env file exists
cat .env
```

### "Content too large" / MCP upload fails

**Cause:** Using MCP for large documents (>10-20KB).

**Fix:** Use upload script instead:

```bash
uv run scripts/upload_confluence.py document.md --id PAGE_ID
```

### "Authentication failed" for scripts

**Cause:** Invalid API token or credentials.

**Fix:**

1. Generate new API token: <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Verify `CONFLUENCE_USER` matches your Atlassian account email
3. Check `CONFLUENCE_URL` format: `https://yourcompany.atlassian.net/wiki` (no trailing slash)

### OAuth prompt appears repeatedly

**Cause:** MCP server not properly configured or session expired.

**Fix:**

1. Restart Claude Code
2. Verify `.mcp.json` exists in plugin directory
3. Complete OAuth flow in browser when prompted
4. Check Atlassian permissions at <https://id.atlassian.com/manage-profile/apps>

### Images not uploading

**Cause:** Image paths incorrect or files don't exist.

**Fix:**

1. Use relative paths from markdown file location
2. Verify image files exist:

   ```bash
   ls -la path/to/image.png
   ```

3. Use `--dry-run` to preview before upload:

   ```bash
   uv run scripts/upload_confluence.py doc.md --id PAGE_ID --dry-run
   ```

### Mermaid/PlantUML diagrams not showing

**Cause:** Diagrams not converted to images.

**Fix:**

```bash
# Convert Mermaid to PNG first
mmdc -i diagram.mmd -o diagram.png -b transparent

# Then reference in Markdown
# ![Architecture](./diagram.png)

# Then upload
uv run scripts/upload_confluence.py document.md --id PAGE_ID
```

## 📚 Reference Documentation

- **[CQL Reference](skills/references/cql_reference.md)** - Complete Confluence Query Language syntax and examples
- **[Wiki Markup Guide](skills/references/wiki_markup_guide.md)** - Confluence Wiki Markup syntax reference
- **[Troubleshooting Guide](skills/references/troubleshooting.md)** - Detailed error messages and solutions

## 🔗 External Resources

- [Atlassian Remote MCP
  Server](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/)
  - Official documentation
- [Atlassian MCP Server GitHub](https://github.com/atlassian/atlassian-mcp-server) - Remote MCP Server source code
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/) - API documentation
- [mark CLI](https://github.com/kovetskiy/mark) - Git-to-Confluence sync tool
- [Mermaid Documentation](https://mermaid.js.org/) - Diagram syntax and examples

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please see the main [repository](https://github.com/pigfoot/claude-code-hubs) for guidelines.

## 👨‍💻 For Developers

If you're developing skills or contributing to this plugin, see **[DEVELOPMENT.md](DEVELOPMENT.md)** for:

- Architecture decision: ADF v2 + Method 6 (JSON diff)
- Markdown conversion engine details (mistune 3.x for new page upload)
- Component role clarifications (upload vs download vs roundtrip)
- Output compatibility analysis
- Testing and validation procedures

---

**Version**: 0.1.0 | **Author**: pigfoot | **Marketplace**: pigfoot-marketplace
