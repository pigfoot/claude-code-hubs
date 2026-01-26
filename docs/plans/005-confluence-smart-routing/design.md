# Design: Confluence Smart Routing

## Overview

This document specifies the design for intelligent API routing in the Confluence plugin, automatically selecting between MCP and REST API based on operation type, available credentials, and user preferences.

**Core Principle:** Use the fastest available method, with graceful fallback and user transparency.

---

## User Requirements

| Item | Decision |
|------|----------|
| Primary Use Case | **Read/Search** (occasional writes) |
| Write Speed Requirement | **1-5 seconds** (not 26 seconds MCP) |
| Setup Preference | **Auto-detect** (fast if token available, works without) |
| MCP-exclusive Features (Rovo) | **Nice to have** (not essential) |

---

## Architecture

### Current State (No Routing)

```
User Request
    ↓
┌─────────────────────────────────────┐
│ MCP Only (via Atlassian connector)  │
│ - 55 min token expiry               │
│ - 26s write speed                   │
│ - Rovo search available             │
└─────────────────────────────────────┘
    OR
┌─────────────────────────────────────┐
│ REST API Only (manual scripts)      │
│ - Permanent API token               │
│ - 1s write speed                    │
│ - No Rovo search                    │
└─────────────────────────────────────┘
```

**Problems:**
- ❌ Manual selection between APIs
- ❌ No automatic fallback
- ❌ Inconsistent user experience

### New Architecture (Smart Routing)

```
User Request
    ↓
┌─────────────────────────────────────┐
│        Smart Router                 │
│  1. Detect available credentials    │
│  2. Analyze operation type          │
│  3. Select optimal API              │
│  4. Execute with fallback           │
└─────────────────────────────────────┘
    ↓
┌──────────────┐    ┌──────────────┐
│  REST API    │ or │     MCP      │
│  (Primary)   │    │  (Fallback)  │
└──────────────┘    └──────────────┘
```

**Benefits:**
- ✅ Automatic API selection
- ✅ Graceful fallback on failure
- ✅ Optimal performance per operation
- ✅ Transparent to user

---

## Routing Logic

### Decision Matrix

| Operation | Has API Token | No API Token | Rationale |
|-----------|---------------|--------------|-----------|
| **Read Page** | REST API | MCP | Both work, REST slightly faster |
| **Search (CQL)** | REST API | MCP | Precision search |
| **Search (Rovo AI)** | MCP | MCP | MCP-exclusive feature |
| **Write Page** | REST API (~1s) ✅ | MCP (~26s) + ⚠️ warning | Speed critical |
| **Upload Attachment** | REST API | ❌ Not supported | MCP cannot upload files |
| **Resolve Short URL** | Either | Either | Decode locally, then fetch |

### Pseudo-code

```python
def route_request(operation: str, params: dict) -> Result:
    has_token = bool(os.getenv("CONFLUENCE_API_TOKEN"))

    if operation == "rovo_search":
        # MCP-exclusive
        return execute_mcp(operation, params)

    if operation == "write" and not has_token:
        # Warn about slow write
        warn("MCP writes take ~26 seconds. Set CONFLUENCE_API_TOKEN for 25x faster writes.")

    if has_token:
        # Try REST API first
        try:
            return execute_rest_api(operation, params)
        except Exception as e:
            log(f"REST API failed: {e}, falling back to MCP")
            return execute_mcp(operation, params)
    else:
        # MCP only mode
        return execute_mcp(operation, params)
```

---

## Environment Variables

### Standardization Task

**Current (inconsistent):**
```bash
CONFLUENCE_USERNAME=email@company.com  # Used in scripts
CONFLUENCE_USER=email@company.com      # Not used
```

**New (standardized):**
```bash
CONFLUENCE_USER=email@company.com      # Best practice naming
```

**Migration:**
- Update all scripts: `CONFLUENCE_USERNAME` → `CONFLUENCE_USER`
- Files to update:
  - `upload_confluence.py`
  - `download_confluence.py`
  - `confluence_adf_utils.py`

### Final Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CONFLUENCE_URL` | Yes | Base URL (e.g., `https://yoursite.atlassian.net/wiki`) |
| `CONFLUENCE_USER` | Yes* | User email for REST API auth |
| `CONFLUENCE_API_TOKEN` | Yes* | API token for REST API auth |

*Required for REST API fast mode. Without these, falls back to MCP.

---

## Feature Specifications

### 1. Smart Search with Precision Detection

**Problem:** Rovo search sometimes returns low-relevance results.

