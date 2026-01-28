# Design Document: Batch Generation with Background Tasks

**Change ID:** `001-implement-batch-generation`
**Status:** Draft

## Overview

This design introduces a batch generation mode for nano-banana that reduces conversation context consumption by 80% when
generating 5+ images. The solution uses background Bash tasks with progress file polling.

## Architecture

### Component Diagram

```
┌─────────────────────┐
│   Claude (Skill)    │
│                     │
│  1. Detect 5+ slides│
│  2. Create config   │
│  3. Start bg task   │
│  4. Poll progress   │
│  5. Read results    │
└──────────┬──────────┘
           │
           │ Bash(run_in_background=True)
           ↓
┌─────────────────────┐         ┌──────────────────────┐
│  generate_batch.py  │────────→│  Progress File       │
│                     │  writes │  /tmp/nano-banana-   │
│  • Parse config     │         │  progress.json       │
│  • Generate slides  │         │                      │
│  • Track progress   │         │  {"current": N,      │
│  • Handle errors    │         │   "total": M, ...}   │
└─────────┬───────────┘         └──────────────────────┘
          │
          │ on completion
          ↓
┌─────────────────────┐
│   Results File      │
│   /tmp/nano-banana- │
│   results.json      │
│                     │
│   {"completed": N,  │
│    "outputs": [...],│
│    "errors": [...]} │
└─────────────────────┘
```

### Data Flow

```
User Request (10 slides)
    ↓
Skill: Detect batch mode needed (≥5 slides)
    ↓
Skill: Create slides_config.json
    {
      "slides": [
        {"number": 1, "prompt": "...", "style": "professional"},
        {"number": 2, "prompt": "...", "style": "data-viz"},
        ...
      ],
      "output_dir": "/path/to/deck/",
      "model": "gemini-3-pro-image-preview",
      "format": "webp",
      "quality": 90
    }
    ↓
Skill: Bash(run_in_background=True)
    → "Started background task: task_abc123"
    ↓
Loop: Poll every 10-15s
    Read(/tmp/nano-banana-progress.json)
    → {"current": 3, "total": 10, "status": "generating slide 3..."}
    → Update user: "Progress: 3/10 slides completed (30%)"
    ↓
Wait for completion
    ↓
Read(/tmp/nano-banana-results.json)
    → {"completed": 10, "outputs": [...], "duration": "45s"}
    ↓
Report to user
    → "✓ All 10 slides completed in 45s"
```

## Technical Decisions

### 0. Progressive Disclosure for Token Efficiency

**Decision:** Keep SKILL.md minimal (~20 new lines), put details in references/

**Context:**

- nano-banana recently optimized: 795 → 387 lines (-51%)
- Adopted progressive disclosure: main skill → references/
- Must not regress token consumption

**Implementation:**

- **SKILL.md** (~387 + 20 = 407 lines total):
  - Batch mode trigger rule (5+ slides)
  - 4-step workflow summary (no code)
  - Reference link to batch-generation.md

- **references/batch-generation.md** (~200-300 lines):
  - Complete workflow with Python code
  - Configuration schemas
  - Progress/results file schemas
  - Error handling examples
  - Troubleshooting guide

**Rationale:**

- Maintains token efficiency achieved in v0.0.4
- Claude loads SKILL.md first, references/ only when needed
- Consistent with existing gemini-api.md, imagen-api.md pattern
- Users benefit: faster skill loading, details on demand

**Target:** SKILL.md stays under 420 lines total

---

### 1. Why Background Bash vs Subagent?

**Decision:** Use `Bash(run_in_background=True)`

**Rationale:**

- **Cost:** Zero additional API tokens (vs +1,500% with subagents)
- **Speed:** Python runs at native speed, no startup overhead
- **Simplicity:** Single Python process, no coordination complexity
- **Context:** 80% reduction (390 vs 1,800 tokens)

**Trade-off:** Requires polling mechanism vs subagent's built-in notifications

### 2. Progress File Format

**Decision:** Use JSON with structured schema

```json
{
  "current": 3,
  "total": 10,
  "status": "generating slide 3...",
  "completed": [
    "/path/slide-1.webp",
    "/path/slide-2.webp",
    "/path/slide-3.webp"
  ],
  "failed": [],
  "started_at": "2026-01-16T10:30:00Z"
}
```

