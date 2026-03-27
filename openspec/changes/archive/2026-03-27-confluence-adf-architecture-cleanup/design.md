## Context

The Confluence plugin currently has two parallel content format paths:

1. **Storage Format (v1)**: `Markdown → mistune ConfluenceStorageRenderer → XHTML → v1 REST API`
2. **ADF (v2)**: `Markdown → mistune AST → markdown_to_adf.py → ADF JSON → v2 REST API`

For roundtrip editing, Method 6 (JSON diff) already operates directly on ADF JSON without Markdown intermediate. However, the documentation across 6+ files incorrectly attributes macro loss to Storage Format, when the actual cause is Markdown conversion. The legacy Storage Format download path (`--legacy`) uses markdownify which drops `ac:*` XML tags.

### Current architecture

```
New page:   Markdown → mistune → Storage HTML (v1) OR ADF JSON (v2, if markers detected)
Download:   v2 API ADF → adf_to_markdown.py → Markdown (default)
            v1 API Storage → markdownify → Markdown (--legacy, LOSSY)
Roundtrip:  v2 API GET ADF → Method 6 JSON diff → v2 API PUT ADF (correct, no Markdown)
Attachment: v1 API only
Page width: v1 API property endpoint only
```

## Goals / Non-Goals

**Goals:**

- Simplify to a single content format path (ADF v2) for all operations
- Fix documentation that incorrectly blames Storage Format for macro loss
- Clarify that macro loss is caused by Markdown intermediate conversion, not by any API format
- Clarify that Storage Format is NOT deprecated (v2 API supports `representation: storage`)
- Remove dead/misleading code paths (Storage Format upload, legacy download)
- Retain v1 API only for endpoints with no v2 equivalent (attachment upload, page width)

**Non-Goals:**

- Adding Storage Format direct XML roundtrip support (this is what Michael's plugin does — valid but not our approach)
- Replacing mistune with another parser (mistune 3.x is still appropriate for 2026)
- Changing Method 6 (JSON diff) — it already works correctly
- Removing `adf_to_markdown.py` — still useful as a display utility for Claude

## Decisions

### 1. Standardize on ADF v2 for all uploads

**Decision**: Remove `ConfluenceStorageRenderer` and v1 Storage Format upload path. All uploads go through `markdown_to_adf.py → create_page_adf() / update_page_adf()`.

**Rationale**: Having two upload paths creates confusion and maintenance burden. The ADF path is already the recommended path and supports all features. Upload priority: REST API v2 (ADF) if API token available, MCP (`contentFormat: "markdown"`) as fallback.

**Alternative considered**: Keep both paths. Rejected because the Storage Format path adds complexity without benefit — ADF upload is equally lossless and uses the modern API.

### 2. Remove legacy download path

**Decision**: Remove `--legacy` flag, `convert_storage_to_markdown()`, and the v1 Storage Format download logic from `download_confluence.py`.

**Rationale**: The legacy path goes through markdownify which drops `ac:*` tags (lossy). The v2 ADF download with custom markers is strictly better. No user should be using the legacy path.

**Alternative considered**: Keep but deprecate with warning. Rejected — no valid use case remains.

### 3. Reposition `markdown_to_adf.py` as upload-only tool

**Decision**: `markdown_to_adf.py` is for new page creation from Markdown only. It is NOT part of the roundtrip editing workflow.

**Rationale**: Roundtrip editing uses Method 6 (JSON diff on ADF), which never converts through Markdown. The `markdown_to_adf.py` module is only needed when starting from a Markdown file that doesn't exist in Confluence yet.

### 4. Reposition `adf_to_markdown.py` as display utility

**Decision**: `adf_to_markdown.py` converts ADF to readable Markdown for Claude to view/understand page content. It is NOT a roundtrip conversion step.

**Rationale**: In Method 6, this module is used to show Claude what's on the page (display purpose). The actual roundtrip data flow is ADF → ADF with JSON diff/patch. The Markdown output is never fed back into an ADF converter.

### 5. Fix documentation: macro loss attribution

**Decision**: Correct all documentation to attribute macro loss to Markdown intermediate conversion, not to Storage Format or API limitations.

**Key correction**: "Macros are lost when converting Storage/ADF → Markdown → Storage/ADF because Markdown cannot represent Confluence-specific elements. Direct Storage Format XML roundtrip and direct ADF JSON roundtrip (Method 6) are both lossless."

### 6. Fix documentation: Storage Format deprecation claims

**Decision**: Clarify that Storage Format is NOT deprecated. What's being deprecated:
- v1 API endpoint URLs (being replaced by v2 endpoints)
- Legacy Editor UI (by April 2026)

What's NOT being deprecated:
- Storage Format as a content representation (`representation: storage` in v2 API)

Evidence: [v2 API docs](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/), [v1 deprecation timeline](https://community.developer.atlassian.com/t/update-to-confluence-v1-api-deprecation-timeline/79687)

### 7. Keep v1 API for attachment upload and page width

**Decision**: Retain v1 REST API for:
- `POST /wiki/rest/api/content/{id}/child/attachment` (no v2 equivalent)
- `PUT /wiki/rest/api/content/{id}/property/content-appearance-*` (no v2 equivalent)

**Rationale**: These are the only two operations where v2 API has no equivalent endpoint.

## Risks / Trade-offs

- **[BREAKING: Storage Format upload removed]** → Users who depend on `--legacy` or Storage Format upload will need to switch. Mitigation: This was already the non-default path; document the change in release notes.
- **[markdownify/beautifulsoup4 may become unused]** → If legacy download is removed, these dependencies may be removable. Mitigation: Check if any other scripts use them before removing from dependencies.
- **[MCP size limit for fallback upload]** → MCP `contentFormat: "markdown"` has 10-20KB limit. Mitigation: Primary path is REST API v2 with ADF; MCP is fallback only for users without API token.
- **[Documentation is spread across 6+ files]** → Large surface area for corrections. Mitigation: Systematic audit using the findings from our doc review.
