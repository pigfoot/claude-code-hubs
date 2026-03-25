## Context

The confluence plugin has two content editing paths:

1. **ADF scripts** (28 tools like `add_panel.py`, `add_table_row.py`) — use v2 REST API, operate on ADF JSON directly via `confluence_adf_utils.py`. These preserve all page structures.

2. **Download/upload roundtrip** (`download_confluence.py` / `upload_confluence.py`) — uses v1 REST API, converts between Storage format (XML/HTML) and Markdown via `markdownify` (download) and `mistune` (upload). This path loses expand panels, emojis, mentions, inline cards, and new-style ADF panels.

The v2 API infrastructure already exists in `confluence_adf_utils.py` (`get_page_adf`, `update_page_adf`). The task is to build ADF ↔ Markdown converters and rewire download/upload to use them.

## Goals / Non-Goals

**Goals:**

- Preserve all Confluence-specific elements through the markdown roundtrip (expand, emoji, mention, inlineCard, panel, status, date)
- Use v2 REST API (ADF format) end-to-end for download/upload
- Keep downloaded markdown human-readable and editable
- Maintain backward compatibility with old-style markdown files (no markers)
- Reuse existing `confluence_adf_utils.py` for API operations

**Non-Goals:**

- Replacing Method 6 (MCP JSON Diff roundtrip) — it serves a different use case (in-place text editing)
- Supporting `multiBodiedExtension` (tabs macro) or `mediaInline` — rare, can add later
- Full ADF schema validation — trust Confluence's own validation on write
- Layout/section macros — complex nested structures, keep as pass-through markers

## Decisions

### 1. Marker format: HTML comments for block elements, inline syntax for inline elements

**Decision**: Use `<!-- EXPAND: "title" --> ... <!-- /EXPAND -->` for block elements and `:shortname:` / inline comments for inline elements.

**Alternatives considered**:
- **Custom markdown extensions** (e.g., `:::expand[title]`): Requires modifying mistune parser more deeply. Less readable.
- **YAML frontmatter metadata**: Can't represent inline positions. Loses spatial relationship.
- **JSON sidecar file**: Roundtrip requires keeping two files in sync. Error-prone.

**Rationale**: HTML comments are valid markdown, survive most editors and formatters, and can nest naturally. Inline elements like emoji use established `:shortname:` convention. Mentions and inline cards use inline HTML comments because they need to carry metadata (account IDs, URLs).

### 2. ADF-to-Markdown: Custom tree walker, not markdownify

**Decision**: Write a custom recursive ADF node walker in `adf_to_markdown.py`.

**Alternatives considered**:
- **Patch markdownify**: It operates on HTML, not ADF JSON. Would need ADF → HTML → markdownify, which is the current broken flow.
- **Use atlas-doc-parser**: Python package for ADF → Markdown, but doesn't support custom markers and may not handle all node types we need.

**Rationale**: ADF is a well-structured JSON tree. A custom walker is straightforward (~200 lines), gives full control over output for every node type, and avoids the HTML intermediary that causes information loss.

### 3. Markdown-to-ADF: Extend mistune with custom directives

**Decision**: Use mistune 3.x as the markdown parser, add pre-processing for custom markers, and build an `ADFRenderer` that outputs ADF JSON instead of HTML.

**Alternatives considered**:
- **marklassian (JS)**: Requires Node.js subprocess, adds dependency. Rejected per existing codebase convention (pure Python).
- **Write parser from scratch**: Unnecessary when mistune handles standard markdown well.
- **Regex-based marker extraction + mistune for the rest**: Fragile, hard to handle nested markers.

**Rationale**: mistune 3.x supports custom renderers. We replace `HTMLRenderer` with `ADFRenderer` that builds ADF JSON nodes. For custom markers (`<!-- EXPAND -->`, `:emoji:`, etc.), we pre-process the markdown to convert markers into tokens that mistune can handle, or post-process the AST.

### 4. API layer: Reuse confluence_adf_utils.py

**Decision**: Import `get_page_adf()` and `update_page_adf()` from `confluence_adf_utils.py`. No new API code.

**Rationale**: These functions already handle v2 API auth, URL construction, error reporting, and version management. They are battle-tested by the 28 existing ADF scripts.

