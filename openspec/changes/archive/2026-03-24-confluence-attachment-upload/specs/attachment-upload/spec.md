## ADDED Requirements

### Requirement: Upload any file type as Confluence attachment

The system SHALL upload any file type (images, PDFs, documents,
archives, etc.) to a Confluence page as an attachment via the v1 REST
API, extracting `fileId` and `collectionName` from the upload response
for correct ADF referencing.

#### Scenario: Upload a single file as attachment only

- **WHEN** user runs `upload_attachment.py PAGE_ID --file ./report.pdf --attach-only`
- **THEN** the system SHALL upload the file via `POST /wiki/rest/api/content/{pageId}/child/attachment`
- **AND** SHALL set `X-Atlassian-Token: no-check` header
- **AND** SHALL auto-detect content-type from file extension
- **AND** SHALL NOT modify the page body
- **AND** SHALL display the `fileId`, `attachmentId`, and filename in output

#### Scenario: Upload and display as mediaSingle

- **WHEN** user runs `upload_attachment.py PAGE_ID --file ./diagram.png --media-single --after-heading "Screenshots"`
- **THEN** the system SHALL upload the file as an attachment
- **AND** SHALL extract `fileId` from `response.results[0].extensions.fileId`
- **AND** SHALL extract `collectionName` from `response.results[0].extensions.collectionName`
- **AND** SHALL insert a `mediaSingle` ADF node after the specified heading
- **AND** the `media` node `attrs.id` SHALL be the `fileId` (UUID format)
- **AND** the `media` node `attrs.collection` SHALL be the `collectionName`

#### Scenario: Upload and display as mediaGroup

- **WHEN** user runs `upload_attachment.py PAGE_ID --files ./a.pdf ./b.docx --media-group --at-end`
- **THEN** the system SHALL upload all files as attachments
- **AND** SHALL insert a single `mediaGroup` ADF node containing one `media` child per file
- **AND** each `media` node SHALL use the correct `fileId` and `collectionName`

#### Scenario: Auto-detect content type

- **WHEN** user uploads a file with a known extension
- **THEN** the system SHALL map the extension to the correct MIME type:
  - `.png` → `image/png`
  - `.jpg`, `.jpeg` → `image/jpeg`
  - `.gif` → `image/gif`
  - `.svg` → `image/svg+xml`
  - `.pdf` → `application/pdf`
  - `.doc` → `application/msword`
  - `.docx` → `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `.xls` → `application/vnd.ms-excel`
  - `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `.zip` → `application/zip`
  - `.txt` → `text/plain`
  - Unknown → `application/octet-stream`

#### Scenario: File not found

- **WHEN** user specifies a file path that does not exist
- **THEN** the system SHALL exit with error code 1
- **AND** SHALL display an error message with the missing file path

#### Scenario: Dry run mode

- **WHEN** user includes `--dry-run` flag
- **THEN** the system SHALL display what would be uploaded and where it would be placed
- **AND** SHALL NOT upload any files or modify the page

---

### Requirement: Shared upload helper function

The system SHALL provide a shared `upload_attachment_file()` function
in `confluence_adf_utils.py` that returns the correct IDs for ADF
media node construction.

#### Scenario: Upload and return structured result

- **WHEN** `upload_attachment_file(base_url, auth, page_id, file_path)` is called
- **THEN** the function SHALL upload the file via v1 REST API
- **AND** SHALL return a dict with keys: `fileId`, `collectionName`, `attachmentId`, `filename`, `mediaType`
- **AND** `fileId` SHALL be extracted from `response.results[0].extensions.fileId`
- **AND** `collectionName` SHALL be extracted from `response.results[0].extensions.collectionName`

#### Scenario: Upload failure

- **WHEN** the upload API returns a non-2xx status code
- **THEN** the function SHALL return `None`
- **AND** SHALL print an error message with the status code and response body

#### Scenario: fileId missing from response

- **WHEN** the v1 API response does not contain `extensions.fileId`
- **THEN** the function SHALL fall back to querying `GET /wiki/api/v2/attachments/{attachmentId}` to obtain the `fileId`
- **AND** SHALL log a warning about the fallback
