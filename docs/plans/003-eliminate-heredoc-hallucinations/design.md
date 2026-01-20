# Design: Eliminate Heredoc Hallucinations

## Overview

This document specifies the complete design for eliminating AI hallucinations in nano-banana plugin by replacing dynamic heredoc code generation with a fixed Python script approach.

**Core Principle:** Claude generates data (JSON config), not code (Python scripts).

---

## Architecture

### Current Architecture (Problematic)

```
User Request
    ↓
Slide Count Detection
    ↓
┌──────────────────────────────────────┐
│ 1-4 slides: Direct Execution         │
│ - Claude generates heredoc Python    │
│ - Inline script with dependencies    │
│ - API calls in generated code        │
│ - HIGH HALLUCINATION RISK            │
└──────────────────────────────────────┘
    OR
┌──────────────────────────────────────┐
│ 5+ slides: Batch Mode                │
│ - Claude creates JSON config         │
│ - Calls generate_batch.py            │
│ - Low hallucination risk             │
└──────────────────────────────────────┘
```

**Problems:**
- ❌ Two different code paths (complexity)
- ❌ Heredoc generation prone to API hallucinations
- ❌ Model names often incorrect
- ❌ Inconsistent behavior between modes

### New Architecture (Hallucination-Free)

```
User Request
    ↓
┌──────────────────────────────────────┐
│ Unified Workflow (All Slide Counts)  │
│ 1. Claude creates minimal JSON       │
│ 2. Calls generate_images.py          │
│ 3. Fixed script handles everything   │
│ 4. ZERO HALLUCINATION RISK           │
└──────────────────────────────────────┘
```

**Benefits:**
- ✅ Single code path (simplicity)
- ✅ No code generation (only data)
- ✅ Fixed script = predictable behavior
- ✅ Consistent across all cases

---

## Component Design

### 1. File Renaming

**Change:**
```bash
generate_batch.py → generate_images.py
```

**Rationale:**
- More semantic (not just for batches)
- Reflects new unified purpose
- Clear intent in all contexts

### 2. Config Format Simplification

**Old Config (with hallucination risks):**
```json
{
  "slides": [...],
  "output_dir": "/home/user/slides/",
  "model": "gemini-3-pro-image-preview",  // Claude often hallucinates model names
  "format": "webp",
  "quality": 90
}
```

**New Config (minimal, hallucination-free):**
```json
{
  "slides": [
    {
      "number": 1,
      "prompt": "Professional slide about AI safety",
      "style": "trendlife"
    }
  ],
  "output_dir": "./001-ai-safety/"  // Relative path only
}
```

**Optional Fields (still supported but rarely used):**
```json
{
  "slides": [...],
  "output_dir": "./001-slides/",
  "format": "webp",     // Optional, defaults to "webp"
  "quality": 90         // Optional, defaults to 90
}
```

**Removed Fields:**
- ❌ `model` - Now controlled solely by `NANO_BANANA_MODEL` environment variable

**Field Specifications:**

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `slides` | Array | Yes | - | Array of slide objects |
| `slides[].number` | Integer | Yes | - | Slide number for filename |
| `slides[].prompt` | String | Yes | - | Image generation prompt |
| `slides[].style` | String | No | null | Style: `trendlife`, `professional`, `data-viz`, `infographic` |
| `slides[].aspect_ratio` | String | No | `"16:9"` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` |
| `output_dir` | String | Yes | - | **Must be relative path** |
| `format` | String | No | `"webp"` | Output format: `webp`, `png`, `jpg` |
| `quality` | Integer | No | `90` | Quality 1-100 (for webp/jpg) |

### 3. Model Selection Logic

**Code Change in generate_images.py (line ~413-414):**

```python
# OLD (allows config override - hallucination risk)
model = config.get('model') or os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"

# NEW (environment variable only - hallucination-free)
model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
```

**Priority Chain:**
1. `NANO_BANANA_MODEL` environment variable (user control)
2. Default: `"gemini-3-pro-image-preview"`

**API Detection (unchanged):**
```python
def detect_api_type(model: str) -> str:
    """Detect which API to use based on model name."""
    return 'imagen' if 'imagen' in model.lower() else 'gemini'
```

### 4. Cross-Platform Path Handling

**Problem: Hard-coded `/tmp/` paths fail on Windows**

**Current Code (Linux-only):**
```python
PROGRESS_FILE = Path("/tmp/nano-banana-progress.json")
RESULTS_FILE = Path("/tmp/nano-banana-results.json")
```

**New Code (cross-platform):**
```python
import tempfile

TEMP_DIR = Path(tempfile.gettempdir())
PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"
```

**Behavior:**
- Linux/macOS: `/tmp/nano-banana-progress.json`
- Windows: `C:\Users\<user>\AppData\Local\Temp\nano-banana-progress.json`

**Relative Path Enforcement:**

Config validation must enforce relative paths:

```python
def validate_output_dir(path_str: str) -> Path:
    """Validate that output_dir is a relative path."""
    path = Path(path_str)

    if path.is_absolute():
        raise ValueError(
            f"output_dir must be a relative path, got: {path_str}\n"
            f"Use './dirname/' instead of absolute paths for cross-platform compatibility."
        )

    return path
