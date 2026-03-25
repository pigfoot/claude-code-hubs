## Why

The current `download_confluence.py` / `upload_confluence.py` markdown roundtrip uses the v1 REST API (Storage format), which destroys page structures during the download → edit → upload cycle. Expand panels, emojis, @mentions, inline cards, and new-style ADF panels are all silently lost. This was confirmed on a real page (ID 2321482360) where a roundtrip upload dropped the page from 34 components to 22, losing all 4 expand panels, 2 emojis, 2 mentions, 2 inline cards, and 2 panels.

The root cause is that Storage format either lacks these elements entirely (inlineCard doesn't exist in v1 API) or represents them in ways that `markdownify` and `BeautifulSoup` cannot parse (`ac:emoticon`, `ac:link>ri:user`, `ac:adf-extension`). The v2 API returns ADF (JSON) where all elements are clean, typed nodes that can be reliably processed.

## What Changes

- **New**: `adf_to_markdown.py` — Custom ADF tree walker that converts ADF JSON to Markdown with HTML comment markers for Confluence-specific elements (expand, emoji, mention, inlineCard, panel, status, date)
- **New**: `markdown_to_adf.py` — Markdown parser (using mistune) extended with custom marker recognition that produces ADF JSON output
- **Modified**: `download_confluence.py` — Switch from v1 API (Storage format + markdownify) to v2 API (ADF + custom walker)
- **Modified**: `upload_confluence.py` — Switch from Storage format renderer to ADF JSON builder, write via v2 API
- **Modified**: `add_panel.py` — Fix `\n` escape sequences not converting to actual newlines (bug found during investigation)

## Capabilities

### New Capabilities

- `adf-markdown-conversion`: Bidirectional ADF ↔ Markdown conversion with custom markers that preserve Confluence-specific elements (expand, emoji, mention, inlineCard, panel, status, date) through the roundtrip

### Modified Capabilities

- `confluence-roundtrip`: Existing roundtrip requirements expand to cover full ADF element preservation via v2 API, not just text-level diff/patch (Method 6). The download/upload workflow (Method 1) now uses ADF natively instead of Storage format.

## Impact

- **Scripts**: `download_confluence.py`, `upload_confluence.py` — core logic rewritten to use v2 API
- **New scripts**: `adf_to_markdown.py`, `markdown_to_adf.py` — new converter modules
- **Shared utils**: `confluence_adf_utils.py` — already has `get_page_adf()` / `update_page_adf()`, no changes needed
- **Dependencies**: No new pip packages needed (mistune already used by upload, requests already used by ADF utils)
- **API**: Shifts from v1 (`/wiki/rest/api/content/{id}`) to v2 (`/wiki/api/v2/pages/{id}`) for roundtrip operations. The 28 existing ADF scripts already use v2 API and are unaffected.
- **Backward compatibility**: Old-style markdown files (without markers) can still be uploaded; markers are additive
- **Docs**: `roundtrip-implementation-comparison.md` already updated with Method 7 entry; SKILL.md will need updates after implementation