**Solution:** Calculate confidence score and prompt user.

```python
def smart_search(query: str) -> SearchResult:
    results = rovo_search(query)
    confidence = calculate_confidence(query, results)

    if confidence < 0.6:
        return SearchResult(
            results=results,
            suggestion="搜尋結果可能不夠精準，要試試 CQL 精確搜尋嗎？",
            cql_preview=f'title ~ "{query}" OR text ~ "{query}"'
        )

    return SearchResult(results=results)

def calculate_confidence(query: str, results: list) -> float:
    """
    Confidence factors:
    - Title exact match count
    - Keyword overlap ratio
    - Result count reasonableness (too many = too broad)
    """
    if not results:
        return 0.0

    query_words = set(query.lower().split())

    title_matches = sum(
        1 for r in results
        if query.lower() in r['title'].lower()
    )

    # High confidence if query appears in titles
    if title_matches >= 3:
        return 0.9
    elif title_matches >= 1:
        return 0.7

    # Low confidence if too many generic results
    if len(results) > 50:
        return 0.4

    return 0.5
```

### 2. Short URL Resolution

**Problem:** Confluence short URLs (`/wiki/x/ZQGBfg`) need decoding.

**Solution:** Local Base64 decoding before API call.

```python
import re
import base64
from typing import Optional, Dict

def resolve_confluence_url(url: str) -> Dict[str, str]:
    """
    Resolve various Confluence URL formats to page ID.

    Supported formats:
    - Short URL: /wiki/x/ZQGBfg
    - Full URL: /spaces/SPACE/pages/123456/Title
    - Direct page ID: 123456
    """
    # Short URL format (TinyUI)
    tiny_match = re.search(r'/wiki/x/([A-Za-z0-9_-]+)', url)
    if tiny_match:
        tiny_code = tiny_match.group(1)
        page_id = decode_tiny_url(tiny_code)
        return {"type": "page_id", "value": str(page_id)}

    # Full URL format
    page_match = re.search(r'/pages/(\d+)', url)
    if page_match:
        return {"type": "page_id", "value": page_match.group(1)}

    # Direct page ID
    if url.isdigit():
        return {"type": "page_id", "value": url}

    return {"type": "unknown", "value": url}

def decode_tiny_url(tiny_code: str) -> int:
    """
    Decode Confluence TinyUI format to page ID.

    Example: 'ZQGBfg' -> 2122383717
    """
    # Add padding for Base64
    padded = tiny_code + '=='
    # Convert URL-safe Base64 to standard
    standard = padded.replace('-', '+').replace('_', '/')
    # Decode and convert to integer
    decoded = base64.b64decode(standard)
    page_id = int.from_bytes(decoded, 'big')
    return page_id
```

### 3. MCP Fallback with Speed Warning

**Problem:** Users unaware of MCP's slow write performance.

**Solution:** Warn before slow operations, suggest API token setup.

```python
def execute_write_operation(page_id: str, content: str) -> Result:
    has_token = bool(os.getenv("CONFLUENCE_API_TOKEN"))

    if has_token:
        # Fast path: REST API (~1 second)
        return rest_api_write(page_id, content)
    else:
        # Slow path: MCP (~26 seconds)
        print("⚠️  使用 MCP 寫入約需 26 秒")
        print("    設定 CONFLUENCE_API_TOKEN 可加速 25 倍")
        print("    參考: https://id.atlassian.com/manage-profile/security/api-tokens")
        print()

        return mcp_write(page_id, content)
```

### 4. Token Expiry Handling

**Problem:** MCP token expires every 55 minutes.

**Solution:** Silent fallback to REST API when available.

```python
def handle_mcp_failure(operation: str, params: dict, error: Exception) -> Result:
    """Handle MCP failures with graceful degradation."""

    has_token = bool(os.getenv("CONFLUENCE_API_TOKEN"))

    if "Session not found" in str(error) or "token expired" in str(error).lower():
        if has_token:
            # Silent fallback to REST API
            log("MCP session expired, using REST API")
            return execute_rest_api(operation, params)
        else:
            # Prompt user to re-authenticate
            return Result(
                success=False,
                error="MCP session 已過期",
                suggestion="請執行 /mcp 重新認證 Atlassian"
            )

    # Other errors: propagate
    raise error
```

---

## Implementation Tasks

### Priority 0 (Core)

| Task | Description | Files |
|------|-------------|-------|
| ENV-001 | Rename `CONFLUENCE_USERNAME` → `CONFLUENCE_USER` | `upload_confluence.py`, `download_confluence.py`, `confluence_adf_utils.py` |
| ROUTE-001 | Implement basic routing logic | New: `confluence_router.py` |
| ROUTE-002 | Add credential detection | `confluence_router.py` |

