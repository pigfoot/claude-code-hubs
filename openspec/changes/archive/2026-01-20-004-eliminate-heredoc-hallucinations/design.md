# Design: Eliminate Heredoc Hallucinations

## Overview

Replace dynamic heredoc code generation with a fixed Python script approach to eliminate AI hallucinations in the
nano-banana plugin.

**Core Principle:** Claude generates data (JSON config), not code (Python scripts).

**Complete Design Document:** See `/docs/plans/003-eliminate-heredoc-hallucinations/design.md` for full architectural
details.

---

## Architecture

### Current Architecture (Problematic)

```
User Request → Slide Count Detection →
    IF 1-4 slides: Claude generates heredoc Python (HIGH HALLUCINATION RISK)
    IF 5+ slides: Claude creates JSON config, calls generate_batch.py (LOW RISK)
```

**Problems:**

- Two different code paths (complexity)
- Heredoc generation prone to API hallucinations (30-40% failure rate)
- Model names often incorrect
- Windows path/encoding issues

### New Architecture (Hallucination-Free)

```
User Request → Claude creates JSON config →
    Call generate_images.py (fixed script) →
    (ZERO HALLUCINATION RISK)
```

**Benefits:**

- Single code path (simplicity)
- No code generation (only data)
- Fixed script = predictable behavior
- Consistent across all cases

---

## Key Design Decisions

### 1. File Rename

**Change:** `generate_batch.py` → `generate_images.py`

**Rationale:**

- More semantic (handles all cases, not just batches)
- Reflects new unified purpose
- Clear intent in all contexts

### 2. Config Format Simplification

**Minimal Config (required):**

```json
{
  "slides": [
    {"number": 1, "prompt": "...", "style": "trendlife"}
  ],
  "output_dir": "./001-slides/"
}
```

**Optional Fields:**

```json
{
  "format": "webp",     // Default: "webp"
  "quality": 90         // Default: 90
}
```

**Removed Field:**

- ❌ `model` - Now controlled solely by `NANO_BANANA_MODEL` environment variable

**Rationale:** Less for Claude to generate = less chance of hallucination

### 3. Model Selection

**Old Priority:** Config → Environment → Default
**New Priority:** Environment → Default

```python
# OLD (allows config override - hallucination risk)
model = config.get('model') or os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"

# NEW (environment variable only - hallucination-free)
model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
```

**Rationale:** User environment variable should always win; prevents Claude from overriding with hallucinated model
names

### 4. Cross-Platform Path Handling

**Problem:** Hardcoded `/tmp/` paths fail on Windows

**Solution:**

```python
import tempfile

TEMP_DIR = Path(tempfile.gettempdir())
PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"
```

**Behavior:**

- Linux/macOS: `/tmp/nano-banana-progress.json`
- Windows: `C:\Users\<user>\AppData\Local\Temp\nano-banana-progress.json`

### 5. Relative Path Enforcement

**Validation:**

```python
def validate_output_dir(path_str: str) -> Path:
    """Validate that output_dir is a relative path."""
    path = Path(path_str)
    if path.is_absolute():
        raise ValueError("output_dir must be relative path")
    return path
```

**Examples:**

- ✅ `"./001-slides/"` - Valid
- ✅ `"../output/slides/"` - Valid
- ❌ `"/home/user/slides/"` - Invalid (absolute)
- ❌ `"/c/Users/slides/"` - Invalid (Git Bash style on Windows)

**Rationale:** Avoids Git Bash `/c/Users` vs Windows `C:\Users` path conflicts

---

## Claude's Workflow

**What Claude Generates (minimal JSON only):**

```python
import json
import tempfile
from pathlib import Path

config = {
    "slides": [
        {"number": 1, "prompt": "...", "style": "trendlife"}
    ],
    "output_dir": "./001-ai-presentation/"
}

config_path = Path(tempfile.gettempdir()) / "nano-banana-config.json"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
```

**What Claude Executes:**

```bash
uv run generate_images.py --config <config-path>
```

**What Claude NEVER Does:**

- ❌ Generate Python code with API calls
- ❌ Specify model names
- ❌ Use absolute paths
- ❌ Write heredoc scripts

---

## Documentation Strategy

### Files to Remove

**Why:** Contain only heredoc examples, now obsolete

1. `references/gemini-api.md` - Heredoc templates for Gemini API
2. `references/imagen-api.md` - Heredoc templates for Imagen API

### Files to Rewrite

**SKILL.md:**

- Remove: All heredoc sections (~100-150 lines)
- Add: Unified generation workflow section
- Update: API selection to reference environment variable only

**batch-generation.md:**

- Update: Script name references
- Update: Path examples (use `tempfile.gettempdir()`)
- Update: Remove `model` from config examples

**README.md:**

- Replace: Heredoc examples with config-based approach
- Add: Cross-platform usage notes

**guide.md:**

- Review: Check for any remaining heredoc patterns
- Update: If found, replace with config approach

---

## Implementation Phases

### Phase 1: Script Updates (Foundation)

1. Rename file
2. Update model selection logic
3. Add cross-platform temp directory handling
4. Add output directory path validation

### Phase 2: Documentation Updates (Communication)

1. Remove heredoc reference files
2. Rewrite SKILL.md sections
3. Update all script/path references
4. Review and update supporting docs

### Phase 3: Testing (Validation)

1. Test single image (Linux/Windows)
2. Test batch with TrendLife (Windows)
3. Test path validation
4. Test large batch (10 slides)

---

## Testing Strategy

### Test Matrix

| Test Case | Platform | Slides | Style | Expected |
|-----------|----------|--------|-------|----------|
| Single image | Linux | 1 | professional | ✅ Config created, image generated |
| Single image | Windows | 1 | trendlife | ✅ Config created, logo applied |
| Small batch | Linux | 3 | mixed | ✅ All images generated |
| Large batch | Windows | 10 | trendlife | ✅ Progress tracking, logos applied |
| Relative path | Windows | 1 | - | ✅ Path resolved correctly |
| Absolute path | Linux | 1 | - | ❌ Error: "must be relative path" |

### Success Criteria

1. Zero hallucinations (no API parameter errors)
2. Cross-platform compatibility verified
3. All documentation updated
4. Consistent behavior across slide counts
5. Path validation working correctly

---

## Risk Mitigation

### Low-Risk Items

- File rename: Simple, git history preserved
- Model priority change: Safer, user-controlled
- Path validation: Better UX, catches errors early

### Medium-Risk Items

- Documentation rewrite: Large scope, but low technical risk
- Removing reference files: May break bookmarks

### Mitigation Strategies

1. Add migration notice in README.md
2. Keep archived copies in docs/plans/
3. Comprehensive test coverage
4. Clear communication in changelog

---

## Future Considerations

This change lays foundation for:

- Config validation schemas (JSON schema)
- Dry-run mode (preview without execution)
- Resume failed batches (retry logic)
- Plugin system for custom styles

All while maintaining the hallucination-free guarantee.

---

## References

- **Full Design:** `/docs/plans/003-eliminate-heredoc-hallucinations/design.md`
- **Current Script:** `/plugins/nano-banana/skills/nano-banana/generate_batch.py`
- **Main Documentation:** `/plugins/nano-banana/skills/nano-banana/SKILL.md`
