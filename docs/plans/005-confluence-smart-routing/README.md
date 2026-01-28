# 005: Confluence Smart Routing

## Summary

Intelligent API routing for the Confluence plugin that automatically selects between MCP and REST API based on operation
type, available credentials, and performance requirements.

## Problem

- MCP has 55-minute token expiry and 26-second write times
- REST API requires manual configuration but is 25x faster
- Users must manually choose which API to use
- No graceful fallback when one API fails

## Solution

Smart router that:

1. Auto-detects available credentials (`CONFLUENCE_API_TOKEN`)
2. Routes to optimal API per operation type
3. Falls back gracefully on failures
4. Warns users about slow operations

## Key Features

| Feature | Priority | Status |
|---------|----------|--------|
| Environment variable standardization (`CONFLUENCE_USER`) | P0 | Pending |
| Basic routing logic | P0 | Pending |
| Short URL resolution (`/wiki/x/...`) | P1 | Pending |
| Smart search with precision detection | P1 | Pending |
| MCP write speed warning | P2 | Pending |
| Token expiry fallback | P2 | Pending |

## Routing Decision

| Operation | Has API Token | No Token |
|-----------|---------------|----------|
| Read | REST API | MCP |
| Search (CQL) | REST API | MCP |
| Search (Rovo) | MCP | MCP |
| Write | REST API (~1s) | MCP (~26s) + ⚠️ |
| Attachment | REST API | ❌ |

## Files

- [design.md](./design.md) - Complete technical specification

## Quick Links

- [RESEARCH.md](/plugins/confluence/RESEARCH.md) - Background research
- [Existing scripts](/plugins/confluence/skills/confluence/scripts/) - Current implementation

---

**Created:** 2026-01-26
**Status:** Draft
