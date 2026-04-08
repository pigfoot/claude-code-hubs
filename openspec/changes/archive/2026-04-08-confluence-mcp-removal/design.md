## Context

The Confluence plugin bundles an Atlassian MCP server via `.mcp.json`. Claude Code treats this as a hard dependency: when the MCP OAuth session expires (55 min), the entire plugin — including the REST API scripts — is disabled. The plugin's 30 Python scripts already use REST API for uploads, structural edits, and downloads. MCP is only required for: page reads, CQL search, and Rovo AI search.

Existing REST API infrastructure (`confluence_adf_utils.py`) already provides `get_auth()`, `get_page_adf()`, `update_page_adf()`, `create_page_adf()` — everything needed to replace MCP for reads/writes.

## Goals / Non-Goals

**Goals:**
- Plugin never disabled due to MCP OAuth expiry
- CQL search works without any OAuth flow
- Rovo AI search remains available as optional upgrade (triggers OAuth only when CQL quality is insufficient)
- Method 6 (roundtrip editing) works without MCP

**Non-Goals:**
- Supporting users without REST API credentials (`CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`)
- Implementing our own OAuth flow for Rovo
- Replacing Rovo with a custom semantic search

## Decisions

### Decision 1: Delete `.mcp.json`, not conditional loading

**Chosen**: Hard delete `.mcp.json`.

**Alternative considered**: Make MCP optional by checking connectivity at startup.

**Rationale**: Claude Code either loads a plugin's MCP or it doesn't — there's no "optional MCP" concept. Any declared MCP server that fails to connect disables the plugin. Deleting the file is the only way to break the dependency.

---

### Decision 2: CQL-first search, Rovo as upgrade path

**Chosen**: Run `search_cql.py` first. When `smart_search.py` detects confidence < 0.6, ask user if they want Rovo (triggers OAuth via built-in `mcp__claude_ai_Atlassian__authenticate`).

**Alternative considered**: Try Rovo first, fall back to CQL (mirror of current behavior).

**Rationale**: CQL requires no OAuth and always works with REST API credentials. Starting with CQL means zero latency for the common case where results are adequate. Rovo OAuth is only triggered when the user explicitly consents, avoiding surprise auth prompts. This also aligns with the broader principle of making OAuth an explicit user action.

---

### Decision 3: Built-in Atlassian MCP for Rovo (`mcp__claude_ai_Atlassian__*`)

**Chosen**: When Rovo is needed, use Claude Code's built-in Atlassian integration (`mcp__claude_ai_Atlassian__searchAtlassian`), not a plugin-declared server.

**Alternative considered**: Keep `.mcp.json` but make search the only MCP operation.

**Rationale**: Even a minimal `.mcp.json` recreates the dependency problem. The built-in integration is Claude Code's own responsibility — if it fails, it doesn't take down the plugin. The tool namespace changes from `mcp__plugin_confluence_atlassian__*` to `mcp__claude_ai_Atlassian__*`, but since SKILL.md is rewritten anyway, this is acceptable.

---

### Decision 4: New scripts `read_page.py` and `search_cql.py` (not extending existing scripts)

**Chosen**: Create two new lightweight scripts following the pattern of `analyze_page.py`.

**Alternative considered**: Add `--read` / `--search` flags to `download_confluence.py`.

**Rationale**: `download_confluence.py` is heavy — it writes files, fetches children, downloads attachments. A lightweight `read_page.py` that writes to stdout is what SKILL.md needs for the reading workflow and Method 6 ADF ingestion. Similarly, `search_cql.py` is a focused tool. Single-responsibility keeps scripts composable.

---

### Decision 5: `smart_search.py` suggestion reversal

**Chosen**: When CQL confidence < 0.6, the suggestion message asks if the user wants Rovo AI search (instead of current "consider using CQL").

**Rationale**: The suggestion must match the new search direction. CQL is now the baseline; Rovo is the upgrade. The confidence scoring algorithm itself is unchanged.

---

### Decision 6: `mcp_json_diff_roundtrip.py` — implement `_read_page()` / `_write_page()` via REST API

**Chosen**: Implement the two `NotImplementedError` stubs using `confluence_adf_utils.get_page_adf()` and `update_page_adf()`.

**Rationale**: These stubs were placeholder comments pointing to MCP tool calls. Now that we have REST API equivalents, they can be real implementations. The `roundtrip_helper.py` interface (`process_confluence_edit()`) is unchanged — callers don't know how the read/write happens.

## Risks / Trade-offs

**Breaking change: REST API credentials now required**
→ Users who relied on MCP OAuth as their only credential path lose access. Mitigation: clear error message in `get_auth()` with setup instructions; README Quick Start updated to make credentials Step 1.

**Built-in Atlassian MCP tool names may change**
→ Anthropic could rename `mcp__claude_ai_Atlassian__*` in future Claude Code versions. Mitigation: SKILL.md is a text file — easy to update. No code depends on the tool names.

**Rovo OAuth prompt UX is unclear**
→ When `smart_search.py` suggests Rovo and the user agrees, Claude calls `mcp__claude_ai_Atlassian__authenticate`, which launches a browser OAuth flow. If the user is on a headless machine, this may fail silently. Mitigation: SKILL.md documents the fallback ("if authentication isn't possible, use CQL results as-is").

**smart_search.py suggestion threshold may need tuning**
→ The 0.6 confidence threshold was calibrated for Rovo → CQL suggestions. CQL → Rovo suggestions may need different calibration since CQL and Rovo have different precision characteristics. Mitigation: threshold is a constant (`SUGGESTION_THRESHOLD = 0.6`) that can be tuned independently.

## Migration Plan

For existing plugin users:

1. Set REST API credentials if not already set:
   ```bash
   export CONFLUENCE_URL="https://yoursite.atlassian.net/wiki"
   export CONFLUENCE_USER="your-email@company.com"
   export CONFLUENCE_API_TOKEN="your-token"
   ```
2. `claude plugin update confluence` (picks up new plugin version without `.mcp.json`)
3. No data migration needed — all page content stays on Confluence

**Rollback**: Re-add `.mcp.json` and revert SKILL.md. No state to unwind.

## Open Questions

- Should `search_cql.py` pass results through `smart_search.py` automatically, or should SKILL.md instruct Claude to call `smart_search.py` separately? (Separate call is more composable but requires SKILL.md to chain two scripts.)
