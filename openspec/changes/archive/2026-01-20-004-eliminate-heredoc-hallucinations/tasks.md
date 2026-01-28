# Implementation Tasks

Ordered list of small, verifiable work items for eliminating heredoc hallucinations.

## Phase 1: Script Updates

### Task 1.1: Rename Script File

**Goal:** Rename `generate_batch.py` to `generate_images.py`

**Actions:**

```bash
cd plugins/nano-banana/skills/nano-banana/
git mv generate_batch.py generate_images.py
```

**Validation:**

- File exists at `generate_images.py`
- Old file `generate_batch.py` no longer exists
- Git history preserved

**Dependencies:** None
**Can parallelize:** No (blocking for all subsequent tasks)

---

### Task 1.2: Update Model Selection Logic

**Goal:** Remove config-based model override, use environment variable only

**Actions:**

1. Open `generate_images.py`
2. Find line ~413-414:

   ```python
   model = config.get('model') or os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
   ```

3. Replace with:

   ```python
   model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
   ```

**Validation:**

- `config.get('model')` no longer appears in script
- Model selection uses environment variable first
- Default model is `"gemini-3-pro-image-preview"`

**Dependencies:** Task 1.1
**Can parallelize:** No

---

### Task 1.3: Add Cross-Platform Temp Directory Handling

**Goal:** Replace hardcoded `/tmp/` paths with `tempfile.gettempdir()`

**Actions:**

1. Add import at top of `generate_images.py`:

   ```python
   import tempfile
   ```

2. Replace lines ~46-47:

   ```python
   PROGRESS_FILE = Path("/tmp/nano-banana-progress.json")
   RESULTS_FILE = Path("/tmp/nano-banana-results.json")
   ```

   With:

   ```python
   TEMP_DIR = Path(tempfile.gettempdir())
   PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
   RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"
   ```

**Validation:**

- On Linux/macOS: Files created in `/tmp/`
- On Windows: Files created in `C:\Users\<user>\AppData\Local\Temp\`
- No hardcoded `/tmp/` strings remain

**Dependencies:** Task 1.1
**Can parallelize:** Yes (with Task 1.2)

---

### Task 1.4: Add Output Directory Path Validation

**Goal:** Validate that `output_dir` is a relative path

**Actions:**

1. Add validation function in `generate_images.py` after imports:

   ```python
   def validate_output_dir(path_str: str) -> Path:
       """Validate that output_dir is a relative path."""
       path = Path(path_str)

       if path.is_absolute():
           print(
               f"Error: output_dir must be relative path, got: {path_str}\n"
               f"Use './dirname/' instead for cross-platform compatibility.",
               file=sys.stderr
           )
           sys.exit(1)

       return path
   ```

2. In `load_config()` function (~line 50-94), after validating `output_dir` exists:

   ```python
   # Validate output_dir is relative
   output_dir = config['output_dir']
   validate_output_dir(output_dir)
   ```

**Validation:**

- Config with absolute path (`/home/user/slides/`) → Error message
- Config with relative path (`./slides/`) → Accepted
- Error message is clear and actionable

**Dependencies:** Task 1.1
**Can parallelize:** Yes (with Tasks 1.2, 1.3)

---

## Phase 2: Documentation Updates

### Task 2.1: Remove Heredoc Reference Files

**Goal:** Delete obsolete heredoc example files

**Actions:**

```bash
cd plugins/nano-banana/skills/nano-banana/
git rm references/gemini-api.md
git rm references/imagen-api.md
```

**Validation:**

- Files no longer exist
- Git shows files as deleted

**Dependencies:** None
**Can parallelize:** Yes (with all Phase 1 tasks)

---

### Task 2.2: Rewrite SKILL.md - Remove Heredoc Sections

**Goal:** Remove all heredoc patterns from main skill documentation

**Actions:**

1. Open `SKILL.md`
2. Find and remove sections:
   - "## Direct Generation Mode"
   - "### Core Pattern: Heredoc Scripts"
   - All `uv run - << 'EOF'` examples
3. Remove references to gemini-api.md and imagen-api.md

**Validation:**

- No heredoc examples remain
- No references to deleted reference files
- Word count reduced by ~100-150 lines

**Dependencies:** Task 2.1
**Can parallelize:** No

---

### Task 2.3: Rewrite SKILL.md - Add Unified Workflow Section

**Goal:** Document new unified generation workflow

**Actions:**

1. In `SKILL.md`, add new section after API Selection:

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

**Validation:**

- New section clearly explains unified workflow
- Config examples are minimal and correct
- No model field in examples

**Dependencies:** Task 2.2
**Can parallelize:** No

---

### Task 2.4: Update batch-generation.md References

**Goal:** Update script name and path examples

**Actions:**

1. Open `references/batch-generation.md`
2. Find and replace all:
   - `generate_batch.py` → `generate_images.py`
   - `/tmp/slides_config.json` → `Path(tempfile.gettempdir()) / "nano-banana-config.json"`
3. Remove `model` field from all config examples
4. Add note about cross-platform temp paths

**Validation:**

- All script references updated
- No hardcoded `/tmp/` paths in examples
- Config examples don't include `model` field

**Dependencies:** None
**Can parallelize:** Yes (with all other Phase 2 tasks)

---

### Task 2.5: Update README.md Usage Examples

**Goal:** Replace heredoc examples with config-based approach

**Actions:**

1. Open `README.md`
2. Find "Quick Start" or "Usage" section
3. Replace heredoc examples with:

   ```markdown
   ### Quick Start

   Generate images (single or multiple):

   1. Set environment (optional):
   ```bash
   export NANO_BANANA_MODEL="gemini-3-pro-image-preview"
   ```

   1. Create config and run:

   ```bash
   # Claude will create config and execute:
   uv run generate_images.py --config <config-path>
   ```

   All generation uses the same unified workflow.

   ```

**Validation:**

- No heredoc examples in README
- Examples show config-based approach
- Cross-platform note included

**Dependencies:** None
**Can parallelize:** Yes (with all other Phase 2 tasks)

---

### Task 2.6: Review guide.md for Heredoc Patterns

**Goal:** Ensure no heredoc examples remain

**Actions:**

1. Open `references/guide.md`
2. Search for `uv run -` or `<< 'EOF'`
3. If found, replace with config-based examples or remove

**Validation:**

- No heredoc patterns found
- If examples exist, they use config approach

**Dependencies:** None
**Can parallelize:** Yes (with all other Phase 2 tasks)

---

## Phase 3: Testing

### Task 3.1: Test Single Image Generation (Linux)

**Goal:** Verify single-image workflow on Linux

**Test Case:**

```bash
# Create test config
cat > /tmp/test-single-linux.json << 'EOF'
{
  "slides": [
    {"number": 1, "prompt": "Professional slide about AI", "style": "professional"}
  ],
  "output_dir": "./test-single/"
}
EOF

