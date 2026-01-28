# Implementation Tasks

**Change ID:** `001-implement-batch-generation`

## Task Breakdown

### Phase 1: Python Script Foundation

**Goal:** Create batch generation script with progress tracking

- [ ] **Task 1.1:** Create `generate_batch.py` script
  - Accept JSON config with slides array, output_dir, format, quality
  - Parse config and validate parameters
  - Initialize progress tracking
  - **Validation:** Script can parse sample config without errors
  - **Estimated effort:** 1-2 hours

- [ ] **Task 1.2:** Implement progress file writer
  - Write progress to `/tmp/nano-banana-progress.json` after each slide
  - Format: `{"current": N, "total": M, "status": "...", "completed": [paths]}`
  - Handle file I/O errors gracefully
  - **Validation:** Progress file updates correctly during generation
  - **Estimated effort:** 30 minutes

- [ ] **Task 1.3:** Implement results file writer
  - Write final summary to `/tmp/nano-banana-results.json`
  - Format: `{"completed": N, "failed": M, "outputs": [paths], "errors": [...]}`
  - Include duration and summary statistics
  - **Validation:** Results file contains accurate completion data
  - **Estimated effort:** 30 minutes

- [ ] **Task 1.4:** Add error handling and recovery
  - Catch and log individual slide failures
  - Continue processing remaining slides on error
  - Report all errors in final results
  - **Validation:** Script continues after single slide failure
  - **Estimated effort:** 1 hour

### Phase 2: SKILL.md Integration (Progressive Disclosure)

**Goal:** Add minimal batch mode trigger logic to SKILL.md, keep it under 20 new lines

- [ ] **Task 2.1:** Add batch mode trigger to SKILL.md (15-20 lines max)
  - Add "Multi-Slide Generation" section with mode selection rule
  - Rule: 5+ slides → batch mode, 1-4 slides → direct execution
  - Brief 4-step workflow summary (no code examples)
  - Reference to `references/batch-generation.md` for details
  - **Validation:** Addition is <20 lines, maintains token efficiency
  - **Target:** SKILL.md remains ~407 lines (current 387 + 20)
  - **Estimated effort:** 20 minutes

- [ ] **Task 2.2:** Verify SKILL.md stays under 420 lines
  - Measure total line count after addition
  - Ensure no bloat from detailed examples
  - Confirm reference link works
  - **Validation:** SKILL.md ≤ 420 lines total
  - **Estimated effort:** 5 minutes

### Phase 3: Reference Documentation (All Details Here)

**Goal:** Create comprehensive batch generation reference (200-300 lines)

- [ ] **Task 3.1:** Create `references/batch-generation.md` (detailed guide)
  - **Complete workflow with code examples** (from design.md)
  - 4-step workflow with Python code blocks
  - Configuration reference with JSON schemas
  - Progress file schema and polling examples
  - Results file schema and parsing examples
  - Error codes and troubleshooting guide
  - **All content that would bloat SKILL.md goes here**
  - **Validation:** Document is 200-300 lines, comprehensive
  - **Estimated effort:** 1.5-2 hours

- [ ] **Task 3.2:** Update `slide-deck-styles.md` with batch mode reference
  - Replace current "Multi-Slide Generation" section
  - Add brief note: "For 5+ slides, see `batch-generation.md`"
  - Keep current parallel generation info for 3-5 slides
  - **Validation:** Updated section is concise, points to batch-generation.md
  - **Estimated effort:** 15 minutes

### Phase 4: Testing & Validation

**Goal:** Verify batch mode works correctly

- [ ] **Task 4.1:** Manual test: 5-slide generation
  - Create test config for 5 simple slides
  - Run batch generation
  - Verify progress updates
  - Verify final results
  - **Validation:** All 5 slides generated successfully with <500 tokens
  - **Estimated effort:** 30 minutes

- [ ] **Task 4.2:** Manual test: 10-slide generation
  - Create test config for 10 varied slides
  - Run batch generation
  - Monitor progress file updates
  - Verify context usage (~390 tokens)
  - **Validation:** All 10 slides generated, context target met
  - **Estimated effort:** 45 minutes

- [ ] **Task 4.3:** Error scenario test
  - Create config with intentional error (bad model name)
  - Verify script continues processing
  - Verify error is reported in results
  - **Validation:** Errors don't crash script, are clearly reported
  - **Estimated effort:** 30 minutes

- [ ] **Task 4.4:** Backward compatibility test
  - Test 1-4 slide scenarios still use direct execution
  - Verify no regression in simple use cases
  - **Validation:** Direct execution still works for <5 slides
  - **Estimated effort:** 30 minutes

### Phase 5: Documentation Updates

**Goal:** Update all user-facing documentation

- [ ] **Task 5.1:** Update main README.md
  - Add batch mode to "Multi-Slide Generation" section
  - Update context optimization numbers
  - Change "Future versions" to "Current implementation"
  - **Validation:** README accurately reflects new capability
  - **Estimated effort:** 30 minutes

- [ ] **Task 5.2:** Update plugin.json version
  - Bump version to 0.0.5
  - Update description if needed
  - **Validation:** Version incremented correctly
  - **Estimated effort:** 5 minutes

- [ ] **Task 5.3:** Update marketplace.json version
  - Sync nano-banana version to 0.0.5
  - **Validation:** Marketplace version matches plugin
  - **Estimated effort:** 5 minutes

## Dependencies Between Tasks

```
Phase 1 (Python) → Phase 2 (SKILL.md) → Phase 3 (References) → Phase 4 (Testing) → Phase 5 (Docs)
                     ↓
                  Task 4.4 can run in parallel after Task 2.1
```

## Total Estimated Effort

- Phase 1: 3-4 hours (Python script development)
- Phase 2: 25 minutes (Minimal SKILL.md changes)
- Phase 3: 1.75-2.25 hours (Detailed reference docs)
- Phase 4: 2-2.5 hours (Testing)
- Phase 5: 40 minutes (User-facing docs)

**Total: 8-10 hours** (reduced from 9-12 due to progressive disclosure strategy)

## Success Metrics

- ✅ Batch mode activates for 5+ slides
- ✅ Context usage <500 tokens for 10 slides
- ✅ Progress updates visible to user
- ✅ All errors handled gracefully
- ✅ Backward compatibility maintained
- ✅ Documentation complete and accurate
