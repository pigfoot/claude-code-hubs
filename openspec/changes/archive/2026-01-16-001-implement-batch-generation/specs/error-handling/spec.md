# Capability: Error Handling

**Capability ID:** `error-handling`
**Status:** Draft
**Related Changes:** 001-implement-batch-generation

## Overview

Robust error handling for batch generation that continues processing after individual slide failures and provides
comprehensive error reporting.

## ADDED Requirements

### Requirement: Continue on Individual Failure

The batch generation script SHALL continue processing remaining slides when an individual slide generation fails.

**ID:** `error-handling-001`  
**Priority:** High

#### Scenario: Single slide fails due to API error

**Given:** Batch generation is processing 10 slides
**When:** Slide 3 fails with "API rate limit exceeded"
**Then:**

- Error is logged with slide number and message
- Script continues to slide 4
- Progress file updated with failed count
- Remaining slides 4-10 are processed normally

#### Scenario: Multiple non-consecutive failures

**Given:** Batch generation is processing 10 slides
**When:** Slides 2, 5, and 8 fail
**Then:**

- All three errors are logged separately
- Slides 1, 3, 4, 6, 7, 9, 10 complete successfully
- Final results show 7 completed, 3 failed
- All error details are preserved

**Rationale:** Partial results are better than no results; one failure shouldn't block the entire batch.

---

### Requirement: Comprehensive Error Reporting

The results file SHALL include complete error details for all failed slides.

**ID:** `error-handling-002`  
**Priority:** High

#### Scenario: Results file with mixed success/failure

**Given:** 10-slide generation completed with 2 failures
**When:** Results file is written
**Then:**

- Contains `completed: 8, failed: 2, total: 10`
- `outputs` array lists 8 successful slides with paths
- `errors` array contains 2 entries with:
  - Slide number
  - Error message
  - Timestamp

**Results File Example:**

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
    {
      "slide": 3,
      "error": "API rate limit exceeded",
      "timestamp": "2026-01-16T10:31:15Z"
    },
    {
      "slide": 7,
      "error": "Invalid prompt format",
      "timestamp": "2026-01-16T10:32:03Z"
    }
  ],
  "started_at": "2026-01-16T10:30:00Z",
  "completed_at": "2026-01-16T10:32:30Z",
  "duration_seconds": 150
}
```

**Rationale:** Detailed error info enables debugging and retry of specific slides.

---

### Requirement: Graceful Error Communication

Claude SHALL communicate errors to the user in a clear, actionable format.

**ID:** `error-handling-003`
**Priority:** High

#### Scenario: Reporting partial success with failures

**Given:** Results file shows 8 completed, 2 failed
**When:** Claude reports results to user
**Then:**

- Success message: "✓ Completed 8 slides in 150s"
- Warning: "⚠ 2 slides failed:"
- Error details listed:
  - "Slide 3: API rate limit exceeded"
  - "Slide 7: Invalid prompt format"
- Paths to successful slides provided
- Actionable suggestion if applicable (e.g., "Retry failed slides after rate limit resets")

**Rationale:** Users need to know what succeeded, what failed, and what to do next.

---

### Requirement: Exit Code Handling

The batch generation script SHALL use appropriate exit codes to signal outcome.

**ID:** `error-handling-004`  
**Priority:** Medium

#### Scenario: Partial success exit code

**Given:** 8 out of 10 slides generated successfully
**When:** generate_batch.py exits
**Then:**

- Exit code is 0 (success - some slides completed)
- Results file contains full details

#### Scenario: Total failure exit code

**Given:** All 10 slides failed to generate
**When:** generate_batch.py exits
**Then:**

- Exit code is 1 (failure - no slides completed)
- Results file contains all error details
- User is notified: "❌ All slides failed to generate"

**Rationale:** Exit codes enable shell-level success/failure detection while results file provides details.

---

### Requirement: Error Type Handling

The script SHALL handle different error types appropriately.

**ID:** `error-handling-005`  
**Priority:** Medium

#### Scenario: API errors (rate limit, auth failure)

**Given:** API returns 429 or 401 error
**When:** Slide generation fails
**Then:**

- Error message includes API error code and description
- Suggests wait time for rate limit
- Continues to next slide

#### Scenario: File I/O errors

**Given:** Output directory is not writable
**When:** Slide generation attempts to save file
**Then:**

- Error message includes permission details
- Script does NOT continue (fatal error)
- User is notified immediately

#### Scenario: Invalid configuration

**Given:** Config JSON has invalid model name
**When:** First slide generation attempts
**Then:**

- Error detected before API call
- Clear validation error message
- Script exits early (fail fast)

**Rationale:** Different error types need different handling strategies (continue vs fail fast).

---

## MODIFIED Requirements

None - this is a new capability.

## REMOVED Requirements

None.

## Cross-References

- Related: `batch-generation` - Error handling is integral to batch processing
- Related: `progress-tracking` - Failed slides must update progress
- Dependency: Python exception handling
- Dependency: File I/O error handling
