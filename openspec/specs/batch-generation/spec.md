# batch-generation Specification

## Purpose

TBD - created by archiving change 001-implement-batch-generation. Update Purpose after archive.

## Requirements

### Requirement: Automatic Batch Mode Activation

**Previous:** The system SHALL automatically activate batch generation mode when a user requests 5 or more images.

**Modified:** The system SHALL use the unified generation workflow for all image requests, eliminating the concept of
separate "batch mode" activation.

**ID:** `batch-generation-001`
**Priority:** High

#### Scenario: Single image uses same workflow

**Given:** User requests 1 image
**When:** Claude prepares generation
**Then:**

- Uses `generate_images.py` script
- Creates JSON config with 1 slide
- Same workflow as multiple images
- No mode detection needed

#### Scenario: Small batch uses same workflow

**Given:** User requests 3 images
**When:** Claude prepares generation
**Then:**

- Uses `generate_images.py` script
- Creates JSON config with 3 slides
- Same workflow as single or large batch
- No threshold checking

#### Scenario: Large batch uses same workflow

**Given:** User requests 10 images
**When:** Claude prepares generation
**Then:**

- Uses `generate_images.py` script
- Creates JSON config with 10 slides
- Progress tracking scales naturally
- Same workflow as smaller counts

**Rationale:** Eliminates complexity of threshold detection. Previous 5-slide threshold no longer relevant.

---

### Requirement: Configuration File Creation

The system SHALL create a JSON configuration file containing slide specifications without the `model` field.

**ID:** `batch-generation-002`
**Priority:** High

**Updated:** Script name changed from `generate_batch.py` to `generate_images.py`, `model` field removed

#### Scenario: Creating config for mixed-style presentation

**Given:** User requests slides with different visual styles
**When:** Claude prepares generation
**Then:**

- Config JSON is created
- Contains slides array with number, prompt, style
- Includes output_dir (relative path)
- Does NOT include `model` field
- Uses environment variable for model selection

Updated example:

```json
{
  "slides": [
    {"number": 1, "prompt": "Pipeline overview", "style": "professional"},
    {"number": 2, "prompt": "Build stage", "style": "data-viz"}
  ],
  "output_dir": "./ci-cd-deck/",
  "format": "webp",
  "quality": 90
}
```

**Previous example included:** `"model": "gemini-3-pro-image-preview"` ← Removed

**Rationale:** Model selection via environment variable prevents hallucinations; relative paths ensure cross-platform
compatibility.

---

### Requirement: Background Task Execution

The system SHALL execute generation using the renamed script `generate_images.py` with the same background execution
capabilities.

**ID:** `batch-generation-003`
**Priority:** High

**Updated:** Command reference changed from `generate_batch.py` to `generate_images.py`

#### Scenario: Starting generation task

**Given:** Config file is created
**When:** Claude starts generation
**Then:**

- Executes: `uv run generate_images.py --config <path>`
- Uses updated script name
- Task runs in background when appropriate
- Same background execution behavior as before

**Previous command:** `python generate_batch.py --config /tmp/slides_config.json`
**Updated command:** `uv run generate_images.py --config <path>`

**Rationale:** Script rename reflects unified workflow; functionality unchanged.

---

### Requirement: Context Consumption Target

Generation for any number of slides SHALL consume less than 500 tokens in the main conversation context through the
unified workflow.

**ID:** `batch-generation-004`
**Priority:** High

**Updated:** Target now applies to all image counts, not just 5+

#### Scenario: Context consumption for any slide count

**Given:** User requests images (1, 5, 10, or more)
**When:** Generation completes successfully
**Then:**

- Total context consumption ≤ 500 tokens
- Breakdown: config creation (~50 tokens), script execution (~20 tokens), progress polls (~120-240 tokens), results
  (~250 tokens)
- Optimization applies to all counts, not just "batch mode"

**Rationale:** Unified workflow provides consistent efficiency across all image counts.

---

### Requirement: Sequential Slide Generation

The batch generation script SHALL generate slides sequentially (one at a time) rather than in parallel.

**ID:** `batch-generation-005`  
**Priority:** Medium

#### Scenario: Generating 10 slides in order

**Given:** Config specifies slides 1-10
**When:** generate_batch.py executes
**Then:**

