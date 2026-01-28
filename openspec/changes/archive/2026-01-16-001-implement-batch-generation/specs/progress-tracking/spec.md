# Capability: Progress Tracking

**Capability ID:** `progress-tracking`
**Status:** Draft
**Related Changes:** 001-implement-batch-generation

## Overview

Real-time progress tracking for batch generation using JSON progress files that Claude polls periodically to update the
user.

## ADDED Requirements

### Requirement: Progress File Updates

The batch generation script SHALL write progress to `/tmp/nano-banana-progress.json` after completing each slide.

**ID:** `progress-tracking-001`  
**Priority:** High

#### Scenario: Progress updates during generation

**Given:** generate_batch.py is processing 10 slides
**When:** Each slide completes successfully
**Then:**

- Progress file is updated immediately
- File contains current count, total count, status message
- File includes array of completed slide paths
- Timestamp is updated

**Progress File Schema:**

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
  "started_at": "2026-01-16T10:30:00Z",
  "updated_at": "2026-01-16T10:30:45Z"
}
```

**Rationale:** Structured JSON enables reliable parsing and clear user updates.

---

### Requirement: Periodic Progress Polling

Claude SHALL poll the progress file every 10-15 seconds to provide user updates.

**ID:** `progress-tracking-002`
**Priority:** High

#### Scenario: Polling during 10-slide generation

**Given:** Batch generation is running
**When:** Claude checks progress
**Then:**

- `Read("/tmp/nano-banana-progress.json")` is called every 10-15 seconds
- Progress JSON is parsed
- User sees update: "Progress: 3/10 slides completed (30%)"
- Polling continues until current == total

#### Scenario: Handling missing progress file

**Given:** Background task just started
**When:** Claude attempts first poll
**Then:**

- If file doesn't exist yet, wait and retry
- No error shown to user
- Continue polling normally

**Rationale:** 10-15s interval balances responsiveness with API call efficiency.

---

### Requirement: Progress Visibility to User

User SHALL see periodic progress updates showing completion percentage and slide count.

**ID:** `progress-tracking-003`
**Priority:** High

#### Scenario: User sees progress during generation

**Given:** 10-slide batch generation is running
**When:** Progress polls occur
**Then:**

- User sees updates like:
  - "Progress: 3/10 slides completed (30%)"
  - "Progress: 7/10 slides completed (70%)"
- Updates appear at reasonable intervals (not spammy)
- Format is consistent and clear

**Rationale:** Visibility prevents user from thinking the task is stuck or failed.

---

### Requirement: Completion Detection

Claude SHALL detect when batch generation completes by checking progress file.

**ID:** `progress-tracking-004`
**Priority:** High

#### Scenario: Detecting successful completion

**Given:** Progress file shows current == total
**When:** Claude reads progress file
**Then:**

- Polling stops
- Final results file is read
- User is notified of completion

#### Scenario: Detecting early termination

**Given:** Background task terminates abnormally
**When:** Progress file stops updating for 60+ seconds
**Then:**

- Claude detects stalled progress
- User is notified: "Generation may have failed, checking results..."
- Results file is read for error details

**Rationale:** Reliable completion detection ensures user always gets outcome.

---

## MODIFIED Requirements

None - this is a new capability.

## REMOVED Requirements

None.

## Cross-References

- Related: `batch-generation` - Progress tracking is integral to batch mode
- Related: `error-handling` - Failed slides must be reflected in progress
- Dependency: File I/O via Read tool
- Dependency: JSON parsing capability