**Rationale:**

- Easy to parse with `jq` or Python json module
- Self-documenting structure
- Extensible for future fields

**Alternative considered:** Plain text log

- Rejected: Harder to parse, error-prone

### 3. When to Use Batch Mode?

**Decision:** Automatic activation at 5+ slides

**Rationale:**

- **1-4 slides:** Direct execution is simpler
  - Immediate feedback
  - Easy debugging
  - Context cost acceptable (<800 tokens)

- **5+ slides:** Batch mode provides clear benefit
  - Context savings: 80%
  - Progress tracking valuable
  - Worth the polling overhead

**Threshold analysis:**

| Slides | Direct Context | Batch Context | Savings | Worth It? |
|--------|----------------|---------------|---------|-----------|
| 3      | ~600 tokens    | ~390 tokens   | 35%     | No - complexity not justified |
| 5      | ~1,000 tokens  | ~390 tokens   | 61%     | **Yes - threshold** |
| 10     | ~1,800 tokens  | ~390 tokens   | 78%     | Yes |
| 20     | ~3,600 tokens  | ~390 tokens   | 89%     | Yes |

### 4. Error Handling Strategy

**Decision:** Continue processing on individual slide failures

**Behavior:**

1. Slide N fails → log error, continue to slide N+1
2. Update progress with failed count
3. Report all errors in final results
4. Exit code 0 if any slides succeeded, 1 if all failed

**Rationale:**

- User gets partial results instead of nothing
- Failures in one slide don't block the rest
- All errors reported for debugging

**Example:**

```json
{
  "completed": 8,
  "failed": 2,
  "outputs": ["/path/slide-1.webp", ...],
  "errors": [
    {"slide": 3, "error": "API rate limit exceeded"},
    {"slide": 7, "error": "Invalid prompt format"}
  ]
}
```

### 5. Polling Interval

**Decision:** 10-15 seconds

**Rationale:**

- **Too fast (<5s):** Excessive API calls, user sees too many updates
- **Too slow (>20s):** User feels disconnected, poor UX
- **10-15s sweet spot:**
  - ~3-6 updates for 10 slides (reasonable)
  - User stays informed
  - Low overhead

**Dynamic adjustment:**

- Could adapt based on slide complexity (future enhancement)

### 6. File Paths

**Decision:** Use `/tmp/nano-banana-{progress,results}.json`

**Rationale:**

- `/tmp` is standard temp location across Unix systems
- Predictable paths (no need to pass task_id)
- Auto-cleanup on reboot
- No permission issues

**Alternative considered:** Task-specific paths like `/tmp/nano-banana-{task_id}.json`

- Rejected: Unnecessary complexity, task_id management overhead

### 7. Backward Compatibility

**Decision:** Keep direct execution for 1-4 slides

**Rationale:**

- Don't break existing workflows
- Simpler code path for simple cases
- User expectations (immediate feedback for small jobs)

**Implementation:**

```python
# In SKILL.md logic
if slide_count >= 5:
    use_batch_mode()
else:
    use_direct_execution()  # existing behavior
```

## API Contracts

### Input: Config JSON

```json
{
  "slides": [
    {
      "number": 1,
      "prompt": "CI/CD pipeline overview with build, test, deploy stages",
      "style": "professional",
      "output_filename": "slide-1.webp"
    }
  ],
  "output_dir": "/home/user/presentation/",
  "model": "gemini-3-pro-image-preview",
  "format": "webp",
  "quality": 90,
  "api_key": "${GEMINI_API_KEY}",
  "base_url": "${GOOGLE_GEMINI_BASE_URL}"
}
```

**Validation rules:**

- `slides`: array, min length 1, required
- `slides[].number`: integer, required
- `slides[].prompt`: string, non-empty, required
- `slides[].style`: string, optional (default: none)
- `output_dir`: string, valid directory path, required
- `model`: string, optional (default from env)
- `format`: enum("webp", "jpg", "png"), optional (default: "webp")
- `quality`: integer 1-100, optional (default: 90)

### Output: Progress JSON