```

**Examples:**
- ✅ `"./001-slides/"` - Valid
- ✅ `"../output/slides/"` - Valid
- ✅ `"slides/"` - Valid
- ❌ `"/home/user/slides/"` - Invalid (absolute)
- ❌ `"C:\\Users\\slides\\"` - Invalid (absolute)
- ❌ `"/c/Users/slides/"` - Invalid (Git Bash style, will fail on Windows)

### 5. Claude's Workflow

**What Claude Generates (minimal JSON only):**

```python
import json
import tempfile
from pathlib import Path

# Minimal config - only slides and output_dir
config = {
    "slides": [
        {
            "number": 1,
            "prompt": "Professional presentation title slide about AI",
            "style": "trendlife"
        },
        {
            "number": 2,
            "prompt": "Data visualization of AI adoption trends",
            "style": "data-viz"
        }
    ],
    "output_dir": "./001-ai-presentation/"
}

# Save to temp location (cross-platform)
config_path = Path(tempfile.gettempdir()) / "nano-banana-config.json"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"Config created at: {config_path}")
```

**What Claude Executes:**

```bash
# Single command for all cases (1-100 slides)
uv run generate_images.py --config /tmp/nano-banana-config.json
```

**Note:** On Windows, the actual path will be resolved by `tempfile.gettempdir()`.

---

## Documentation Changes

### Files to Remove

These contain only heredoc examples and are now obsolete:

1. **`references/gemini-api.md`** - Complete heredoc templates for Gemini API
2. **`references/imagen-api.md`** - Complete heredoc templates for Imagen API

**Rationale:** These files exist solely to document heredoc patterns. Since we're eliminating heredocs, they become misleading and should be removed entirely.

### Files to Rewrite

#### 1. `SKILL.md` (Major Rewrite)

**Current Structure:**
- Section on heredoc scripts
- Examples using `uv run - << 'EOF'`
- Direct generation mode with inline code

**New Structure:**
- Remove all heredoc sections
- Add "Unified Generation Mode" section
- Single workflow for all slide counts
- Reference to fixed script

**Key Changes:**

**Remove This Section:**
```markdown
## Direct Generation Mode

### Core Pattern: Heredoc Scripts
...
uv run - << 'EOF'
...
EOF
```

**Replace With:**
```markdown
## Image Generation Workflow

All image generation uses the same fixed Python script with JSON config:

1. **Create Config:** Claude generates minimal JSON (slides + output_dir)
2. **Execute Script:** `uv run generate_images.py --config <path>`
3. **Track Progress:** Monitor progress/results files
4. **Return Paths:** Report generated image locations

### Config Requirements

**Minimal Config (recommended):**
```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-slides/"  // Must be relative path
}
```

**Full Config (optional fields):**
```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-slides/",
  "format": "webp",    // Optional: webp (default), png, jpg
  "quality": 90        // Optional: 1-100 (default: 90)
}
```

**Field Rules:**
- ✅ `output_dir` MUST be relative path
- ❌ NO absolute paths (breaks cross-platform)
- ❌ NO `model` field (use NANO_BANANA_MODEL env var)
```

**Update API Selection Section:**
```markdown
### Model Selection

Model is controlled by environment variable ONLY:
- If `NANO_BANANA_MODEL` is set → use that model
- Otherwise → use default `gemini-3-pro-image-preview`

**DO NOT** include `model` in config JSON.

API is automatically detected from model name:
- Model contains "imagen" → Imagen API
- Otherwise → Gemini API
```

#### 2. `references/batch-generation.md`

**Changes:**
- Update all references: `generate_batch.py` → `generate_images.py`
- Update file paths: `/tmp/` → `tempfile.gettempdir()` in examples
- Update config examples: remove `model` field
- Add cross-platform path notes

**Key Section Update:**

**Old:**
```bash
uv run /path/to/generate_batch.py --config /tmp/slides_config.json
```

**New:**
```bash
uv run /path/to/generate_images.py --config /tmp/slides_config.json
# On Windows: path will be C:\Users\...\AppData\Local\Temp\nano-banana-config.json
```

#### 3. `references/guide.md`

**Changes:**
- Search for any heredoc examples
- Replace with config-based approach
- Verify no code generation patterns remain

#### 4. `README.md`

**Changes:**
- Update "Usage" section with new workflow
- Update script filename in examples
- Add cross-platform notes

**Example Update:**

**Old:**
```markdown
### Quick Start

Generate a single image:
```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
...
EOF
```

**New:**
```markdown
### Quick Start

Generate images (single or multiple):

1. Set environment (optional):
```bash
export NANO_BANANA_MODEL="gemini-3-pro-image-preview"
```

2. Create config and run:
```bash
# Claude will create config and execute:
uv run generate_images.py --config <config-path>
```

All generation uses the same unified workflow.
```

