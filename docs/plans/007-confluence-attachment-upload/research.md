# Confluence Attachment Upload - Research Notes

Technical investigation into Confluence attachment upload, media ID handling, and ADF media node requirements.

---

## Table of Contents

- [The Problem: attachment ID vs fileId](#the-problem-attachment-id-vs-fileid)
- [API Landscape: v1 vs v2](#api-landscape-v1-vs-v2)
- [Experiment 1: ID Flow Tracing](#experiment-1-id-flow-tracing)
- [Experiment 2: ADF mediaSingle with fileId vs attachment ID](#experiment-2-adf-mediasingle-with-fileid-vs-attachment-id)
- [Experiment 3: Visible Image with Correct fileId](#experiment-3-visible-image-with-correct-fileid)
- [Experiment 4: Storage Format (upload_confluence.py)](#experiment-4-storage-format-upload_confluencepy)
- [Experiment 5: Non-Image Files as mediaGroup/mediaSingle](#experiment-5-non-image-files-as-mediagroupmediasingle)
- [Key Findings Summary](#key-findings-summary)
- [ADF Media Node Reference](#adf-media-node-reference)

---

## The Problem: attachment ID vs fileId

The existing `add_media.py` and `add_media_group.py` scripts upload
images via the v1 REST API and use the **attachment ID** (e.g.,
`att12345`) as the ADF media node's `attrs.id`. However, Confluence
ADF requires the **Media Services UUID** (`fileId`), which is a
different value.

These are two distinct ID systems:

| ID Type | Format | Source | Used In |
|---------|--------|--------|---------|
| Attachment ID | `att12345678` | v1 upload response `.results[0].id` | REST API endpoints |
| fileId (Media UUID) | `e55a0e72-9f01-415e-887c-30870716cbe0` | v1 upload response `.results[0].extensions.fileId` | ADF `media` node `attrs.id` |

### The Bug in Existing Code

```python
# add_media.py line 62-67 (WRONG)
attachment_id = result["results"][0]["id"]  # "att12345" — this is NOT the media UUID
# ...
media_attrs = {
    "id": attachment_id,  # ← BUG: should be fileId
    "type": "file",
    "collection": "",     # ← BUG: should be collectionName
}
```

---

## API Landscape: v1 vs v2

### Upload: Only v1 API Supported

As of March 2026, there is **no POST/PUT endpoint in Confluence REST
API v2** for uploading attachments. This is tracked as
[CONFCLOUD-77196](https://jira.atlassian.com/browse/CONFCLOUD-77196)
(status: "Future Consideration", last updated 2026-02-26).

| Operation | v1 API | v2 API |
|-----------|--------|--------|
| **Upload attachment** | `POST /wiki/rest/api/content/{id}/child/attachment` | Not available |
| **Query attachment** | `GET /wiki/rest/api/content/{id}/child/attachment` | `GET /wiki/api/v2/attachments/{id}` |
| **Delete attachment** | N/A | `DELETE /wiki/api/v2/attachments/{id}` |
| **Get fileId** | Available in `extensions.fileId` of upload response | Available in `fileId` field |

### Key Discovery: v1 Response Already Contains fileId

The v1 upload response includes `fileId` in the `extensions` object. **No additional v2 API call is needed.**

```
POST /wiki/rest/api/content/{pageId}/child/attachment
Headers: X-Atlassian-Token: no-check
Body: multipart/form-data with file field

Response: results[0].extensions = {
    "fileId": "e55a0e72-9f01-415e-887c-30870716cbe0",   ← Media UUID
    "collectionName": "contentId-2337112322",             ← Collection ID
    "mediaType": "image/png",
    "fileSize": 424
}
```

---

## Experiment 1: ID Flow Tracing

**Date**: 2026-03-24
**Target Page**: `2337112322` (<https://trendmicro.atlassian.net/wiki/x/AoFNiw>)

### Procedure

1. Created a minimal 1x1 pixel PNG test image
2. Uploaded via v1 API
3. Queried via v2 API
4. Compared both IDs

### Results

```
v1 upload response:
  results[0].id           = "att2336359563"
  results[0].extensions   = {
    "fileId": "e55a0e72-9f01-415e-887c-30870716cbe0",
    "collectionName": "contentId-2337112322",
    "mediaType": "image/png",
    "fileSize": 69
  }

v2 GET /api/v2/attachments/att2336359563:
  id     = "att2336359563"
  fileId = "e55a0e72-9f01-415e-887c-30870716cbe0"

Conclusion: attachment ID ≠ fileId, both available from v1 response
```

---

## Experiment 2: ADF mediaSingle with fileId vs attachment ID

### Procedure

Added two `mediaSingle` nodes to the same page:

1. One with correct `fileId` as `attrs.id`
2. One with `attachment ID` as `attrs.id`

### Results

| Node | `attrs.id` value | UI Result |
|------|-------------------|-----------|
| mediaSingle #1 | `e55a0e72-9f01-415e-887c-30870716cbe0` (fileId) | No error (image too small to see — 1x1px) |
| mediaSingle #2 | `att2336359563` (attachment ID) | **"Preview unavailable"** error |

**Conclusion**: ADF media nodes **must** use `fileId` (UUID), not `attachment ID`.

---

## Experiment 3: Visible Image with Correct fileId

### Procedure

1. Created a visible 200x100 pixel test image (blue rectangle with colored boxes)
2. Uploaded via v1 API, extracted `fileId` from `extensions`
3. Created `mediaSingle` node with correct `fileId` and `collectionName`

### Results

Image displayed correctly inline on the Confluence page. Verified visually.

### Correct ADF Structure

```json
{
  "type": "mediaSingle",
  "attrs": { "layout": "center" },
  "content": [{
    "type": "media",
    "attrs": {
      "id": "e47d4d2e-b7e9-423c-9b08-9a499bd86f6a",
      "type": "file",
      "collection": "contentId-2337112322"
    }
  }]
}
```

---

## Experiment 4: Storage Format (upload_confluence.py)

### Procedure

Created a Markdown file with an image reference
(`![alt](image.png)`), uploaded via `upload_confluence.py` which uses
Confluence Storage Format.

### Results

Image displayed correctly. Storage format uses filename-based referencing:

```xml
<ac:image>
  <ri:attachment ri:filename="test_upload_img_green.png" />
</ac:image>
```

### Key Difference: Two Image Reference Approaches

| Approach | Format | Reference Method | Needs fileId? |
|----------|--------|------------------|---------------|
| Storage Format | XHTML (`<ac:image>`) | By filename (`ri:filename`) | No |
| ADF | JSON (`mediaSingle`/`media`) | By Media UUID (`attrs.id`) | **Yes** |

**Conclusion**: `upload_confluence.py` does NOT need changes — storage
format references by filename, Confluence resolves internally.

---

## Experiment 5: Non-Image Files as mediaGroup/mediaSingle

### Procedure

1. Created test files: `test_report.txt` (39 bytes) and `test_document.pdf` (316 bytes)
2. Uploaded both via v1 API
3. Added to page as both `mediaGroup` (side-by-side) and `mediaSingle` (individual blocks)

### Upload Results

```
test_report.txt:
  attachment ID: att2339864660
  fileId: 7637f4be-571e-4471-a3c4-f916a88bcb33
  mediaType: text/plain

test_document.pdf:
  attachment ID: att2340978743
  fileId: d39d19da-ac6a-40f9-ae82-ec15d178144a
  mediaType: application/pdf
```

### UI Results

| Display Mode | Appearance |
|-------------|------------|
| `mediaGroup` | Side-by-side file cards with filenames and dates |
| `mediaSingle` | Individual file cards, larger, with filename and date |

Both display modes work correctly for non-image files. Files show as downloadable cards (not inline previews).

**Conclusion**: The same `fileId` mechanism works for all file types, not just images.

---

## Key Findings Summary

### What Needs to Change

| File | Bug | Fix |
|------|-----|-----|
| `add_media.py` | Uses `results[0].id` (attachment ID) | Use `results[0].extensions.fileId` |
| `add_media.py` | `collection: ""` (empty string) | Use `results[0].extensions.collectionName` |
| `add_media_group.py` | Same two bugs as above | Same fixes |
| `upload_confluence.py` | N/A — uses storage format | **No change needed** |

### What to Add

A new `upload_attachment.py` script that:

- Supports any file type (not just images)
- Extracts `fileId` and `collectionName` from v1 API upload response
- Optionally inserts `mediaSingle` or `mediaGroup` node into page ADF
- Supports `--attach-only` mode (upload without modifying page body)

### Correct Upload-to-Display Flow

```
Step 1: Upload via v1 API
  POST /wiki/rest/api/content/{pageId}/child/attachment
  Headers: X-Atlassian-Token: no-check
  Body: multipart/form-data

Step 2: Extract IDs from response
  fileId     = response.results[0].extensions.fileId
  collection = response.results[0].extensions.collectionName

Step 3: Build ADF media node
  {
    "type": "media",
    "attrs": {
      "id": <fileId>,              // UUID format
      "type": "file",
      "collection": <collection>   // "contentId-{pageId}"
    }
  }

Step 4: Wrap in mediaSingle or mediaGroup
  mediaSingle → single file/image block
  mediaGroup  → multiple files side-by-side
```

---

## ADF Media Node Reference

### mediaSingle (block-level, single file/image)

```json
{
  "type": "mediaSingle",
  "attrs": {
    "layout": "center"
  },
  "content": [{
    "type": "media",
    "attrs": {
      "id": "<fileId-UUID>",
      "type": "file",
      "collection": "contentId-<pageId>"
    }
  }]
}
```

**Layout options**: `"center"`, `"wide"`, `"full-width"`, `"wrap-left"`, `"wrap-right"`, `"align-start"`, `"align-end"`

### mediaGroup (block-level, multiple files)

```json
{
  "type": "mediaGroup",
  "content": [
    {
      "type": "media",
      "attrs": {
        "id": "<fileId-1>",
        "type": "file",
        "collection": "contentId-<pageId>"
      }
    },
    {
      "type": "media",
      "attrs": {
        "id": "<fileId-2>",
        "type": "file",
        "collection": "contentId-<pageId>"
      }
    }
  ]
}
```

### Optional media attrs

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | integer | Display width in pixels (images only) |
| `height` | integer | Display height in pixels (images only) |
| `alt` | string | Alt text (images only) |
| `occurrenceKey` | string | Enables file deletion |

### Sources

- [Confluence REST API v1 - Attachments](https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content---attachments/)
- [Confluence REST API v2 - Attachment](https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-attachment/)
- [CONFCLOUD-77196 - Missing v2 upload endpoint](https://jira.atlassian.com/browse/CONFCLOUD-77196)
- [ADF mediaSingle Node](https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/mediaSingle/)
- [ADF media Node](https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/media/)
