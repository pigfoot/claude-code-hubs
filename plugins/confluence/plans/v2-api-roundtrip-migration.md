# Plan: Migrate download/upload roundtrip to v2 API (ADF-native)

Status: **Implementation complete** (38/38 tasks done)

> **OpenSpec change**: `v2-api-roundtrip` (spec-driven, all artifacts complete)
>
> - Proposal: `openspec/changes/v2-api-roundtrip/proposal.md`
> - Design: `openspec/changes/v2-api-roundtrip/design.md`
> - Specs: `openspec/changes/v2-api-roundtrip/specs/adf-markdown-conversion/spec.md`
>          `openspec/changes/v2-api-roundtrip/specs/confluence-roundtrip/spec.md`
> - Tasks: `openspec/changes/v2-api-roundtrip/tasks.md` (38/38 tasks complete)
>
> This file captures the original research findings. For implementation details,
> refer to the OpenSpec artifacts above.

## Problem Statement

The current `download_confluence.py` / `upload_confluence.py` markdown roundtrip
destroys page structures because it uses the v1 API (Storage format) and goes through
lossy markdown conversion. Specifically, these elements are lost:

| Element | Storage format representation | ADF representation | Download handler | Upload handler |
|---------|-------------------------------|-------------------|-----------------|----------------|
| expand | `ac:structured-macro ac:name="expand"` | `{"type":"expand", "attrs":{"title":"..."}}` | None → dropped by markdownify | None |
| emoji | `ac:emoticon ac:emoji-shortname=":name:"` | `{"type":"emoji", "attrs":{"shortName":":name:"}}` | None → dropped | None |
| mention | `ac:link > ri:user ri:account-id="..."` | `{"type":"mention", "attrs":{"id":"...", "text":"@Name"}}` | None → dropped | None |
| inlineCard | **Not in storage format at all** | `{"type":"inlineCard", "attrs":{"url":"..."}}` | Impossible via v1 API | None |
| panel (new ADF) | `ac:adf-extension > ac:adf-node type="panel"` | `{"type":"panel", "attrs":{"panelType":"note"}}` | None (only old `ac:name="note"` handled) | None |
| panel (old) | `ac:structured-macro ac:name="info"` | `{"type":"panel", "attrs":{"panelType":"info"}}` | Converted to `> **INFO**: ...` | Becomes `<blockquote>` (loses panel styling) |

### Root cause

```
Current flow (v1 API + Storage format):

  v1 API ──► Storage XML/HTML ──► BeautifulSoup ──► markdownify ──► .md
  .md ──► mistune ──► Storage XML/HTML ──► v1 API

  Problems:
  1. Storage format lacks some ADF nodes (inlineCard not present at all)
  2. markdownify doesn't know Confluence XML (ac:emoticon, ac:link>ri:user, etc.)
  3. Expand macros have no handler → silently dropped
  4. New ADF panels use ac:adf-extension wrapper → not recognized
  5. Upload has no way to recreate these elements from plain markdown
```

### Evidence (from page 2321482360 analysis)

Storage format inspection revealed:

- 4 `ac:structured-macro ac:name="expand"` — not handled by download
- 2 `ac:emoticon` — not handled by download
- 2 `ac:link > ri:user` — not handled by download
- 1 `ac:adf-extension > ac:adf-node type="panel"` — not handled by download
- 0 inlineCard in storage — only exists in ADF format

ADF format (via v2 API) has all elements as clean JSON nodes:

- `{"type":"expand", "attrs":{"title":"..."}}`
- `{"type":"emoji", "attrs":{"shortName":":ms_teams:"}}`
- `{"type":"mention", "attrs":{"id":"622a2c...", "text":"@Michael Fu"}}`
- `{"type":"inlineCard", "attrs":{"url":"https://..."}}`
- `{"type":"panel", "attrs":{"panelType":"note"}}`

## Proposed Solution: v2 API (ADF-native) roundtrip

### Architecture

```
New flow (v2 API + ADF format):

  v2 API ──► ADF JSON ──► custom ADF walker ──► Markdown with markers
  Markdown with markers ──► mistune + marker parser ──► ADF JSON ──► v2 API

  Key differences:
  1. Read ADF directly (all node types visible)
  2. Custom ADF-to-Markdown walker (not markdownify)
  3. Preserve non-markdown elements using HTML comment markers
  4. Custom Markdown-to-ADF builder (not just Storage HTML)
  5. Write ADF directly via v2 API
```

### Custom markdown syntax for Confluence elements