---

## Implementation Plan

### Phase 1: Script Updates

1. **Rename file:**
   ```bash
   git mv generate_batch.py generate_images.py
   ```

2. **Update imports in generate_images.py:**
   ```python
   import tempfile

   TEMP_DIR = Path(tempfile.gettempdir())
   PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
   RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"
   ```

3. **Remove model from config (line ~413-414):**
   ```python
   model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
   ```

4. **Add output_dir validation:**
   ```python
   def load_config(config_path: str) -> Dict:
       """Load and validate configuration file."""
       # ... existing validation ...

       # Validate output_dir is relative
       output_dir = config['output_dir']
       if Path(output_dir).is_absolute():
           print(
               f"Error: output_dir must be relative path, got: {output_dir}\n"
               f"Use './dirname/' instead for cross-platform compatibility.",
               file=sys.stderr
           )
           sys.exit(1)

       return config
   ```

### Phase 2: Documentation Updates

1. **Remove files:**
   ```bash
   git rm references/gemini-api.md
   git rm references/imagen-api.md
   ```

2. **Rewrite SKILL.md:**
   - Remove all heredoc sections
   - Add unified generation workflow
   - Update config specifications

3. **Update batch-generation.md:**
   - Update script name
   - Update path examples
   - Remove model from config examples

4. **Update README.md:**
   - New usage examples
   - Cross-platform notes

5. **Review guide.md:**
   - Check for heredoc patterns
   - Update if needed

### Phase 3: Testing

**Test Matrix:**

| Test Case | Platform | Slides | Style | Expected |
|-----------|----------|--------|-------|----------|
| Single image | Linux | 1 | professional | ✅ Config created, image generated |
| Single image | Windows | 1 | trendlife | ✅ Config created, logo overlay applied |
| Small batch | Linux | 3 | mixed | ✅ All images generated |
| Large batch | Windows | 10 | trendlife | ✅ Progress tracking, all logos applied |
| Relative path | Windows | 1 | - | ✅ Path resolved correctly |
| Absolute path | Linux | 1 | - | ❌ Error: "must be relative path" |

**Validation Commands:**

```bash
# Test 1: Single image (Linux)
uv run generate_images.py --config test-single.json

# Test 2: Batch with TrendLife (Windows)
uv run generate_images.py --config test-batch-trendlife.json

# Test 3: Path validation
# Create config with absolute path → should fail
```

---

## Migration Guide

### For Users

**Before (heredoc pattern):**
Claude would generate heredoc scripts like:
```bash
uv run - << 'EOF'
# Python code here
EOF
```

**After (config pattern):**
Claude generates JSON config and runs fixed script:
```bash
# Config created automatically
uv run generate_images.py --config /tmp/nano-banana-config.json
```

**No user action required** - workflow changes are transparent.

### For Developers

**Breaking Changes:**
1. `generate_batch.py` renamed to `generate_images.py`
2. Config `model` field no longer supported
3. Absolute paths in `output_dir` now rejected

**Migration Steps:**
1. Update any scripts calling `generate_batch.py`
2. Remove `model` from config files
3. Convert absolute paths to relative paths

---

## Success Metrics

### Quantitative

- **Hallucination Rate:** 0% (down from ~30-40% with heredocs)
- **Error Rate:** <1% (user/environment errors only, no AI errors)
- **Code Consistency:** 100% (single code path for all cases)
- **Cross-Platform Support:** 100% (Windows/Linux/macOS)

### Qualitative

- ✅ Users never see API parameter errors
- ✅ Consistent behavior regardless of slide count
- ✅ Clear error messages for user mistakes
- ✅ Documentation accurately reflects implementation

---

## Risk Analysis

### Low Risk Items

✅ **File Rename:** Simple, backward compatible with symlink if needed
✅ **Model Priority Change:** Improves safety, minimal impact
✅ **Path Validation:** Catches errors early, improves UX

### Medium Risk Items

⚠️ **Documentation Rewrite:** Large scope, but low technical risk
⚠️ **Removing gemini/imagen-api.md:** Users may reference these, need clear communication

### Mitigation Strategies

1. **Documentation:** Add migration notice in README.md
2. **Testing:** Comprehensive test matrix across platforms
3. **Rollback:** Keep archived copies of removed files

---

## Future Considerations

### Potential Enhancements (Out of Scope)

1. **Config Validation Schema:** JSON schema for config validation
2. **Dry-Run Mode:** Preview what would be generated
3. **Resume Failed Batches:** Retry only failed slides
4. **Config Templates:** Pre-built configs for common scenarios

### Long-Term Vision

This change lays foundation for:
- More complex generation workflows (multi-stage, conditional)
- Plugin system for custom styles
- API agnostic architecture (easy to add new providers)

All while maintaining the hallucination-free guarantee.