- Slides are generated in numeric order: 1, 2, 3, ..., 10
- Next slide starts only after previous completes
- No concurrent API requests

**Rationale:** Sequential generation avoids API rate limits and simplifies error handling.

---

### Requirement: Logo Overlay Integration in Batch Generation

The batch generation script SHALL automatically apply logo overlay for slides with brand styles (e.g., TrendLife).

**ID:** `batch-generation-006`
**Priority:** High

#### Scenario: TrendLife slides in batch get logo overlay

**Given:** Config contains slides with `"style": "trendlife"`
**When:** Batch generation processes each slide
**Then:**

- Slide image is generated with TrendLife colors
- Layout type is automatically detected from prompt
- Logo overlay is applied using `logo_overlay.py` module
- Final output includes TrendLife logo
- Progress includes logo overlay step

#### Scenario: Mixed styles in single batch

**Given:** Config contains:

```json
{
  "slides": [
    {"number": 1, "prompt": "Title slide", "style": "trendlife"},
    {"number": 2, "prompt": "Data viz", "style": "professional"},
    {"number": 3, "prompt": "Conclusion", "style": "trendlife"}
  ]
}
```

**When:** Batch generation runs
**Then:**

- Slide 1: TrendLife style + logo overlay applied
- Slide 2: Professional style, no logo overlay
- Slide 3: TrendLife style + logo overlay applied
- Each slide processed according to its style

#### Scenario: Logo overlay failure in batch

**Given:** Slide 5 in batch encounters logo overlay error
**When:** Logo overlay fails for that slide
**Then:**

- Error is logged: "Slide 5: Logo overlay failed - [reason]"
- Slide is saved without logo
- Batch continues with remaining slides
- Final summary includes warning

**Rationale:** Logo overlay must be seamlessly integrated into batch workflow without disrupting the background
execution model.

---

### Requirement: Brand Style Progress Tracking

The batch generation progress tracking SHALL include logo overlay status for brand-styled slides.

**ID:** `batch-generation-007`
**Priority:** Medium

#### Scenario: Progress includes logo overlay step

**Given:** Batch generation is processing TrendLife slide
**When:** Progress file is updated
**Then:**

- Progress includes: "Generated slide 3/10 (logo overlay applied)"
- Or if overlay fails: "Generated slide 3/10 (WARNING: logo overlay failed)"
- Users can monitor logo overlay success

#### Scenario: Progress for non-brand slides

**Given:** Batch generation is processing professional style slide
**When:** Progress file is updated
**Then:**

- Progress shows: "Generated slide 2/10"
- No mention of logo overlay (not applicable)
- Standard progress format maintained

**Progress Format Examples:**

```
Generated slide 1/10 (logo overlay applied)
Generated slide 2/10
Generated slide 3/10 (logo overlay applied)
WARNING: Slide 4 logo overlay failed - continuing
Generated slide 4/10
```

**Rationale:** Clear progress tracking helps users understand which slides received logo overlay and identify any
issues.

---

### Requirement: Performance Impact Management

Logo overlay SHALL NOT significantly impact batch generation performance, maintaining the sub-500 token context target.

**ID:** `batch-generation-008`
**Priority:** Medium

#### Scenario: Logo overlay within performance budget

**Given:** Batch generation of 10 TrendLife slides
**When:** All slides include logo overlay
**Then:**

- Logo overlay adds <200ms per slide
- Total time increase: <2 seconds for 10 slides
- Context consumption remains ≤ 500 tokens
- Background execution model still effective

#### Scenario: Memory efficiency maintained

**Given:** Logo overlay uses Pillow for image processing
**When:** Processing multiple slides in batch
**Then:**

- Memory is released after each logo overlay
- Peak memory usage <500MB
- No memory leaks from repeated operations

**Performance Targets with Logo Overlay:**

| Metric | Without Logo | With Logo | Delta |
|--------|--------------|-----------|-------|
| Per slide time | ~12s | ~12.2s | +200ms |
| 10-slide batch | ~2min | ~2min 2s | +2s |
| Context tokens | 400-500 | 400-500 | 0 |
| Memory usage | 300MB | 450MB | +150MB |

**Rationale:** Logo overlay must be efficient enough not to negate the benefits of batch generation.
