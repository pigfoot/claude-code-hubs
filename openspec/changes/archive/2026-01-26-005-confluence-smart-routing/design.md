# Design: Confluence Smart Routing

> Full technical design document: `docs/plans/005-confluence-smart-routing/design.md`

## Architecture Overview

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

## Key Design Decisions

### 1. Environment Variable Naming

**Decision:** Use `CONFLUENCE_USER` instead of `CONFLUENCE_USERNAME`

**Rationale:**

- Follows industry convention (`DB_USER`, `MYSQL_USER`, `POSTGRES_USER`)
- Shorter and cleaner
- Consistent with other environment variables

### 2. Routing Priority

**Decision:** REST API is primary when credentials available, MCP as fallback

**Rationale:**

- REST API is 25x faster for writes (1s vs 26s)
- REST API has permanent authentication (no 55-min expiry)
- MCP provides zero-config experience for users without API token
- Rovo search remains MCP-exclusive (no REST API alternative)

### 3. URL Resolution Strategy

**Decision:** Local Base64 decoding for short URLs

**Rationale:**

- No network call needed for URL resolution
- Works offline
- Handles all Confluence URL formats consistently

### 4. Search Confidence Scoring

**Decision:** Confidence threshold of 0.6 for prompting CQL alternative

**Rationale:**

- Based on empirical testing with Rovo vs CQL searches
- Low threshold avoids excessive prompts
- User can always choose to ignore suggestion

## Component Relationships

```
┌─────────────────────────────────────────────────────────┐
│                    confluence_router.py                  │
│  - detect_credentials()                                 │
│  - route_request()                                      │
│  - handle_fallback()                                    │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ url_resolver │    │ smart_search │    │  Existing    │
│    .py       │    │    .py       │    │  Scripts     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Trade-offs Considered

| Aspect | Choice | Alternative | Why Chosen |
|--------|--------|-------------|------------|
| Auth detection | Check env vars | Read Keychain | Simpler, cross-platform |
| URL decoding | Local Base64 | API call | Faster, offline capable |
| Fallback trigger | Error pattern matching | Proactive expiry check | More reliable, less overhead |
| Warning UX | Chinese + English | Config language | Better local UX |

## Performance Targets

| Metric | Target | Measured |
|--------|--------|----------|
| REST API write | <2s | 1.02s |
| MCP write | ~26s | 25.96s |
| URL resolution | <10ms | N/A (TBD) |
| Fallback success | >95% | N/A (TBD) |
