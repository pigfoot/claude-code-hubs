## 1. Fix Documentation — Macro Loss Attribution

- [x] 1.1 Fix `plans/v2-api-roundtrip-migration.md`: Correct claims that Storage Format causes macro loss → clarify Markdown intermediate is the cause
- [x] 1.2 Fix `references/roundtrip-workflow.md`: Correct Method 1 cons and critical warning box → macro loss is from Markdown conversion, not API or format
- [x] 1.3 Fix `references/roundtrip-implementation-comparison.md`: Correct "Methods 1-3 all lose macros" → clarify loss is from Markdown step, not inherent to the methods
- [x] 1.4 Fix `references/macro-preservation-guide.md`: Change "❌ Lost" labels → "❌ Lost via Markdown conversion (preserved via direct ADF/Storage XML roundtrip)"
- [x] 1.5 Fix `references/markdown-first-workflow.md`: Remove "existing pages with complex macros: use Confluence web editor directly" → direct roundtrip is possible
- [x] 1.6 Fix `references/comparison-tables.md`: Add emphasis that v2 API fully supports Storage Format representation

## 2. Fix Documentation — Storage Format Deprecation Claims

- [x] 2.1 Add clarification across all docs: Storage Format is NOT deprecated, only v1 API endpoints and Legacy Editor UI are
- [x] 2.2 Add clarification: v2 API supports `representation: storage` for GET/PUT/POST
- [x] 2.3 Add note about MCP Gateway limitation: MCP only supports ADF, but direct REST API v2 supports both formats

## 3. Remove Storage Format Upload Path

- [x] 3.1 Remove `ConfluenceStorageRenderer` class from `upload_confluence.py`
- [x] 3.2 Remove `convert_markdown_to_storage()` function from `upload_confluence.py`
- [x] 3.3 Remove Storage Format v1 upload logic (`upload_to_confluence()` with `representation: storage`)
- [x] 3.4 Update `upload_to_confluence_adf()` to be the sole upload path
- [x] 3.5 Remove `--legacy` flag from `upload_confluence.py` CLI arguments
- [x] 3.6 Remove marker-free fallback to Storage Format — all uploads go through `markdown_to_adf.py` → ADF v2

## 4. Remove Legacy Download Path

- [x] 4.1 Remove `--legacy` flag from `download_confluence.py` CLI arguments
- [x] 4.2 Remove `convert_storage_to_markdown()` function from `download_confluence.py`
- [x] 4.3 Remove `download_page()` v1 function (keep only `download_page_v2()`)
- [x] 4.4 Evaluate if `markdownify` and `beautifulsoup4` dependencies can be removed from inline metadata

## 5. Update Component Role Documentation

- [x] 5.1 Update `SKILL.md`: Clarify `markdown_to_adf.py` is for new page upload only, not roundtrip
- [x] 5.2 Update `SKILL.md`: Clarify `adf_to_markdown.py` is a display utility for Claude, not a roundtrip data path
- [x] 5.3 Update `SKILL.md`: Clarify Method 6 operates directly on ADF JSON, Markdown shown to Claude is display-only
- [x] 5.4 Update `README.md`: Reflect simplified architecture (single format path, ADF v2)
- [x] 5.5 Update `DEVELOPMENT.md`: Add section explaining the architecture decision (ADF v2 + Method 6, no Markdown intermediate for roundtrip)

## 6. Update Upload Script for ADF-Only Path

- [x] 6.1 Update `upload_confluence.py` main flow: always use `markdown_to_adf()` regardless of marker presence
- [x] 6.2 Keep `_set_page_width()` via v1 API (no v2 equivalent)
- [x] 6.3 Keep attachment upload via v1 API (no v2 equivalent)
- [x] 6.4 Update inline script dependencies: remove `markdownify`, `beautifulsoup4` if no longer needed

## 7. Verify and Update Tests

- [x] 7.1 Run existing tests to confirm no regressions (75 tests passing)
- [x] 7.2 Remove or update any tests that reference Storage Format upload/download paths (none existed)
- [x] 7.3 Add test verifying `markdown_to_adf()` works for marker-free markdown (no Storage fallback needed)
- [x] 7.4 Verify the multiple-status-on-one-line fix is covered by tests (already added)