### Priority 1 (Enhanced UX)

| Task | Description | Files |
|------|-------------|-------|
| URL-001 | Implement short URL decoder | New: `url_resolver.py` |
| URL-002 | Integrate URL resolution into router | `confluence_router.py` |
| SEARCH-001 | Implement confidence scoring | New: `smart_search.py` |
| SEARCH-002 | Add precision warning prompt | `smart_search.py` |

### Priority 2 (Polish)

| Task | Description | Files |
|------|-------------|-------|
| WARN-001 | Add MCP write speed warning | `confluence_router.py` |
| FALL-001 | Implement MCP → REST API fallback | `confluence_router.py` |
| FALL-002 | Add token expiry detection | `confluence_router.py` |
| DOC-001 | Update RESEARCH.md with final design | `RESEARCH.md` |

---

## API Comparison Reference

### Format Support

| Format | MCP | REST API | Notes |
|--------|-----|----------|-------|
| **Markdown** | ✅ Server-side conversion | ❌ Not supported | MCP exclusive |
| **ADF** | ✅ `contentFormat: "adf"` | ✅ `atlas_doc_format` | Both support |
| **Storage HTML** | ❌ Not supported | ✅ `representation: "storage"` | REST exclusive |
| **Wiki Markup** | ❌ Not supported | ✅ `representation: "wiki"` | REST exclusive |

### Performance (Same Markdown Content)

| Method | Processing | Time |
|--------|------------|------|
| **REST API** | Client-side conversion (mistune) | **1.02 sec** |
| **MCP** | Server-side Markdown conversion | **25.96 sec** |

**Speed Difference:** REST API is **25.5x faster**

### Feature Comparison

| Feature | REST API | MCP | Winner |
|---------|----------|-----|--------|
| Permanent auth | ✅ API Token | ❌ 55 min OAuth | REST |
| Write speed | ✅ ~1s | ❌ ~26s | REST |
| Attachment upload | ✅ | ❌ | REST |
| Rovo AI search | ❌ | ✅ | MCP |
| Cross-product search | ❌ | ✅ | MCP |
| Zero config | ❌ | ✅ | MCP |

---

## Testing Plan

### Test Matrix

| Test Case | Has Token | Operation | Expected Result |
|-----------|-----------|-----------|-----------------|
| T-001 | ✅ | Read page | REST API used |
| T-002 | ❌ | Read page | MCP used |
| T-003 | ✅ | Write page | REST API (~1s) |
| T-004 | ❌ | Write page | MCP (~26s) + warning |
| T-005 | ✅ | Rovo search | MCP used (exclusive) |
| T-006 | ❌ | CQL search | MCP used |
| T-007 | ✅ | Short URL `/wiki/x/...` | Decode + REST API |
| T-008 | ❌ | MCP expired | Prompt re-auth |
| T-009 | ✅ | MCP expired | Silent fallback to REST |

### Validation Commands

```bash
# Test URL resolution
python url_resolver.py "https://site.atlassian.net/wiki/x/ZQGBfg"
# Expected: {"type": "page_id", "value": "2122383717"}

# Test routing (with token)
CONFLUENCE_API_TOKEN=xxx python confluence_router.py read 123456
# Expected: Using REST API...

# Test routing (without token)
unset CONFLUENCE_API_TOKEN && python confluence_router.py read 123456
# Expected: Using MCP...
```

---

## Success Metrics

### Quantitative

- **Write Speed (with token):** <2 seconds (target: ~1s)
- **Fallback Success Rate:** >95%
- **URL Resolution Accuracy:** 100%

### Qualitative

- ✅ Users never manually choose API
- ✅ Clear feedback on which API is used
- ✅ Actionable suggestions for slow operations
- ✅ Seamless fallback on failures

---

## Future Considerations

### Out of Scope (This Version)

1. **CONFLUENCE_SPACE default:** Auto-select space for new pages
2. **Batch operations:** Parallel writes with progress tracking
3. **Caching layer:** Cache frequently accessed pages
4. **MCP token refresh:** Auto-refresh before expiry (blocked by Atlassian bug)

### Long-Term Vision

This design enables:
- Plugin system for additional Atlassian products (Jira, Bitbucket)
- Multi-account support (personal + work)
- Offline mode with sync

---

**Last Updated:** 2026-01-26
**Status:** Draft - Pending Review