```json
{
  "current": 3,
  "total": 10,
  "status": "generating slide 3...",
  "completed": ["/path/slide-1.webp", "/path/slide-2.webp", "/path/slide-3.webp"],
  "failed": [],
  "started_at": "2026-01-16T10:30:00Z",
  "updated_at": "2026-01-16T10:30:45Z"
}
```

### Output: Results JSON

```json
{
  "completed": 8,
  "failed": 2,
  "total": 10,
  "outputs": [
    {"slide": 1, "path": "/path/slide-1.webp", "size_kb": 245},
    {"slide": 2, "path": "/path/slide-2.webp", "size_kb": 312},
    ...
  ],
  "errors": [
    {"slide": 3, "error": "API rate limit exceeded", "timestamp": "2026-01-16T10:31:15Z"},
    {"slide": 7, "error": "Invalid prompt format", "timestamp": "2026-01-16T10:32:03Z"}
  ],
  "started_at": "2026-01-16T10:30:00Z",
  "completed_at": "2026-01-16T10:32:30Z",
  "duration_seconds": 150
}
```

## Implementation Notes

### Python Script Structure

```python
#!/usr/bin/env python3
"""
generate_batch.py - Batch image generation with progress tracking

Usage:
    python generate_batch.py --config slides_config.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

PROGRESS_FILE = Path("/tmp/nano-banana-progress.json")
RESULTS_FILE = Path("/tmp/nano-banana-results.json")

def load_config(config_path):
    """Load and validate configuration"""
    pass

def write_progress(current, total, status, completed, failed):
    """Write progress to JSON file"""
    pass

def write_results(completed, failed, outputs, errors, started_at):
    """Write final results to JSON file"""
    pass

def generate_slide(slide_config, output_dir, model, format, quality):
    """Generate single slide, return (success, output_path, error)"""
    pass

def main():
    config = load_config(sys.argv[2])  # --config path

    started_at = datetime.utcnow().isoformat() + 'Z'
    completed = []
    failed = []
    errors = []

    for i, slide in enumerate(config['slides']):
        status = f"generating slide {slide['number']}..."
        write_progress(i, len(config['slides']), status, completed, failed)

        success, output_path, error = generate_slide(
            slide, config['output_dir'],
            config.get('model'), config.get('format', 'webp'),
            config.get('quality', 90)
        )

        if success:
            completed.append(output_path)
        else:
            failed.append(slide['number'])
            errors.append({"slide": slide['number'], "error": error})

    write_results(completed, failed, outputs, errors, started_at)
    sys.exit(0 if completed else 1)

if __name__ == '__main__':
    main()
```

### Skill Workflow (Progressive Disclosure Strategy)

**IMPORTANT:** Following nano-banana's token optimization (795→387 lines), we use progressive disclosure:

- **SKILL.md**: Minimal trigger logic (~15-20 lines)
- **references/batch-generation.md**: Complete workflow with code examples (~200-300 lines)

#### Content for SKILL.md (15-20 lines)

```markdown
## Multi-Slide Generation

**Automatic Mode Selection:**
- 5+ slides → batch mode (background task, progress tracking)
- 1-4 slides → direct execution (current behavior, immediate feedback)

**Batch Mode Quick Reference:**
1. Create config JSON with slide specs
2. Start background task: `Bash(run_in_background=True)`
3. Poll `/tmp/nano-banana-progress.json` every 10-15s
4. Read `/tmp/nano-banana-results.json` when complete

**For complete workflow, schemas, and examples:** See `references/batch-generation.md`
```

**Target:** SKILL.md stays under 420 lines total (387 current + ~20 new)

---

#### Content for references/batch-generation.md (200-300 lines)

**Complete workflow with all code examples:**

```markdown
# Batch Generation Reference

## Overview
For generating 5+ slides efficiently with minimal context consumption.

## When to Use
- **Automatic activation:** 5+ slides detected
- **Benefits:** 80% context reduction (1,800 → 390 tokens)
- **Trade-off:** Less immediate feedback (progress shown in batches)

## Complete Workflow

### Step 1: Create Configuration File

```python
config = {
    "slides": [
        {"number": 1, "prompt": "CI/CD pipeline overview", "style": "professional"},
        {"number": 2, "prompt": "Build stage architecture", "style": "professional"},
        {"number": 3, "prompt": "Testing pyramid", "style": "data-viz"},
        # ... more slides
    ],
    "output_dir": "/path/to/deck/",
    "model": os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview",
    "format": os.environ.get("NANO_BANANA_FORMAT", "webp"),
    "quality": int(os.environ.get("NANO_BANANA_QUALITY", "90"))
}