### 5. Backward compatibility: Detect marker presence

**Decision**: When uploading, detect whether the markdown contains custom markers. If no markers found, fall back to the current Storage format renderer for backward compatibility.

**Rationale**: Users may have existing markdown files created with the old download script. These should still upload correctly. The presence of `<!-- EXPAND:`, `<!-- PANEL:`, or `<!-- CARD:` markers signals the new ADF path.

### 6. Text marks handling in ADF

**Decision**: Map ADF text marks to standard markdown inline formatting:

| ADF mark | Markdown |
|----------|----------|
| `strong` | `**text**` |
| `em` | `*text*` |
| `code` | `` `text` `` |
| `link` | `[text](url)` |
| `strike` | `~~text~~` |
| `underline` | `<u>text</u>` |
| `subsup` | `<sub>text</sub>` / `<sup>text</sup>` |

**Rationale**: Standard markdown formatting roundtrips cleanly through mistune. HTML tags for underline/subsup are necessary since markdown has no equivalent.

## Risks / Trade-offs

**[Markers broken during editing]** → Users or Claude might accidentally modify HTML comment markers, causing parse failures on upload. **Mitigation**: Validate markers after parsing; warn on malformed markers and fall back to treating them as plain text. Add clear documentation.

**[ADF schema evolution]** → Atlassian may add new node types. **Mitigation**: Unknown node types are serialized as `<!-- ADF:type {...attrs} -->` pass-through markers, preserving them without understanding them.

**[Complex table structures]** → ADF tables support merged cells (colspan/rowspan), which markdown tables cannot represent. **Mitigation**: Simple tables convert to markdown tables. Complex tables with merges use marker-wrapped raw JSON to preserve structure.

**[Nested expand/panel]** → Expands can contain panels, panels can contain expands. **Mitigation**: The recursive walker and HTML comment markers handle nesting naturally: `<!-- EXPAND --> <!-- PANEL --> ... <!-- /PANEL --> <!-- /EXPAND -->`.

**[Large pages]** → Pages with very large ADF trees could produce large markdown files. **Mitigation**: Not a practical concern — Confluence pages rarely exceed 1MB of ADF. Standard file I/O handles this fine.

## Migration Plan

1. ~~Create `adf_to_markdown.py` and `markdown_to_adf.py` as new standalone modules~~ ✅
2. ~~Add integration tests using real ADF samples from the test page~~ ✅
3. ~~Update `download_confluence.py` to use new ADF path (with `--legacy` flag to keep old behavior)~~ ✅
4. ~~Update `upload_confluence.py` to detect markers and use ADF path~~ ✅
5. ~~Update SKILL.md and reference docs~~ ✅
6. After validation, remove `--legacy` flag and make ADF path the default — **Decided to keep `--legacy` permanently for backward compat**

**Rollback**: The `--legacy` flag allows reverting to Storage format path. The v1 API code is not deleted, just no longer the default.

## v1 API Dependencies (post-migration)

Page content read/write is fully on v2 API. These operations remain on v1 intentionally:

### Must stay on v1

- **Attachment upload** (`POST /rest/api/content/{id}/child/attachment`) — no v2 upload endpoint exists
- **Attachment download** — download URLs come from v1 attachment response

### Kept on v1 by design

- **`--legacy` download path** — uses v1 Storage format for backward compat
- **No-markers upload path** — falls back to v1 Storage for old-style markdown

### Could migrate later (low priority)

- **Attachment listing** → `GET /api/v2/pages/{id}/attachments` exists but untested
- **Child page listing** → CQL or v2 children endpoint (currently uses `get_page_child_by_type`)
- **Space key ↔ ID** → already has URL-parsing fallback; `get_space()` used only when available

See `plugins/confluence/plans/v2-api-roundtrip-migration.md` § "Remaining v1 API dependencies" for full analysis.

## Resolved Questions

- **Text marks without markdown equivalent** (text color, background color): Dropped silently during ADF→MD. These are rare in practice and would clutter the markdown with markers.
- **Emoji `:shortname:` conflict with GitHub emoji**: Accepted. Confluence emoji shortnames are specific (`:ms_teams:`, `:confluence:`) and unlikely to collide with GitHub's set.
