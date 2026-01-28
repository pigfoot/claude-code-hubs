# Tasks: Confluence Smart Routing

## Phase 1: Environment Variable Standardization (P0)

### 1.1 Rename CONFLUENCE_USERNAME to CONFLUENCE_USER

- [x] Update `upload_confluence.py`: Change `os.getenv("CONFLUENCE_USERNAME")` → `os.getenv("CONFLUENCE_USER")`
- [x] Update `download_confluence.py`: Same change
- [x] Update `confluence_adf_utils.py`: Same change
- [x] Update `README.md`: Update all documentation references

**Validation:** Run `rg "CONFLUENCE_USERNAME" plugins/confluence/` returns no matches ✅

### 1.2 Update Documentation

- [x] Update Quick Setup section in `plugins/confluence/README.md`
- [x] Update environment variable tables
- [x] Add migration note for existing users

**Validation:** Documentation shows `CONFLUENCE_USER` consistently ✅

---

## Phase 2: Core Smart Routing (P0)

### 2.1 Create Router Module

- [x] Create `plugins/confluence/skills/confluence/scripts/confluence_router.py`
- [x] Implement `detect_credentials()` function
- [x] Implement `route_request(operation, params)` function
- [x] Add operation type constants: `READ`, `WRITE`, `SEARCH_CQL`, `SEARCH_ROVO`, `UPLOAD`

**Validation:** Unit tests for credential detection and routing logic ✅

### 2.2 Integrate Router with Existing Scripts

- [x] Add router import to `upload_confluence.py`
- [x] Add router import to `download_confluence.py`
- [x] Log which API is being used for transparency

**Validation:** Scripts use router for API selection ✅

---

## Phase 3: URL Resolution (P1)

### 3.1 Implement URL Resolver

- [x] Create `plugins/confluence/skills/confluence/scripts/url_resolver.py`
- [x] Implement `decode_tiny_url(code)` - Base64 decoding
- [x] Implement `resolve_confluence_url(url)` - Pattern matching for all URL formats
- [x] Support formats: `/wiki/x/...`, `/pages/123456/...`, raw page ID

**Validation:** ✅

```bash
python url_resolver.py "https://site.atlassian.net/wiki/x/ZQGBfg"
# Output: {"type": "page_id", "value": "1694597502"}
```

### 3.2 Integrate URL Resolution

- [x] Add URL resolution to router before API calls
- [x] Accept URLs as input in addition to page IDs

**Validation:** Scripts accept both URLs and page IDs ✅

---

## Phase 4: Smart Search (P1)

### 4.1 Implement Confidence Scoring

- [x] Create `plugins/confluence/skills/confluence/scripts/smart_search.py`
- [x] Implement `calculate_confidence(query, results)` function
- [x] Factors: title matches, keyword overlap, result count

**Validation:** Confidence scores match expected ranges for test queries ✅

### 4.2 Add Precision Warning

- [x] Return suggestion when confidence < 0.6
- [x] Include CQL preview in suggestion
- [x] Support bilingual messages (Chinese/English)

**Validation:** Low-precision searches show suggestions ✅

---

## Phase 5: Fallback and Warnings (P2)

### 5.1 MCP Write Speed Warning

- [x] Detect when MCP is used for write without API token
- [x] Display warning message with setup instructions
- [x] Include link to API token generation page

**Validation:** Warning appears when writing via MCP ✅

### 5.2 MCP Session Expiry Fallback

- [x] Detect "Session not found" and "token expired" errors
- [x] Silently fallback to REST API when token available
- [x] Prompt re-authentication when token not available

**Validation:** Test cases T-008 and T-009 pass ✅

### 5.3 Token Expiry Detection

- [x] Implement error pattern matching for MCP failures
- [x] Log fallback events for debugging
- [x] Handle edge cases (network errors vs auth errors)

**Validation:** Fallback succeeds >95% of the time ✅

---

## Phase 6: Documentation and Testing (P2)

### 6.1 Update Research Documentation

- [x] Move final design decisions to `research.md`
- [x] Document performance benchmarks
- [x] Add troubleshooting section

**Validation:** Documentation complete and accurate ✅

### 6.2 Integration Testing

- [x] Test matrix: all 9 test cases from design.md
- [x] Cross-platform testing (macOS, Linux, Windows)
- [x] Edge case testing (invalid URLs, network failures)

**Validation:** All test cases pass ✅

---

## Dependencies

```
Phase 1 (ENV) ──┐
               ├──> Phase 2 (Router) ──> Phase 5 (Fallback)
Phase 3 (URL) ──┘

Phase 4 (Search) ──> Phase 5 (Fallback)

Phase 6 (Docs) depends on all previous phases
```

## Parallelizable Work

- Phase 1 and Phase 3 can run in parallel
- Phase 4 can run in parallel with Phase 2
- Phase 6 must wait for all others
