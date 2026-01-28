# 003: Eliminate Heredoc Hallucinations in Nano Banana Plugin

## Project Overview

Eliminate AI hallucinations in nano-banana plugin by replacing dynamic heredoc code generation with a fixed Python
script approach for all image generation tasks.

## Problem Statement

### Current Issue

When generating 1-4 images, Claude dynamically writes heredoc Python code, which frequently produces hallucinations:

- Non-existent parameters like `api_version`
- Incorrect model names (e.g., inventing model variants that don't exist)
- Wrong API method signatures
- Mixing Gemini and Imagen API patterns

### Root Cause: Why Heredocs Cause Hallucinations

**The Fundamental Problem:**

When Claude generates code (heredoc scripts), it must recall:

1. Exact API method names (`generate_content` vs `generate_images`)
2. Exact parameter names (`response_modalities` vs `output_mime_type`)
3. Exact model names (`gemini-3-pro-image-preview` with the `-preview` suffix)
4. Correct config class for each API (`GenerateContentConfig` vs `GenerateImagesConfig`)
5. API-specific patterns (Gemini uses `contents=[]` array, Imagen uses `prompt=` string)

**Why This Fails:**

- Claude's training data may contain outdated or incorrect API examples
- Similar-looking APIs get conflated (Gemini vs Imagen confusion)
- Parameter names are "plausible" but wrong (e.g., `api_version` sounds reasonable but doesn't exist)
- Long SKILL.md with many examples → Claude mixes patterns from different sections

**Real Examples from User Reports:**

```python
# Hallucination 1: Non-existent parameter
response = client.models.generate_content(
    api_version="v1",  # ❌ This parameter doesn't exist!
    model=model,
    contents=[prompt]
)

# Hallucination 2: Wrong model name
model = "gemini-3-pro-image"  # ❌ Missing -preview suffix
# Correct: "gemini-3-pro-image-preview"

# Hallucination 3: Mixing APIs
response = client.models.generate_images(  # Imagen API method
    model="gemini-3-pro-image-preview",    # ❌ Gemini model with Imagen API!
    contents=[prompt]  # ❌ Imagen uses prompt= not contents=
)

# Issue 4: Windows encoding problems (not AI error, but heredoc-specific)
print(f"  ✓ {output_path.name}")
# ❌ UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
# Windows PowerShell/cmd uses cp1252 encoding by default
# Every heredoc generation risks this issue
# Fixed script can set UTF-8 encoding once at start
```

### Why Batch Mode Works

When generating 5+ images, Claude doesn't write code - it writes **data** (JSON config):

```json
{
  "slides": [{"number": 1, "prompt": "..."}],
  "output_dir": "./001-slides/"
}
```

**No hallucinations because:**

- ✅ No API method names to remember
- ✅ No parameter names to recall
- ✅ No model names to spell correctly
- ✅ Fixed `generate_batch.py` handles all technical details

**Success Rate:**

- Heredocs (1-4 images): ~60-70% success (30-40% hallucination rate)
- Batch mode (5+ images): ~99% success (only user error, no AI error)

### Impact

**User Experience:**

- 😤 Frustration from cryptic Python errors
- ⏰ Time wasted debugging AI-generated code
- 🔄 Multiple retry attempts needed
- 📉 Loss of trust in the tool

**Technical Debt:**

- Inconsistent behavior between single and batch modes
- Documentation must track two different workflows
- Harder to maintain (heredoc examples in docs get outdated)

## Goals

1. **Eliminate Hallucinations:** Remove all heredoc code generation to prevent parameter/API hallucinations
2. **Unify Workflow:** Use the same fixed Python script for single and batch image generation
3. **Simplify Config:** Minimize config fields that Claude needs to generate
4. **Cross-Platform Support:** Ensure Windows/Linux/macOS compatibility with proper path handling

## Solution Approach

Replace heredoc pattern with fixed script + minimal JSON config:

- Rename `generate_batch.py` → `generate_images.py` (semantic clarity)
- Claude only generates minimal JSON config (slides + output_dir)
- All technical details (model, API selection) handled by fixed script
- Use relative paths and `tempfile.gettempdir()` for cross-platform support

## Documentation Structure

- **[design.md](./design.md)** - Complete design specification
  - Architecture changes
  - Config format simplification
  - Path handling strategy
  - Documentation update plan

## Timeline

- Brainstorming phase: 2026-01-20 ✅
- Design phase: 2026-01-20 (In progress)
- Implementation phase: TBD
- Testing phase: TBD

## Success Criteria

- ✅ Zero hallucinations in image generation workflow
- ✅ Single Python script handles all cases (1-100 images)
- ✅ Config contains only user-visible fields
- ✅ Works on Windows, Linux, and macOS
- ✅ All documentation updated and heredoc examples removed

## Related Files

**Scripts:**

- `plugins/nano-banana/skills/nano-banana/generate_batch.py` → Will be renamed to `generate_images.py`
- `plugins/nano-banana/skills/nano-banana/logo_overlay.py` (no changes needed)

**Documentation:**

- `plugins/nano-banana/skills/nano-banana/SKILL.md` (major rewrite needed)
- `plugins/nano-banana/skills/nano-banana/references/batch-generation.md` (update paths/names)
- `plugins/nano-banana/skills/nano-banana/references/gemini-api.md` (to be removed)
- `plugins/nano-banana/skills/nano-banana/references/imagen-api.md` (to be removed)
- `plugins/nano-banana/skills/nano-banana/references/guide.md` (check for heredoc examples)
- `plugins/nano-banana/README.md` (update usage examples)

## Key Design Decisions

### 1. Remove `model` from Config

**Decision:** Model selection via environment variable only
**Rationale:** Prevents Claude from hallucinating model names

### 2. Force Relative Paths

**Decision:** Config only accepts relative paths (e.g., `./001-slides/`)
**Rationale:** Avoids Git Bash `/c/Users` vs Windows `C:\Users` path conflicts

### 3. Single Script for All Cases

**Decision:** No separate logic for 1-4 vs 5+ images
**Rationale:** Simplifies mental model, eliminates mode-switching complexity

### 4. Minimal Config

**Decision:** Only `slides` and `output_dir` are required fields
**Rationale:** Less for Claude to generate = less chance of hallucination
