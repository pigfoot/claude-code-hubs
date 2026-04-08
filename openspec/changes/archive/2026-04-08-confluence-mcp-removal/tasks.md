## 1. New Scripts

- [x] 1.1 Create `scripts/read_page.py` — read page as Markdown via REST API v2 (reuse `get_auth`, `get_page_adf`, `adf_to_markdown`; accept URL or ID; stdout only)
- [x] 1.2 Add `--format adf` mode to `read_page.py` — output JSON with `page_id`, `title`, `version`, `space_id`, `adf` fields
- [x] 1.3 Create `scripts/search_cql.py` — CQL search via REST API v1 (`/wiki/rest/api/content/search`); default formatted output + `--format json`
- [x] 1.4 Integrate `smart_search.SmartSearch` into `search_cql.py` — run confidence analysis; include Rovo suggestion when confidence < 0.6

## 2. Update Existing Scripts

- [x] 2.1 Update `scripts/smart_search.py` — reverse suggestion message: when confidence < 0.6, suggest Rovo AI search instead of CQL; remove CQL preview generation from public output
- [x] 2.2 Update `scripts/confluence_router.py` — set `has_mcp = False`; remove MCP fallback paths; update SEARCH_ROVO routing message to reference built-in `mcp__claude_ai_Atlassian__searchAtlassian`; update `handle_fallback()` to remove MCP scenarios
- [x] 2.3 Update `scripts/mcp_json_diff_roundtrip.py` — implement `_read_page()` using `get_auth` + `get_page_adf`; implement `_write_page()` using `update_page_adf`; add `requests`, `python-dotenv` to PEP 723 deps; remove MCP tool name references in comments

## 3. SKILL.md Rewrite

- [x] 3.1 Update Critical Rules — remove "MCP is fine for reading" line; add REST API-only rule; add Rovo via built-in MCP rule
- [x] 3.2 Update Architecture diagram — add `read_page.py` and `search_cql.py` lines; remove MCP fallback line
- [x] 3.3 Update Decision Matrix — replace MCP tools rows with `read_page.py`/`search_cql.py`; remove "Small page create via MCP" row; add new script entries
- [x] 3.4 Rewrite Reading Pages workflow — use `read_page.py PAGE_ID` instead of MCP `getConfluencePage`
- [x] 3.5 Rewrite Method 6 workflow step 1 — use `read_page.py PAGE_ID --format adf` instead of MCP read
- [x] 3.6 Rewrite Search section — `search_cql.py` as primary; add Rovo upgrade workflow (confidence < 0.6 → ask user → `mcp__claude_ai_Atlassian__authenticate` → `mcp__claude_ai_Atlassian__searchAtlassian`)
- [x] 3.7 Delete MCP Upload Fallback section
- [x] 3.8 Delete "Create/Update Pages via MCP" section
- [x] 3.9 Update Common Mistakes table — replace "Ignoring 401 → run /mcp" with API token guidance
- [x] 3.10 Update Prerequisites — REST API env vars required; MCP optional for Rovo

## 4. Remove MCP Declaration

- [x] 4.1 Delete `plugins/confluence/.mcp.json`
- [x] 4.2 Update `plugin.json` — replace `"mcp"` with `"rest-api"` in keywords

## 5. Update Reference Docs

- [x] 5.1 Update `references/roundtrip-workflow.md` — replace 2 MCP tool references with REST API equivalents
- [x] 5.2 Update `references/mention-account-id-lookup.md` — replace 6 MCP tool references
- [x] 5.3 Update `references/roundtrip-implementation-comparison.md` — replace 6 MCP tool references

## 6. Update README.md

- [x] 6.1 Make REST API credentials required in Quick Start (Step 1, not optional)
- [x] 6.2 Remove "MCP Server Configuration" as a required setup step
- [x] 6.3 Add optional "Rovo AI Search" section (built-in Atlassian MCP, on-demand auth)
- [x] 6.4 Update Smart Routing section — reframe as REST API only, no MCP dependency
- [x] 6.5 Remove MCP-related FAQ and troubleshooting entries

## 7. Verification

- [x] 7.1 Grep check: `grep -r "mcp__plugin_confluence_atlassian" plugins/confluence/` returns 0 results
- [x] 7.2 Smoke test `read_page.py PAGE_ID` and `read_page.py PAGE_ID --format adf`
- [x] 7.3 Smoke test `search_cql.py 'title ~ "known page"'`
- [x] 7.4 Regression: `analyze_page.py`, `download_confluence.py`, `upload_confluence.py --dry-run` all still work
- [x] 7.5 Run existing test suite: `cd plugins/confluence && python -m pytest tests/`
- [x] 7.6 Confirm plugin loads correctly after `.mcp.json` deletion (no MCP errors on plugin load)
