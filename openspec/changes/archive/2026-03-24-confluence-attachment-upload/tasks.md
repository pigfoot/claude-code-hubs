## 1. Shared Upload Helper

- [x] 1.1 Add `upload_attachment_file()` function to
  `confluence_adf_utils.py` that uploads via v1 API and returns
  `{ fileId, collectionName, attachmentId, filename, mediaType }`
- [x] 1.2 Add v2 API fallback in `upload_attachment_file()` when `extensions.fileId` is missing from v1 response
- [x] 1.3 Add content-type detection map (png, jpg, gif, svg, pdf, doc, docx, xls, xlsx, zip, txt + fallback)

## 2. Fix add_media.py

- [x] 2.1 Replace inline `upload_attachment()` with shared `upload_attachment_file()` from `confluence_adf_utils`
- [x] 2.2 Update `add_media()` to use `fileId` for `media.attrs.id` and `collectionName` for `media.attrs.collection`
- [x] 2.3 Remove `localId` generation from media attrs (not required by ADF)
- [x] 2.4 Test: upload an image and verify it displays correctly in Confluence UI

## 3. Fix add_media_group.py

- [x] 3.1 Replace inline `upload_attachment()` with shared `upload_attachment_file()` from `confluence_adf_utils`
- [x] 3.2 Update `add_media_group()` to use `fileId` and `collectionName` for each media child node
- [x] 3.3 Test: upload multiple images and verify mediaGroup displays correctly

## 4. New upload_attachment.py Script

- [x] 4.1 Create `upload_attachment.py` with CLI args: `PAGE_ID`,
  `--file`/`--files`, `--attach-only`/`--media-single`/`--media-group`,
  `--after-heading`/`--at-end`, `--dry-run`
- [x] 4.2 Implement attach-only mode (upload without modifying page body)
- [x] 4.3 Implement media-single mode (upload + insert mediaSingle ADF node)
- [x] 4.4 Implement media-group mode (upload multiple + insert mediaGroup ADF node)
- [x] 4.5 Test: upload a PDF and a txt file, verify file cards display in Confluence UI

## 5. Documentation

- [x] 5.1 Add `upload_attachment.py` to SKILL.md command reference table and Quick Decision Matrix
- [x] 5.2 Update README.md with attachment upload examples and supported file types
