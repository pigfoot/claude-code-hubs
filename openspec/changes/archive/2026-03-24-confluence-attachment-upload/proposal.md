## Why

The Confluence skill's `add_media.py` and `add_media_group.py` scripts use
**attachment ID** (`att12345`) as the ADF media node's `attrs.id`, but
Confluence ADF requires the **Media Services UUID** (`fileId`). This causes
uploaded images to show "Preview unavailable" in the UI. Additionally, the
skill has no support for uploading non-image attachments (PDF, Word, Excel,
ZIP, etc.) to Confluence pages.

## What Changes

- **Bug fix**: `add_media.py` and `add_media_group.py` will use
  `response.results[0].extensions.fileId` (UUID) instead of
  `response.results[0].id` (attachment ID) for ADF media nodes
- **Bug fix**: ADF media nodes will use
  `response.results[0].extensions.collectionName` instead of empty
  string `""` for the `collection` attribute
- **New script**: `upload_attachment.py` — a general-purpose attachment
  upload script supporting any file type, with options to display as
  `mediaSingle`, `mediaGroup`, or attach-only (no page body modification)

### Verified by experiments on live Confluence page (2337112322)

| Approach | Result |
|----------|--------|
| ADF `attrs.id` = attachment ID (`att...`) | "Preview unavailable" |
| ADF `attrs.id` = fileId (UUID) | Image/file displays correctly |
| ADF `attrs.collection` = `"contentId-{pageId}"` | Required for correct rendering |
| Storage format `<ri:attachment ri:filename="...">` | Works (no change needed) |
| Non-image files (txt, pdf) via mediaGroup/mediaSingle | File cards display correctly |

## Capabilities

### New Capabilities

- `attachment-upload`: General-purpose file attachment upload to
  Confluence pages with optional inline display
  (mediaSingle/mediaGroup). Supports any file type, auto-detects
  content-type, and extracts `fileId` from v1 API response for correct
  ADF referencing.

### Modified Capabilities

- `confluence-roundtrip`: The media node handling in `add_media.py`
  and `add_media_group.py` needs to use correct `fileId` and
  `collectionName` from upload response — this is a bug fix to existing
  image upload behavior.

## Impact

- **Files modified**:
  - `plugins/confluence/skills/confluence/scripts/add_media.py` — fix
    `upload_attachment()` return value and `add_media()` node
    construction
  - `plugins/confluence/skills/confluence/scripts/add_media_group.py` — same fixes
- **Files created**:
  - `plugins/confluence/skills/confluence/scripts/upload_attachment.py` — new general-purpose upload script
- **Documentation**:
  - `plugins/confluence/skills/confluence/SKILL.md` — add upload_attachment.py to command reference
  - `plugins/confluence/README.md` — document new capability
- **Dependencies**: No new dependencies (uses same `requests` + `python-dotenv` stack)
- **API**: Uses existing v1 upload endpoint
  (`POST /wiki/rest/api/content/{id}/child/attachment`), extracting
  `fileId` from `extensions` in response (no additional API calls
  needed)