```markdown
<!-- These are round-trippable markers embedded in the downloaded markdown -->

Expand panels:
<!-- EXPAND: "Panel Title" -->
Content inside the expand panel...
<!-- /EXPAND -->

Emojis (inline):
:emoji_shortname:
e.g., :ms_teams: or :confluence:

Mentions (inline):
<!-- MENTION: accountId "Display Name" -->
e.g., <!-- MENTION: 622a2c7115521d00726edac5 "Michael Fu" -->

Inline cards (inline):
<!-- CARD: url -->
e.g., <!-- CARD: https://trendmicro.atlassian.net/wiki/spaces/.../pages/123456 -->

Panels:
<!-- PANEL: panelType -->
Content inside the panel...
<!-- /PANEL -->
e.g., <!-- PANEL: note -->
Don't forget to restart Claude Code.
<!-- /PANEL -->

Breakout marks (metadata on expands):
Stored as attributes in EXPAND marker:
<!-- EXPAND: "Title" breakout="wide" width="1800" -->
```

### Existing infrastructure to reuse

The codebase already has v2 API read/write in `confluence_adf_utils.py`:

- `get_page_adf(base_url, auth, page_id)` — reads ADF via v2 API
- `update_page_adf(base_url, auth, page_id, title, body, version)` — writes ADF via v2 API

### Implementation plan

#### Phase 1: ADF-to-Markdown converter (new file: `adf_to_markdown.py`)

Custom ADF tree walker that handles every node type:

| ADF node type | Markdown output |
|---------------|----------------|
| `doc` | (root container) |
| `paragraph` | Plain text + `\n\n` |
| `heading` | `#` / `##` / `###` etc. |
| `text` | Plain text (with marks: bold, italic, code, link) |
| `bulletList` / `orderedList` | `-` / `1.` items |
| `listItem` | (container for list content) |
| `codeBlock` | ` ```lang\n...\n``` ` |
| `blockquote` | `>` prefixed lines |
| `table` | Markdown table `\| ... \|` |
| `rule` | `---` |
| `mediaSingle` / `media` | `![alt](filename)` |
| `expand` | `<!-- EXPAND: "title" -->\n...\n<!-- /EXPAND -->` |
| `emoji` | `:shortname:` |
| `mention` | `<!-- MENTION: id "text" -->` |
| `inlineCard` | `<!-- CARD: url -->` |
| `panel` | `<!-- PANEL: type -->\n...\n<!-- /PANEL -->` |
| `hardBreak` | `\n` |
| `status` | `<!-- STATUS: text color -->` |
| `date` | `<!-- DATE: timestamp -->` |

Text marks handling:

- `strong` → `**text**`
- `em` → `*text*`
- `code` → `` `text` ``
- `link` → `[text](url)`
- `underline` → `<u>text</u>`
- `strike` → `~~text~~`

#### Phase 2: Markdown-to-ADF converter (new file: `markdown_to_adf.py`)

Extend mistune parser to recognize custom markers and produce ADF JSON:

1. Use mistune to parse standard markdown → AST
2. Add custom plugins/directives for:
   - `<!-- EXPAND: ... -->` blocks → `{"type": "expand", ...}`
   - `:emoji:` patterns → `{"type": "emoji", ...}`
   - `<!-- MENTION: ... -->` → `{"type": "mention", ...}`
   - `<!-- CARD: ... -->` → `{"type": "inlineCard", ...}`
   - `<!-- PANEL: ... -->` blocks → `{"type": "panel", ...}`
3. Build ADF JSON tree from parsed AST + custom markers

#### Phase 3: Update download/upload scripts

- `download_confluence.py`: Switch from v1 Storage to v2 ADF, use new `adf_to_markdown.py`
- `upload_confluence.py`: Switch from Storage renderer to ADF builder, use new `markdown_to_adf.py`
- Keep backward compatibility: detect old-style markdown (no markers) and handle gracefully

### Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| ADF schema changes | Pin to known ADF version, handle unknown nodes gracefully (pass through as comment) |
| Nested expands/panels | Recursive walker handles nesting naturally |
| Complex table structures (merged cells) | ADF tables have explicit colspan/rowspan attrs; preserve in markdown or use markers |
| Large pages (>100KB ADF) | Stream processing, no full tree in memory (unlikely to be an issue in practice) |
| Markdown editing breaks markers | Validate markers after edit, warn if malformed |

### Out of scope (for now)

