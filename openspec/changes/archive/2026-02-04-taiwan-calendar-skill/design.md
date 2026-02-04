## Context

Claude Code users frequently need date/working day information, but Claude often makes mistakes due to knowledge
cutoff. The existing `mcp-taipei-metro-month-price` project has similar implementation for reference, but it's tied to
MCP Server architecture with complex caching logic.

This project adopts Claude Code Skill architecture, querying government API via Python script in real-time, solving
the problem in a simple, portable way.

## Goals / Non-Goals

**Goals:**

- Provide accurate Taiwan working day/holiday information
- Support basic queries (today, specific date), range queries, and advanced calculations
- Cross-platform support (macOS/Linux/Windows)
- Portable design that can be copied to other projects
- Use `uv run --managed-python` without requiring Python pre-installation

**Non-Goals:**

- No lunar calendar or 24 solar terms support
- No support for regions outside Taiwan
- No MCP Server integration (Claude Code Skill only)
- No complex cache invalidation logic

## Decisions

### 1. Python Script + CLI Interface

**Choice**: Single Python script with CLI subcommands

**Alternatives considered**:

- TypeScript (consistent with existing TPASS project) → but skill ecosystem is Python-centric
- Inline code in SKILL.md → error-prone and hard to maintain

**Rationale**: Python has rich date handling libraries, and `uv run --managed-python` ensures consistent execution environment.

### 2. Data Source: Government Open Data Platform

**Choice**: Prioritize data.gov.tw administrative calendar API

**Fallback**: New Taipei City open data platform

**Rationale**: Official data is most authoritative with standardized format.

### 3. Caching Strategy: Micro Local Cache

**Choice**: Use `tempfile.gettempdir()` with 1-hour expiry

**Alternatives considered**:

- No cache → requires network request every time, too slow
- Long-term cache (30 days) → might miss sudden make-up workday adjustments
- In-memory cache → requires re-fetching on every execution

**Rationale**: 1 hour is a balance—short enough to keep data fresh, long enough to avoid repeated requests.

### 4. Output Format: Plain Text Natural Language

**Choice**: Output Chinese natural language results directly

**Alternative**: JSON structured output → Claude needs extra parsing

**Rationale**: Claude can directly use output to reply to users, reducing one layer of processing.

### 5. CLI Subcommand Design

```
taiwan_calendar.py today                    # Today's info
taiwan_calendar.py check <date>             # Check specific date
taiwan_calendar.py range <start> <end>      # Working days in range
taiwan_calendar.py add-days [date] <n>      # N working days later
taiwan_calendar.py next-working [date]      # Next working day
taiwan_calendar.py next-holiday [date]      # Next holiday
```

## Risks / Trade-offs

### [Risk] Government API unavailable

→ **Mitigation**: Provide fallback API source + clear error message to users

### [Risk] Cross-year data missing

→ **Mitigation**: Dynamically fetch current year and required year data

### [Risk] Cache file permission issues

→ **Mitigation**: Use system temp directory to ensure write permissions

### [Trade-off] No offline support

→ Simplified implementation, accepting network dependency

### [Trade-off] External API dependency

→ Government API is the most authoritative source, accepting this dependency
