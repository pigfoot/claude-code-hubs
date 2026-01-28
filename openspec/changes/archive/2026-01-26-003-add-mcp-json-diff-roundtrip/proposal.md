# Change: Add MCP + JSON Diff Roundtrip for Confluence (Method 6)

## Why

Existing roundtrip methods for editing Confluence pages face a fundamental trade-off: Methods 1-3 allow Claude to edit
content but **lose all macros** (expand, status, page properties, etc.) during Markdown conversion. Method 4 preserves
macros but **cannot use Claude's intelligent editing**. Method 5 attempts auto-detection but adds complexity and still
loses macros for complex edits.

**Method 6 solves this** by preserving macros while enabling Claude to edit all non-macro text content, using a JSON
diff/patch approach.

## What Changes

- **ADDED**: New `confluence-roundtrip` capability spec for the Confluence plugin
- **ADDED**: `MCPJsonDiffRoundtrip` class - main roundtrip controller
- **ADDED**: `ADFTextExtractor` class - extracts text nodes with paths from ADF JSON
  - Supports two modes: skip macro bodies (safe) or include macro bodies (interactive)
- **ADDED**: `SimpleMarkdownConverter` class - converts ADF to Markdown (macros become placeholders)
- **ADDED**: `TextDiffer` class - computes text changes between original and edited content
- **ADDED**: `BackupManager` class - handles backup and rollback operations
- **ADDED**: Interactive macro body editing - detects and asks user before editing macro content
- **ADDED**: Automatic rollback on failure, manual rollback support
- **ADDED**: Implementation script at `plugins/confluence/skills/confluence/scripts/mcp_json_diff_roundtrip.py`

### Key Architecture

```
Original ADF (with macros)
    │
    ├─→ Keep original (for later patching)
    │
    ├─→ Convert to Markdown (macros lost, but OK)
    │       │
    │       ▼
    │   Claude edits Markdown
    │       │
    │       ▼
    │   Diff: find what TEXT changed
    │       │
    └───────┴─→ Apply only text changes to ORIGINAL ADF
                    │
                    ▼
            Patched ADF (macros untouched, text updated)
```

## Impact

- **Affected specs**: New capability `confluence-roundtrip`
- **Affected code**: `plugins/confluence/skills/confluence/scripts/`
- **Dependencies**: MCP Atlassian plugin (already configured)
- **No breaking changes**: This is an additive feature

## Scope

This proposal covers:

- Spec for roundtrip editing requirements
- Design for Method 6 implementation
- Implementation tasks
- Interactive macro body editing with user confirmation
- Backup and rollback mechanisms

This proposal does NOT cover:

- Changes to existing Methods 1-5 (they remain available)
- CI/CD integration (future enhancement)
- Multi-page batch operations (use Method 1 for that)
