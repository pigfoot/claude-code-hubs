# Design: MCP + JSON Diff Roundtrip (Method 6)

## Context

The Confluence plugin needs to support roundtrip editing: reading a page, allowing Claude to edit it, and writing it back. The challenge is that Confluence pages often contain macros (expand, status, page properties, etc.) that have no Markdown equivalent.

**Current state:**
- Methods 1-3: Use Markdown conversion → Claude edits → lose all macros
- Method 4: Direct XML manipulation → preserves macros → but no Claude intelligence
- Method 5: Auto-detect → complex → still loses macros for complex edits

**Stakeholders:**
- Plugin users who want Claude to edit Confluence pages
- Teams with pages containing important macros (expand panels, status badges, etc.)

## Goals / Non-Goals

**Goals:**
- Preserve all macros during roundtrip editing
- Allow Claude to intelligently edit text content (paragraphs, headings, lists, etc.)
- Use MCP for authentication (OAuth, no API token management)
- Provide predictable, reliable behavior
- Keep implementation simple (~200 lines Python)

**Non-Goals:**
- Edit text INSIDE macro bodies (e.g., content inside expand panels)
- Support batch operations (use Method 1 for that)
- Replace existing methods (Method 6 is an addition)
- Auto-detect when to use Method 6 vs others (keep it explicit)

## Decisions

### Decision 1: Use JSON Diff/Patch approach

**What:** Extract text nodes with their paths from ADF, let Claude edit Markdown version, compute diff, apply only text changes back to original ADF.

**Why:** This is the only way to modify text while leaving macro nodes completely untouched. The macro nodes are never processed, only text nodes are compared and patched.

**Alternatives considered:**
1. **Placeholder syntax in Markdown** - Claude might move/delete/corrupt placeholders; nested macros are complex
2. **Structural ADF diff** - Complex, may still touch macro-adjacent nodes
3. **Use Confluence API's inline editing** - No API support for this

### Decision 2: Use MCP for read/write operations

**What:** Use `mcp__plugin_confluence_atlassian__getConfluencePage` and `updateConfluencePage` tools.

**Why:**
- MCP is already configured in the plugin
- OAuth authentication (no API token management)
- Official Atlassian support
- High-level API (handles version numbers, etc.)

**Alternatives considered:**
1. **REST API directly** - Requires API token, more boilerplate
2. **Third-party MCP** - Less official support

### Decision 3: Simple line-based text matching

**What:** Use line-based comparison with word overlap heuristic (30% threshold) to match original text with edited text.

**Why:** Simple to implement, sufficient for most editing scenarios (typo fixes, sentence rewrites, paragraph additions).

**Alternatives considered:**
1. **Structural diff (difflib.SequenceMatcher)** - More complex, needed for edge cases
2. **LCS-based matching** - Overkill for text-level changes
3. **AI-based semantic matching** - Too expensive, adds latency

**Trade-off:** May have false positives/negatives for heavily restructured content. Users can fall back to Method 1 or Confluence UI for such cases.

### Decision 4: Support interactive macro body editing

**What:** Detect when macros contain editable text content, ask user for confirmation, and optionally include macro bodies in editing scope.

**Why:**
- Method 4 can actually edit macro bodies programmatically
- We can apply the same JSON diff/patch approach to macro body text nodes
- User control: let them decide the risk/benefit trade-off
- Safer than Method 4's direct XML manipulation

**Alternatives considered:**
1. **Always skip macro bodies** - Simpler but limits functionality
2. **Always include macro bodies** - Riskier, no user control
3. **Auto-detect complexity and decide** - Too opaque, users prefer explicit control

**Implementation:**
- Default: skip macro bodies (safe mode)
- When detected: show preview and ask user
- If confirmed: extract text from macro bodies using same path-based approach
- Backup is created regardless, but especially important for macro body edits

### Decision 5: Implement backup and rollback

**What:** Create backup before every edit operation, auto-rollback on failure, support manual rollback.

**Why:**
- Macro body editing adds risk
- Diff/patch algorithm may have edge cases
- Users need confidence to try new features
- Confluence has version history, but manual restoration is tedious

**What to backup:**
- Original ADF JSON
- Page version number
- Timestamp
- Page metadata (title, ID, space)

**Alternatives considered:**
1. **Rely on Confluence version history** - Exists but requires manual restoration
2. **No backup** - Too risky for macro editing
3. **Only backup when editing macro bodies** - Inconsistent UX

## Risks / Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Text matching misses changes | Low | Medium | Use generous overlap threshold (30%); add logging |
| Macro body edit corrupts structure | Low | High | **Backup before edit**; user confirmation; auto-rollback on failure |
| ADF format changes in future | Low | High | Pin to ADF version; monitor Atlassian changelogs |
| Large pages cause slow diffing | Low | Medium | Extract only top-level text nodes; add timeout |
| Backup storage fills disk | Very Low | Low | Set retention policy (keep last 10 backups); add cleanup |
| User accidentally confirms risky edit | Medium | Medium | Show clear preview; require explicit "yes"; suggest safe alternative |

## Migration Plan

No migration needed - this is an additive feature.

**Rollout:**
1. Implement core classes in `scripts/mcp_json_diff_roundtrip.py`
2. Add integration tests
3. Update SKILL.md with usage instructions
4. Update reference docs to recommend Method 6

**Rollback:** If issues arise, users can continue using Methods 1-5 unchanged.

## Open Questions

1. **Q: Should we allow editing macro body content?**
   A: ✅ **Resolved** - Yes, with user confirmation and backup/rollback. Default is safe mode (skip macro bodies).

2. **Q: What's the minimum Python version?**
   A: 3.9+ (uses typing features like `list[...]`)

3. **Q: Should we support Storage Format in addition to ADF?**
   A: Not in v1. MCP returns ADF natively. Storage Format support can be added later if needed.

4. **Q: Where should backups be stored?**
   A: In `.confluence_backups/` directory under the plugin root. Structure: `{page_id}/{timestamp}.json`

5. **Q: How many backups should we keep?**
   A: Default: last 10 per page. Configurable via environment variable `CONFLUENCE_BACKUP_LIMIT`.
