# Change: Confluence Smart Routing

## Why

The Confluence plugin currently has two separate access methods with no intelligent selection:

1. **MCP (via Atlassian connector):**
   - Easy OAuth setup (browser-based)
   - 55-minute token expiry requiring frequent re-authentication
   - ~26 second write times (server-side Markdown conversion)
   - Exclusive access to Rovo AI search

2. **REST API (via Python scripts):**
   - Permanent API token (never expires)
   - ~1 second write times (25x faster)
   - No Rovo AI search capability
   - Requires manual environment variable configuration

**Problems:**
- Users must manually choose which method to use
- No automatic fallback when one API fails
- Inconsistent experience between API and MCP modes
- Environment variable naming is inconsistent (`CONFLUENCE_USERNAME` vs industry standard `CONFLUENCE_USER`)
- Users often don't know MCP writes are slow until they wait 26 seconds

## What Changes

### Core Capabilities

1. **Environment Variable Standardization**
   - **BREAKING:** Rename `CONFLUENCE_USERNAME` → `CONFLUENCE_USER` in all scripts
   - Update all documentation to reflect new naming
   - Rationale: Follows industry convention (`DB_USER`, `MYSQL_USER`, `POSTGRES_USER`)

2. **Smart Routing**
   - New `confluence_router.py` module for intelligent API selection
   - Auto-detect credentials from environment variables
   - Route operations to optimal API based on type:
     - Read/Search with token → REST API
     - Read/Search without token → MCP
     - Write with token → REST API (~1s)
     - Write without token → MCP (~26s) + warning
     - Rovo AI search → MCP (exclusive)
   - Graceful fallback when primary API fails

3. **URL Resolution**
   - New `url_resolver.py` module for decoding Confluence URLs
   - Support short URLs (`/wiki/x/ZQGBfg`) via Base64 decoding
   - Support full URLs (`/pages/123456/...`)
   - Support direct page IDs
   - Local processing (no network calls needed)

4. **Smart Search**
   - New `smart_search.py` module for search quality detection
   - Calculate confidence score based on title matches and result count
   - Suggest CQL alternative when Rovo results may be imprecise (confidence < 0.6)
   - Generate CQL preview query for user

5. **User Feedback**
   - Display warning when using MCP for writes without API token
   - Include setup instructions and API token generation link
   - Silent fallback to REST API when MCP session expires (if token available)
   - Prompt re-authentication when MCP expires and no token available

### Breaking Change

- **BREAKING:** `CONFLUENCE_USERNAME` is no longer supported
- Users must update to `CONFLUENCE_USER` in their environment configuration

## Impact

### Affected Capabilities

- **smart-routing** (NEW) - Intelligent API selection and fallback
- **url-resolution** (NEW) - Confluence URL decoding
- **smart-search** (NEW) - Search quality detection
- **env-standardization** (NEW) - Environment variable naming standards
- **confluence-roundtrip** (MODIFIED) - Integration with smart routing

### Affected Files

**New Files:**
- `plugins/confluence/skills/confluence/scripts/confluence_router.py`
- `plugins/confluence/skills/confluence/scripts/url_resolver.py`
- `plugins/confluence/skills/confluence/scripts/smart_search.py`

**Modified Files:**
- `plugins/confluence/skills/confluence/scripts/upload_confluence.py`
- `plugins/confluence/skills/confluence/scripts/download_confluence.py`
- `plugins/confluence/skills/confluence/scripts/confluence_adf_utils.py`
- `plugins/confluence/README.md`

### Testing Requirements

- Unit tests for credential detection
- Unit tests for URL resolution (all formats)
- Unit tests for confidence scoring
- Integration tests for routing decisions
- Fallback scenario testing (MCP expiry)
- Cross-platform testing (macOS, Linux, Windows)

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| REST API write | <2s | 1.02s |
| MCP write | ~26s | 25.96s |
| URL resolution | <10ms | N/A |
| Fallback success rate | >95% | N/A |

## Design Reference

Complete technical design and implementation details are documented in:
- [docs/plans/005-confluence-smart-routing/design.md](../../docs/plans/005-confluence-smart-routing/design.md)
- [docs/plans/005-confluence-smart-routing/research.md](../../docs/plans/005-confluence-smart-routing/research.md)

Key decisions:
- REST API is primary when credentials available (25x faster writes)
- MCP provides zero-config fallback experience
- Local Base64 decoding for URL resolution (no network calls)
- Confidence threshold of 0.6 for search quality warnings
