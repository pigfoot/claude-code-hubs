# Capability: Batch Generation

**Capability ID:** `batch-generation`
**Status:** Draft
**Related Changes:** 001-implement-batch-generation

## Overview

Batch generation mode for nano-banana skill that processes 5+ image requests in a single background task to reduce conversation context consumption by 80%.

## ADDED Requirements

### Requirement: Automatic Batch Mode Activation

The system SHALL automatically activate batch generation mode when a user requests 5 or more images.

**ID:** `batch-generation-001`  
**Priority:** High

#### Scenario: User requests 10-slide presentation

**Given:** User asks "Generate 10 slides about CI/CD pipeline"
**When:** Claude detects 10 slides are needed
**Then:**
- Batch mode is activated automatically
- User is notified: "Generating 10 slides in batch mode..."
- Direct execution is NOT used

#### Scenario: User requests 3-slide presentation

**Given:** User asks "Generate 3 slides about Docker basics"
**When:** Claude detects 3 slides are needed
**Then:**
- Direct execution is used (existing behavior)
- Batch mode is NOT activated
- User sees immediate feedback per slide

**Rationale:** 5-slide threshold balances context savings (61%+) against complexity overhead.

---

### Requirement: Configuration File Creation

The system SHALL create a JSON configuration file containing all slide specifications before starting batch generation.

**ID:** `batch-generation-002`  
**Priority:** High

#### Scenario: Creating config for mixed-style presentation

**Given:** User requests slides with different visual styles
**When:** Claude prepares batch generation
**Then:**
- Config JSON is created at `/tmp/slides_config.json`
- Contains array of slide objects with number, prompt, style
- Includes output_dir, model, format, quality parameters
- Uses environment variable values for model/format/quality

**Config Example:**
```json
{
  "slides": [
    {"number": 1, "prompt": "Pipeline overview", "style": "professional"},
    {"number": 2, "prompt": "Build stage", "style": "data-viz"},
    {"number": 3, "prompt": "Test automation", "style": "professional"}
  ],
  "output_dir": "/home/user/ci-cd-deck/",
  "model": "gemini-3-pro-image-preview",
  "format": "webp",
  "quality": 90
}
```

**Rationale:** Structured config enables Python script to run independently.

---

### Requirement: Background Task Execution

The system SHALL execute batch generation as a background Bash task using `run_in_background=True`.

**ID:** `batch-generation-003`  
**Priority:** High

#### Scenario: Starting batch generation task

**Given:** Config file is created at `/tmp/slides_config.json`
**When:** Claude starts batch generation
**Then:**
- `Bash(command="python generate_batch.py --config /tmp/slides_config.json", run_in_background=True)` is called
- Task ID is returned (e.g., "task_abc123")
- Python script runs independently in background
- Main conversation continues without blocking

#### Scenario: Background task output isolation

**Given:** Batch generation is running in background
**When:** Python script generates output/logs
**Then:**
- Output does NOT appear in main conversation
- Only progress file updates are visible
- Context is not polluted with generation details

**Rationale:** Background execution prevents context accumulation while maintaining responsiveness.

---

### Requirement: Context Consumption Target

Batch generation for 10 slides SHALL consume less than 500 tokens in the main conversation context.

**ID:** `batch-generation-004`
**Priority:** High

#### Scenario: 10-slide generation context measurement

**Given:** User requests 10-slide presentation
**When:** Batch generation completes successfully
**Then:**
- Total context consumption ≤ 500 tokens
- Breakdown approximately:
  - Config creation: ~50 tokens
  - Start background task: ~20 tokens
  - Progress polls (3-6): ~120-240 tokens
  - Final results: ~250 tokens

**Rationale:** 80% reduction from current 1,800 tokens enables longer conversations.

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

## MODIFIED Requirements

None - this is a new capability addition.

## REMOVED Requirements

None - existing direct execution (1-4 slides) remains unchanged.

## Cross-References

- Related: `progress-tracking` - Required for batch mode user feedback
- Related: `error-handling` - Required for robust batch processing
- Dependency: Existing nano-banana skill infrastructure
- Dependency: `Bash(run_in_background=True)` tool capability
