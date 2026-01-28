# Proposal: Implement Batch Generation for Multi-Slide Workflows

**Change ID:** `001-implement-batch-generation`
**Status:** Draft
**Author:** pigfoot
**Created:** 2026-01-16

## Why

Generating multiple images (e.g., 10 slides) consumes 1,500-2,000 tokens in conversation context, reducing available
space for conversation and limiting usability for long presentations.

## What Changes

- Add batch generation mode for 5+ slides using Background Bash + Progress File
- Create `generate_batch.py` script for batch processing with progress tracking
- Update nano-banana SKILL.md with batch mode detection and workflow
- Add progress polling mechanism (10-15s intervals)
- Implement comprehensive error handling with partial success support
- Maintain backward compatibility for 1-4 slides (direct execution)

## Impact

- **Affected specs:** batch-generation (new), progress-tracking (new), error-handling (new)
- **Affected code:**
  - `plugins/nano-banana/skills/nano-banana/SKILL.md` - add batch mode logic
  - `plugins/nano-banana/skills/nano-banana/references/batch-generation.md` - new reference doc
  - New Python script: `generate_batch.py`
- **Context consumption:** 80% reduction (1,800 → 390 tokens for 10 slides)
- **User experience:** Progress visibility, robust error handling, automatic mode selection

## Problem Statement

When generating multiple images (e.g., 10 slides for a presentation) with nano-banana, each image's output accumulates
in the conversation context:

- **Current behavior:** Execute Python script 10 times → 1,500-2,000 tokens in context
- **Impact:** Context window fills quickly, reducing available space for conversation
- **User pain:** Long presentations consume excessive conversation context

## Proposed Solution

Implement **Background Bash + Progress File** approach for generating 5+ images:

1. **Batch Configuration:** Create JSON config with all slide specifications
2. **Background Execution:** Run Python script with `Bash(run_in_background=True)`
3. **Progress Tracking:** Script writes progress to `/tmp/nano-banana-progress.json`
4. **Periodic Polling:** Claude polls progress file every 10-15 seconds
5. **Result Summary:** Read final results from `/tmp/nano-banana-results.json`

**Context Savings:**

- Current: 1,500-2,000 tokens for 10 slides
- Proposed: ~390 tokens for 10 slides (**80% reduction**)

## Success Criteria

1. **Context Reduction:** Achieve <500 tokens for 10-slide generation
2. **Progress Visibility:** User sees periodic progress updates (e.g., "3/10 completed")
3. **Error Handling:** Failed slides are reported with clear error messages
4. **Backward Compatible:** 1-4 slides continue using direct execution (simpler, immediate feedback)
5. **Automatic Switching:** Claude automatically chooses batch mode for 5+ slides

## Out of Scope

- MCP server implementation (future consideration)
- Parallel image generation (sequential is simpler, avoids rate limits)
- Subagent approach (15x higher API cost, unnecessary complexity)

## Dependencies

- Existing nano-banana skill and Python scripts
- `Bash(run_in_background=True)` tool capability
- File I/O for progress/results JSON

## Risk Assessment

**Low Risk:**

- Additive change (doesn't modify existing 1-4 slide behavior)
- Well-defined interface (JSON config + JSON results)
- Proven pattern (background tasks with progress files)

**Mitigation:**

- Comprehensive error handling in Python script
- Fallback to direct execution if background task fails
- Clear user communication about batch mode activation

## Alternatives Considered

See `plugins/nano-banana/README.md` "Multi-Slide Generation: Context Window Optimization" for full analysis:

1. **Subagent Approach:**
   - Context: 1,400 tokens (30% better)
   - Total API cost: 32,000 tokens (+1,500%)
   - **Rejected:** Cost prohibitive

2. **Direct Execution (Current):**
   - Context: 1,800 tokens
   - Simple but accumulates quickly
   - **Keep for 1-4 slides**

3. **Background Bash (Selected):**
   - Context: 390 tokens (80% better)
   - No additional API cost
   - **Best balance of simplicity, cost, and performance**
