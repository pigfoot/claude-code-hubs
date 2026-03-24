## Context

The Confluence skill uses two approaches for embedding images in pages:

1. **Storage Format** (`upload_confluence.py`) — references attachments
   by filename via `<ri:attachment ri:filename="...">`. Confluence
   resolves the file internally. This works correctly.
2. **ADF Format** (`add_media.py`, `add_media_group.py`) — references
   attachments by Media UUID in `media` node `attrs.id`. The current
   code incorrectly uses the attachment ID instead of the `fileId`,
   causing "Preview unavailable" errors.

Live experiments on page 2337112322 confirmed the root cause and fix.
Full details in
`docs/plans/007-confluence-attachment-upload/research.md`.

## Goals / Non-Goals

**Goals:**

- Fix `add_media.py` and `add_media_group.py` to use correct `fileId` and `collectionName`
- Add `upload_attachment.py` script supporting any file type with optional mediaSingle/mediaGroup display
- Follow existing script architecture patterns (same deps, same CLI style, same `confluence_adf_utils` usage)

**Non-Goals:**

- Changing `upload_confluence.py` (storage format works correctly)
- Adding v2 API upload support (no v2 upload endpoint exists yet)
- Supporting Confluence Server/Data Center (cloud only)
- Adding download support for non-image attachments (existing `download_confluence.py` already handles all types)
- Adding view-file macro support for inline PDF preview (L3 scope, future work)

## Decisions

### 1. Extract fileId from v1 upload response, not via separate v2 call

**Decision**: Read `response.results[0].extensions.fileId` directly from the v1 upload response.

**Alternatives considered**:

- Call `GET /wiki/api/v2/attachments/{id}` after upload to get
  `fileId` — adds latency, unnecessary since v1 already provides it
- Parse the attachment's download URL to extract the media UUID — fragile, URL format could change

**Rationale**: The v1 response `extensions` object already contains
both `fileId` and `collectionName`. Verified experimentally. One API
call is better than two.

### 2. Return a dict from upload_attachment() instead of just a string

**Decision**: Change `upload_attachment()` to return
`{"fileId": ..., "collectionName": ..., "attachmentId": ...}` instead
of just the attachment ID string.

**Alternatives considered**:

- Return only `fileId` — loses `collectionName` and `attachmentId` which callers may need
- Return the full API response — too much data, callers would need to know the response structure

**Rationale**: Returning a structured dict with exactly the fields
needed for ADF construction is the cleanest API. The `attachmentId` is
kept for potential REST API operations (delete, update).

### 3. New script `upload_attachment.py` rather than extending `add_media.py`

**Decision**: Create a new `upload_attachment.py` script with three
modes: `--attach-only`, `--media-single`, `--media-group`.

**Alternatives considered**:

- Extend `add_media.py` to support non-image files — name becomes misleading ("media" implies images)
- Rename `add_media.py` to `upload_attachment.py` — breaks existing users/docs referencing `add_media.py`

**Rationale**: A new general-purpose script with clear mode flags.
Existing `add_media.py` and `add_media_group.py` remain as focused,
simpler tools (still get the bug fix). The new script is the
recommended tool going forward.

### 4. Auto-detect content type from file extension

**Decision**: Use a content-type map (same pattern as
`upload_confluence.py` line 289-296) with fallback to
`application/octet-stream`.

**Rationale**: Consistent with existing code. Covers common types
(png, jpg, gif, svg, pdf, doc, docx, xls, xlsx, zip, txt). Unknown
extensions get a safe default.

### 5. Shared upload helper in confluence_adf_utils.py

**Decision**: Extract the corrected upload logic into a shared
function in `confluence_adf_utils.py` so all three scripts
(`add_media.py`, `add_media_group.py`, `upload_attachment.py`) use
the same implementation.

**Alternatives considered**:

- Fix each script independently — duplicated logic, risk of drift
- Create a new module — unnecessary for one function

**Rationale**: `confluence_adf_utils.py` is already the shared utility
module imported by all media scripts. Adding
`upload_attachment_file()` there centralizes the fix.

## Risks / Trade-offs

**[Risk] v1 API response format change** → The `extensions.fileId`
field is undocumented in official API docs (it's present but not
guaranteed). Mitigation: Fall back to v2 API call if
`extensions.fileId` is missing.

**[Risk] Existing pages with wrong media IDs** → Pages previously
created with `add_media.py` have broken images. Mitigation: This is a
bug fix, not a regression. No migration needed — users can re-upload
images.

**[Trade-off] Three scripts for attachment upload** → `add_media.py`,
`add_media_group.py`, and `upload_attachment.py` all upload files.
Mitigation: Document `upload_attachment.py` as the recommended
general-purpose tool. Keep the other two as focused shortcuts (they're
already in use and referenced in SKILL.md).
