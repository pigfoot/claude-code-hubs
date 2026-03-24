## MODIFIED Requirements

### Requirement: Upload any file type as Confluence attachment

The system SHALL upload any file type (images, PDFs, documents,
archives, etc.) to a Confluence page as an attachment via the v1 REST
API, extracting `fileId` and `collectionName` from the upload response
for correct ADF referencing.

This modifies how `add_media.py` and `add_media_group.py` construct ADF media nodes after uploading attachments.

#### Scenario: Upload image and add as mediaSingle

- **WHEN** user runs `add_media.py PAGE_ID --image-path ./screenshot.png --at-end`
- **THEN** the system SHALL upload the image via v1 REST API
- **AND** SHALL extract `fileId` from `response.results[0].extensions.fileId`
- **AND** SHALL extract `collectionName` from `response.results[0].extensions.collectionName`
- **AND** SHALL construct a `mediaSingle` ADF node where `media.attrs.id` is the `fileId` (UUID format)
- **AND** `media.attrs.collection` SHALL be the `collectionName` (e.g., `"contentId-{pageId}"`)

#### Scenario: Upload multiple images and add as mediaGroup

- **WHEN** user runs `add_media_group.py PAGE_ID --images ./a.png ./b.png --at-end`
- **THEN** the system SHALL upload all images via v1 REST API
- **AND** SHALL extract `fileId` and `collectionName` for each upload
- **AND** SHALL construct a `mediaGroup` ADF node where each `media`
  child uses the correct `fileId` and `collectionName`

#### Scenario: Image displays correctly in Confluence UI

- **WHEN** a `mediaSingle` or `mediaGroup` node is added to a page
- **THEN** the image SHALL render inline in the Confluence page (not "Preview unavailable")
- **AND** the image SHALL be clickable for full-size preview
