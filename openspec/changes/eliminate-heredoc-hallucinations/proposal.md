# Change Proposal: Eliminate Heredoc Hallucinations

## Summary

Eliminate AI hallucinations in nano-banana plugin by replacing dynamic heredoc code generation with a fixed Python script approach for all image generation tasks.

## Problem

**Current Issue:** When generating 1-4 images, Claude dynamically writes heredoc Python code, which frequently produces hallucinations (30-40% failure rate):
- Non-existent parameters like `api_version`
- Incorrect model names (e.g., `gemini-3-pro-image` missing `-preview` suffix)
- Wrong API method signatures
- Mixing Gemini and Imagen API patterns
- Windows encoding issues with Unicode characters

**Why Heredocs Fail:**
- Claude must recall exact API method names, parameter names, model names
- Training data may contain outdated or incorrect examples
- Similar APIs get conflated (Gemini vs Imagen)
- Parameter names sound plausible but don't exist

**Success Rate:**
- Heredocs (1-4 images): 60-70% success
- Batch mode (5+ images): 99% success (only user error, no AI error)

**Root Cause:** Code generation requires precise recall of technical details, while data generation (JSON config) has no such requirement.

## Solution

**Core Principle:** Claude generates data (JSON config), not code (Python scripts).

**Key Changes:**
1. **Rename Script:** `generate_batch.py` → `generate_images.py` (semantic clarity)
2. **Unified Workflow:** All image generation (1-100 images) uses the same fixed script
3. **Simplify Config:** Remove `model` field; Claude only generates `slides` and `output_dir`
4. **Cross-Platform Paths:** Force relative paths, use `tempfile.gettempdir()` for temp files
5. **Remove Heredoc Docs:** Delete `gemini-api.md`, `imagen-api.md` reference files
6. **Rewrite SKILL.md:** Remove all heredoc examples, document unified workflow

## Impact

**Benefits:**
- ✅ Zero AI hallucinations (99% → 100% success rate for AI-generated parts)
- ✅ Consistent behavior across all slide counts
- ✅ Cross-platform compatibility (Windows/Linux/macOS)
- ✅ Simplified mental model (one workflow vs two)
- ✅ Easier maintenance (one script to update)

**Trade-offs:**
- Single-image generation now requires JSON config step (slight overhead)
- Config-based approach less "magical" than inline heredocs
- Breaking change: users/docs referencing old script name

## Scope

### In Scope

**Code Changes:**
1. Rename `generate_batch.py` to `generate_images.py`
2. Remove `config.get('model')` from model selection logic
3. Replace `/tmp/` hardcoded paths with `tempfile.gettempdir()`
4. Add `output_dir` validation to reject absolute paths

**Documentation Changes:**
1. Delete `references/gemini-api.md` (heredoc examples only)
2. Delete `references/imagen-api.md` (heredoc examples only)
3. Rewrite `SKILL.md` (remove all heredoc sections, add unified workflow)
4. Update `references/batch-generation.md` (script name, path examples)
5. Update `README.md` (usage examples)
6. Review `references/guide.md` (check for heredoc patterns)

### Out of Scope

- No changes to API integration logic (Gemini/Imagen detection, generation code)
- No changes to logo overlay functionality
- No changes to progress tracking mechanism
- No changes to error handling patterns
- No new features beyond eliminating heredocs

## Affected Specs

### Modified Specs

**batch-generation:**
- Remove "5+ slides" threshold requirement
- Update to reflect unified workflow for all slide counts
- Update script name references

### New Specs

**unified-generation:**
- Single workflow for all image generation tasks
- JSON config + fixed script pattern
- Cross-platform path handling

**config-simplification:**
- Minimal required fields (slides, output_dir)
- Model selection via environment variable only
- Relative path enforcement

### Related Specs (No Changes)

- logo-overlay: Logo functionality unchanged
- brand-styling: Style detection unchanged
- error-handling: Error patterns unchanged
- progress-tracking: Progress mechanism unchanged

## Dependencies

**None.** This change is self-contained within the nano-banana plugin.

## Risks

### Low Risk

- File rename: Simple, can use symlink for backward compatibility if needed
- Model priority change: Improves safety, minimal user impact
- Path validation: Catches errors early, improves UX

### Medium Risk

- Documentation rewrite: Large scope but low technical risk
- Removing reference files: Users may bookmark these URLs

### Mitigation

1. Add migration notice in README.md
2. Comprehensive test matrix across Windows/Linux/macOS
3. Keep archived copies of removed files in docs/plans/
4. Communicate breaking changes clearly in changelog

## Success Criteria

1. ✅ Zero hallucinations in image generation workflow (measured by no API parameter errors)
2. ✅ Single Python script handles 1-100 images consistently
3. ✅ Config contains only user-visible fields (no model parameter)
4. ✅ Works on Windows, Linux, and macOS (validated via test matrix)
5. ✅ All documentation updated, no heredoc examples remain
6. ✅ Validation passes: `openspec validate eliminate-heredoc-hallucinations --strict`

## Implementation Plan

See [tasks.md](./tasks.md) for detailed task breakdown.

**High-Level Phases:**
1. **Phase 1:** Script updates (rename, model logic, path handling)
2. **Phase 2:** Documentation updates (remove heredocs, rewrite SKILL.md)
3. **Phase 3:** Testing (cross-platform validation)

**Estimated Effort:** 2-3 development sessions

## References

- **Design Document:** `/docs/plans/003-eliminate-heredoc-hallucinations/design.md`
- **Current Script:** `/plugins/nano-banana/skills/nano-banana/generate_batch.py`
- **Main Skill Doc:** `/plugins/nano-banana/skills/nano-banana/SKILL.md`
