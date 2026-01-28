# batch-generation Specification Delta

## MODIFIED Requirements

### Requirement: Configuration File Creation

The system SHALL create a JSON configuration file containing all slide specifications before starting batch generation,
including optional style parameters for brand styling.

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

#### Scenario: Creating config with TrendLife brand style

**Given:** User requests "Generate 5 slides for TrendLife presentation"
**When:** Claude prepares batch generation
**Then:**

- Config JSON includes `"style": "trendlife"` for each slide
- Logo overlay will be automatically applied during generation
- Brand colors are injected into prompts

**TrendLife Config Example:**

```json
{
  "slides": [
    {"number": 1, "prompt": "TrendLife product overview", "style": "trendlife"},
    {"number": 2, "prompt": "Key features", "style": "trendlife"},
    {"number": 3, "prompt": "Security benefits", "style": "trendlife"}
  ],
  "output_dir": "/home/user/trendlife-deck/",
  "model": "gemini-3-pro-image-preview",
  "format": "webp",
  "quality": 90
}
```

**Rationale:** Structured config enables Python script to run independently with brand style support.

---

## ADDED Requirements

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