- `multiBodiedExtension` (tabs macro) — rare, can add later
- `mediaInline` — rare, can add later
- Layout/section macros — complex, keep as-is via `<!-- ADF:type -->` pass-through markers
- Full ADF schema validation — trust Confluence's own validation

### Files created/modified

New files:

- `plugins/confluence/skills/confluence/scripts/adf_to_markdown.py` — ADF→Markdown converter (~360 lines)
- `plugins/confluence/skills/confluence/scripts/markdown_to_adf.py` — Markdown→ADF converter (~450 lines)

Modified files:

- `plugins/confluence/skills/confluence/scripts/download_confluence.py` — added `download_page_v2()`, `--legacy` flag
- `plugins/confluence/skills/confluence/scripts/upload_confluence.py` — added ADF path with auto-detection, `--legacy` flag
- `plugins/confluence/skills/confluence/scripts/confluence_adf_utils.py` — added `create_page_adf()`
- `plugins/confluence/skills/confluence/scripts/add_panel.py` — fixed `\n` escape sequence bug

Reference files (updated):

- `plugins/confluence/skills/confluence/references/roundtrip-implementation-comparison.md` — Method 7 → Implemented
- `plugins/confluence/skills/confluence/SKILL.md` — documented v2 ADF download/upload and marker syntax

### Relation to existing methods

This migration effectively creates **Method 7**: a true ADF-native roundtrip that combines
the best of Method 1 (markdown editing) and Method 4 (structure preservation):

- Like Method 1: User edits markdown, Claude can help
- Like Method 4: All structures preserved via markers
- Unlike all previous methods: Uses ADF (v2 API) end-to-end, no Storage format involved
- Complementary to Method 6: Method 6 is for in-place text editing (no markdown step);
  this new method is for full document download/edit/upload workflows

## Remaining v1 API dependencies

Page content read/write is fully on v2 API. The following operations still use v1 API
and are intentionally kept as-is for now:

### Must stay on v1 (no v2 equivalent)

| Operation | v1 method | Used in | Reason |
|-----------|-----------|---------|--------|
| **Attachment upload** | `POST /rest/api/content/{id}/child/attachment` | `confluence_adf_utils.upload_attachment_file()`, `upload_confluence.py` | v2 API has no file upload endpoint — this is the only way to upload attachments |
| **Attachment download** | `GET {download_url}` | `download_confluence.py` | Download URL comes from v1 attachment listing response |

### Could migrate to v2 (low priority)

| Operation | v1 method | v2 alternative | Used in | Notes |
|-----------|-----------|---------------|---------|-------|
| **Attachment listing** | `confluence.get_attachments_from_content()` | `GET /api/v2/pages/{id}/attachments` | `download_confluence.py`, `upload_confluence.py` | v2 endpoint exists but untested; v1 works fine |
| **Child page listing** | `confluence.get_page_child_by_type()` | CQL query or v2 children endpoint | `download_confluence.py` (`--download-children`) | Would need pagination handling |
| **Space key ↔ ID** | `confluence.get_space()` | Parse from webui URL | `download_confluence.py`, `upload_confluence.py` | Already has URL-parsing fallback (line 255) |

### Intentionally kept on v1 (backward compat)

| Operation | v1 method | Used in | Reason |
|-----------|-----------|---------|--------|
| **Legacy page read** | `confluence.get_page_by_id(expand="body.storage")` | `download_confluence.py` (`--legacy`) | `--legacy` flag explicitly requests v1 Storage format |
| **Legacy page write** | `confluence.update_page()` / `create_page()` | `upload_confluence.py` (no markers) | Fallback for markdown without custom markers |
| **Legacy version check** | `confluence.get_page_by_id(expand="version")` | `upload_confluence.py` `upload_to_confluence()` | Only in Storage format upload path |

### Migration recommendation

**Don't migrate attachments** — v1 attachment upload is the only option and works reliably.
The `atlassian-python-api` library wraps this well. If Atlassian adds a v2 attachment upload
endpoint in the future, migration would be straightforward since `confluence_adf_utils.upload_attachment_file()`
already isolates the API call.

**Optional future work**: Migrate attachment listing to v2 (`GET /api/v2/pages/{id}/attachments`)
to reduce v1 library dependency. Not urgent since current approach works.

## Bug fixes included

### `add_panel.py` — `\n` not converted to newlines

**Fixed**: Line 57-68 in `add_panel.py`

- Before: `\n` escape sequences passed as literal text in single paragraph
- After: `\n` converted to actual newlines, split into multiple paragraph ADF nodes
- Commit: pending