# Run
uv run generate_images.py --config /tmp/test-single-linux.json
```

**Expected:**

- Config accepted
- Image generated in `./test-single/slide-01.webp`
- No errors

**Dependencies:** All Phase 1 and Phase 2 tasks
**Can parallelize:** Yes (with other platform tests)

---

### Task 3.2: Test Single Image Generation (Windows)

**Goal:** Verify single-image workflow on Windows

**Test Case:**

```powershell
# Create test config
$config = @{
  slides = @(
    @{number=1; prompt="Professional slide about AI"; style="professional"}
  )
  output_dir = "./test-single/"
} | ConvertTo-Json | Out-File -Encoding utf8 test-single-windows.json

# Run
uv run generate_images.py --config test-single-windows.json
```

**Expected:**

- Config accepted
- Image generated
- Temp files in `C:\Users\...\AppData\Local\Temp\`
- No encoding errors

**Dependencies:** All Phase 1 and Phase 2 tasks
**Can parallelize:** Yes (with other platform tests)

---

### Task 3.3: Test Batch with TrendLife (Windows)

**Goal:** Verify batch generation with logo overlay on Windows

**Test Case:**

```json
{
  "slides": [
    {"number": 1, "prompt": "TrendLife title slide", "style": "trendlife"},
    {"number": 2, "prompt": "Feature overview", "style": "trendlife"},
    {"number": 3, "prompt": "Security benefits", "style": "trendlife"}
  ],
  "output_dir": "./test-trendlife/"
}
```

**Expected:**

- All 3 slides generated
- Logo overlay applied to all slides
- No path errors
- No encoding errors

**Dependencies:** All Phase 1 and Phase 2 tasks
**Can parallelize:** Yes (with other tests)

---

### Task 3.4: Test Absolute Path Rejection

**Goal:** Verify path validation rejects absolute paths

**Test Case:**

```json
{
  "slides": [{"number": 1, "prompt": "Test slide"}],
  "output_dir": "/home/user/absolute-path/"
}
```

**Expected:**

- Script exits with error code 1
- Error message: "output_dir must be relative path"
- Suggests using `./dirname/`

**Dependencies:** Task 1.4
**Can parallelize:** Yes (with other tests)

---

### Task 3.5: Test Large Batch (10 slides)

**Goal:** Verify progress tracking and batch completion

**Test Case:**

```json
{
  "slides": [
    {"number": 1, "prompt": "Slide 1"},
    {"number": 2, "prompt": "Slide 2"},
    ...
    {"number": 10, "prompt": "Slide 10"}
  ],
  "output_dir": "./test-batch-10/"
}
```

**Expected:**

- Progress file updates correctly
- All 10 slides generated
- Results file shows completion
- Context consumption acceptable

**Dependencies:** All Phase 1 and Phase 2 tasks
**Can parallelize:** No (long-running test)

---

## Summary

**Total Tasks:** 17

- Phase 1 (Script): 4 tasks
- Phase 2 (Docs): 6 tasks
- Phase 3 (Test): 7 tasks

**Parallelization Opportunities:**

- Phase 1: Tasks 1.2, 1.3, 1.4 can run in parallel after 1.1
- Phase 2: Tasks 2.1, 2.4, 2.5, 2.6 can run in parallel
- Phase 3: Most tests can run in parallel except 3.5

**Critical Path:**

1. Task 1.1 (rename) → Task 1.2 (model logic) → Task 2.2 (remove heredocs) → Task 2.3 (add unified workflow) → Task 3.5
   (final test)

**Estimated Time:**

- Phase 1: 1-2 hours
- Phase 2: 2-3 hours
- Phase 3: 1-2 hours
- **Total: 4-7 hours** (single developer)
