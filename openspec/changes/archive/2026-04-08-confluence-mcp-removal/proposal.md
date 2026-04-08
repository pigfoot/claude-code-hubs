## Why

The Confluence plugin declares an Atlassian MCP server in `.mcp.json`. When MCP OAuth expires (55-minute sessions) or disconnects, Claude Code disables the **entire plugin** — including the skill and all 30 Python REST API scripts that have no dependency on MCP. Since most operations already use REST API, MCP is only needed for Rovo AI search, yet its instability brings down the whole plugin.

## What Changes

- **DELETE** `.mcp.json` — plugin no longer declares an MCP server dependency
- **CREATE** `scripts/read_page.py` — read Confluence pages via REST API v2 (replaces MCP `getConfluencePage`)
- **CREATE** `scripts/search_cql.py` — CQL search via REST API v1 (replaces MCP `searchConfluenceUsingCql`)
- **MODIFY** `scripts/mcp_json_diff_roundtrip.py` — implement `_read_page()` / `_write_page()` via REST API (currently `NotImplementedError`)
- **MODIFY** `SKILL.md` — replace all `mcp__plugin_confluence_atlassian__*` references with REST API scripts; add Rovo via built-in Atlassian MCP as optional search upgrade
- **MODIFY** routing logic — REST API is the only path; no MCP fallback for core ops
- Rovo AI search: use Claude Code's built-in `mcp__claude_ai_Atlassian__searchAtlassian` on-demand (optional, no plugin dependency)

## Capabilities

### New Capabilities

- `rest-page-read`: Read a Confluence page by ID via REST API v2, output as Markdown or raw ADF JSON
- `rest-cql-search`: Execute CQL queries against Confluence via REST API v1, with confidence scoring

### Modified Capabilities

- `smart-routing`: **BREAKING** — MCP is no longer a routing target for any operation. REST API is required (all 3 env vars). MCP fallback paths removed. Rovo search is no longer the default entry point.
- `smart-search`: **BREAKING** — Search direction inverted. CQL is now the primary search path. When CQL confidence < 0.6, suggest Rovo AI search (via built-in Atlassian MCP OAuth) instead of the current behavior of suggesting CQL when Rovo quality is low.

## Impact

- **Confluence plugin** (`plugins/confluence/`): `.mcp.json` deleted, `plugin.json` updated
- **SKILL.md**: Major rewrite — all MCP tool invocations replaced
- **scripts/**: 2 new scripts; `mcp_json_diff_roundtrip.py` + `confluence_router.py` modified
- **reference docs**: 3 files with 14 MCP references updated
- **README.md**: REST API credentials now required (not optional); MCP setup removed from quick start
- **Breaking for users**: Cannot use plugin without `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` (previously MCP OAuth was a no-credential fallback)
