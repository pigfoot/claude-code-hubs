## Why

The plugin's documentation and architecture incorrectly attributes macro loss during roundtrip editing to Storage Format limitations, when the actual cause is the Markdown intermediate conversion step. This leads to misleading guidance for users and an unnecessarily complex codebase with two parallel upload paths (Storage Format v1 and ADF v2). Testing with a real 37-element Confluence page confirmed that both direct Storage Format XML roundtrip and ADF JSON roundtrip (Method 6) are lossless — only the Markdown conversion step causes data loss.

## What Changes

- **Fix incorrect documentation**: Correct claims across 6+ reference docs that blame Storage Format for macro loss. The real cause is Markdown conversion (markdownify/html2text dropping `ac:*` XML tags), not Storage Format or the API itself.
- **Clarify format positioning**: Storage Format is NOT deprecated (v2 API supports `representation: storage`). Only v1 API endpoints and Legacy Editor UI are being deprecated.
- **Remove Storage Format upload path** (**BREAKING**): Remove `ConfluenceStorageRenderer` and the v1 Storage Format upload logic from `upload_confluence.py`. Standardize on ADF v2 for all uploads.
- **Remove legacy download path** (**BREAKING**): Remove `--legacy` flag and `convert_storage_to_markdown()` from `download_confluence.py`. Standardize on v2 ADF download.
- **Redefine component roles**:
  - `markdown_to_adf.py` (mistune): Repositioned from "roundtrip core" to "new page upload tool" (Markdown → ADF for initial page creation only)
  - `adf_to_markdown.py`: Repositioned from "roundtrip core" to "display utility" (rendering ADF as readable text for Claude, not a conversion step in the roundtrip)
  - Method 6 (JSON diff): Remains the sole roundtrip editing method — operates directly on ADF JSON, never converts through Markdown
- **Keep v1 API only where v2 has no equivalent**: Attachment upload (`/rest/api/content/{id}/child/attachment`) and page width property (`content-appearance-published`)

## Capabilities

### New Capabilities

_(none — this is a cleanup/correction change, not new functionality)_

### Modified Capabilities

- `adf-markdown-conversion`: Clarify that this conversion is for display/new-page-upload only, NOT for roundtrip editing. Remove any implication that Markdown is part of the roundtrip data path.
- `confluence-roundtrip`: Clarify that roundtrip operates directly on ADF JSON (Method 6), never through Markdown. Remove references to Storage Format roundtrip as a supported path.

## Impact

- **Documentation files** (6+ files): `v2-api-roundtrip-migration.md`, `roundtrip-workflow.md`, `roundtrip-implementation-comparison.md`, `macro-preservation-guide.md`, `markdown-first-workflow.md`, `comparison-tables.md`
- **Scripts**: `upload_confluence.py` (remove Storage path), `download_confluence.py` (remove legacy path)
- **Dependencies**: `mistune` retained (used by `markdown_to_adf.py` for new page upload). `markdownify`, `beautifulsoup4` may become removable if legacy download path is dropped.
- **SKILL.md**: Update tool selection guidance to reflect simplified architecture
- **Tests**: Existing 71 tests (ADF roundtrip) remain valid. May remove or update tests for removed Storage Format paths.
