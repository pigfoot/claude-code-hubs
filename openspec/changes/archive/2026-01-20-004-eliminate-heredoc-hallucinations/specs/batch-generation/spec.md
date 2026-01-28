# batch-generation Specification (Delta)

## Purpose

Update batch-generation spec to reflect unified generation workflow where all image counts use the same script.

## MODIFIED Requirements

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

## REMOVED Requirements

### ~~Requirement: Automatic Batch Mode Activation (threshold-based)~~

**Previous requirement (now obsolete):**
> The system SHALL automatically activate batch generation mode when a user requests 5 or more images.

**Removed because:** No separate "batch mode" exists. All requests use unified workflow.

**Replaced by:** unified-generation spec's single workflow requirement

---

## Summary of Changes

**Modified:**

- batch-generation-001: Remove 5+ slide threshold, all counts use same workflow
- batch-generation-003: Update script name from `generate_batch.py` to `generate_images.py`
- Config examples: Remove `model` field

**Removed:**

- Threshold-based mode activation logic

**Cross-references:**

- See `unified-generation` spec for single workflow details
- See `config-simplification` spec for config format changes