# Write to temp file
with open("/tmp/slides_config.json", "w") as f:
    json.dump(config, f)
```

### Step 2: Start Background Task

```python
Bash(
    command="python /path/to/generate_batch.py --config /tmp/slides_config.json",
    run_in_background=True,
    description="Generate 10 slides in batch mode"
)
# Returns: task_id
```

**Tell user:** "Generating 10 slides in background..."

### Step 3: Poll Progress (every 10-15 seconds)

```python
progress = Read("/tmp/nano-banana-progress.json")
data = json.loads(progress)

# Update user
print(f"Progress: {data['current']}/{data['total']} slides completed ({data['current']/data['total']*100:.0f}%)")

# Check if complete (progress.current == progress.total)
```

### Step 4: Read Final Results

```python
results = Read("/tmp/nano-banana-results.json")
data = json.loads(results)

# Report to user
print(f"✓ Completed {data['completed']} slides in {data['duration_seconds']}s")
if data['failed']:
    print(f"⚠ {data['failed']} slides failed")
    for error in data['errors']:
        print(f"  - Slide {error['slide']}: {error['error']}")

print(f"\nResults: {data['outputs'][0]['path'].parent}")
```

## Configuration Schema

[... detailed schema documentation ...]

## Progress File Schema

[... detailed progress JSON schema ...]

## Results File Schema

[... detailed results JSON schema ...]

## Error Handling

[... error codes and troubleshooting ...]

## Examples

[... complete examples for various scenarios ...]

```

**This keeps SKILL.md lean while providing complete reference when needed.**

## Performance Characteristics

### Context Consumption

| Operation | Tokens | Notes |
|-----------|--------|-------|
| Create config JSON | ~50 | One-time |
| Start background task | ~20 | One-time |
| Poll progress (per poll) | ~40 | Typically 3-6 polls |
| Read final results | ~250 | One-time, includes all paths |
| **Total for 10 slides** | **~390** | vs 1,800 direct |

### Time Characteristics

| Slides | Direct Time | Batch Time | Difference |
|--------|-------------|------------|------------|
| 5      | ~30s        | ~32s       | +2s (startup overhead) |
| 10     | ~60s        | ~62s       | +2s |
| 20     | ~120s       | ~122s      | +2s |

**Note:** Batch mode overhead is constant (~2s), becomes negligible for larger batches.

## Security Considerations

### File Permissions

- Progress/results files in `/tmp` are world-readable by default
- **Consideration:** Could contain sensitive prompt information
- **Mitigation:** Use `umask 077` before creating files (only user can read)

### API Key Handling

- Config JSON should NOT contain API key in plain text
- **Solution:** Use environment variable references: `"api_key": "${GEMINI_API_KEY}"`
- Script expands env vars at runtime

### Path Injection

- Validate all file paths before use
- Prevent directory traversal: `../../etc/passwd`
- **Mitigation:** Use `Path().resolve()` and check prefix

## Future Enhancements

### Phase 2 (Not in current scope)

1. **Parallel Generation:**
   - Use `asyncio` to generate 2-3 slides concurrently
   - Requires rate limit management
   - Estimated speedup: 2-3x

2. **Adaptive Polling:**
   - Faster polling initially, slower as generation progresses
   - Reduces API calls for long batches

3. **Resume Support:**
   - Save state, allow resuming failed batches
   - Useful for very large decks (50+ slides)

4. **MCP Server:**
   - Convert to MCP server for cleanest architecture
   - Eliminates file-based communication
   - Best long-term solution

## Open Questions

None - design is ready for implementation.

## Review Checklist

- [x] Architecture diagram included
- [x] Data flow documented
- [x] Technical decisions justified
- [x] API contracts defined
- [x] Error handling specified
- [x] Performance characteristics documented
- [x] Security considerations addressed
- [x] Future enhancements identified
