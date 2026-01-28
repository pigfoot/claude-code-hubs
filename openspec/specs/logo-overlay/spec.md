# logo-overlay Specification

## Purpose

TBD - created by archiving change 002-trendlife-style-improvement. Update Purpose after archive.

## Requirements

### Requirement: Automatic Logo Overlay for Brand Styles

The system SHALL automatically overlay brand logos on AI-generated slides when a brand style (e.g., TrendLife) is
detected.

**ID:** `logo-overlay-001`
**Priority:** High

#### Scenario: TrendLife style triggers logo overlay

**Given:** User generates a slide with TrendLife style
**When:** Image generation completes
**Then:**

- TrendLife logo is automatically loaded from `assets/logos/trendlife-logo.png`
- Logo is overlaid on the generated image
- Logo positioning is determined by layout type
- Final image includes logo with pixel-perfect placement

#### Scenario: Non-brand style skips logo overlay

**Given:** User generates a slide without brand style
**When:** Image generation completes
**Then:**

- No logo overlay is performed
- Generated image is returned as-is
- Processing time is not impacted

#### Scenario: Logo overlay failure handling

**Given:** Logo file is missing or corrupted
**When:** Logo overlay is triggered
**Then:**

- Error is logged with clear message
- Generated image is returned without logo
- User is notified: "Warning: Logo overlay failed, image generated without logo"
- Generation continues successfully

**Rationale:** Automatic logo overlay ensures brand compliance without manual intervention while maintaining robustness.

---

### Requirement: Layout-Specific Logo Positioning

The system SHALL position logos differently based on detected slide layout type (title, content, divider, end).

**ID:** `logo-overlay-002`
**Priority:** High

#### Scenario: Title slide logo positioning

**Given:** Layout type is detected as "title"
**When:** Logo overlay is applied
**Then:**

- Logo is placed in bottom-right corner
- Logo width is 15% of slide width
- Padding: 40px from right edge, 30px from bottom edge
- Opacity: 100%

#### Scenario: Content slide logo positioning

**Given:** Layout type is detected as "content"
**When:** Logo overlay is applied
**Then:**

- Logo is placed in bottom-right corner
- Logo width is 12% of slide width
- Padding: 40px from right edge, 30px from bottom edge
- Opacity: 100%

#### Scenario: End slide logo positioning

**Given:** Layout type is detected as "end"
**When:** Logo overlay is applied
**Then:**

- Logo is placed in center-bottom position
- Logo width is 20% of slide width
- Padding: 0px horizontal (centered), 50px from bottom edge
- Opacity: 100%

**Position Configuration:**

| Layout | Position | Size Ratio | Padding (H, V) | Opacity |
|--------|----------|------------|----------------|---------|
| title | bottom-right | 15% | 40px, 30px | 100% |
| content | bottom-right | 12% | 40px, 30px | 100% |
| divider | bottom-right | 15% | 40px, 30px | 100% |
| end | center-bottom | 20% | 0px, 50px | 100% |
| default | bottom-right | 12% | 40px, 30px | 100% |

**Rationale:** Different layout types have different visual hierarchies requiring adaptive logo placement for optimal
appearance.

---

### Requirement: Automatic Layout Type Detection

The system SHALL automatically detect slide layout type from prompt content and slide position.

**ID:** `logo-overlay-003`
**Priority:** High

#### Scenario: Title slide detection from keywords

**Given:** User prompt contains "title slide", "cover slide", or "opening"
**When:** Layout detection runs
**Then:**

- Layout type is set to "title"
- Title-specific logo positioning is applied

#### Scenario: End slide detection from keywords

**Given:** User prompt contains "end slide", "closing", "thank you", or "conclusion"
**When:** Layout detection runs
**Then:**

- Layout type is set to "end"
- Center-bottom logo positioning is applied

#### Scenario: First slide defaults to title

**Given:** Slide number is 1 and no specific keywords present
**When:** Layout detection runs
**Then:**

- Layout type is set to "title"
- Assumed to be presentation opener

#### Scenario: Default to content layout

**Given:** No layout keywords detected and slide number > 1
**When:** Layout detection runs
**Then:**

- Layout type is set to "content"
- Standard logo positioning is applied

**Detection Logic:**

```
if "title slide" OR "cover" OR "opening" in prompt:
    return "title"
elif "end slide" OR "closing" OR "thank you" in prompt:
    return "end"
elif "divider" OR "section break" in prompt:
    return "divider"
elif slide_number == 1:
    return "title"
else:
    return "content"
```

**Rationale:** Automatic detection reduces user burden while maintaining flexibility for manual override if needed.

---

### Requirement: Logo Asset Management

The system SHALL maintain brand logo assets in an organized structure with proper documentation.

**ID:** `logo-overlay-004`
**Priority:** Medium

#### Scenario: Logo asset discovery

**Given:** Agent needs to apply logo overlay
**When:** Agent accesses logo assets
**Then:**

- Logos are located in `assets/logos/` directory
- Each logo has usage guidelines in `README.md`
- Logo file naming is consistent: `{brand}-logo.png`

**Asset Structure:**

```
assets/
├── logos/
│   ├── trendlife-logo.png    # TrendLife product logo (166 KB)
│   └── README.md              # Usage guidelines
└── templates/
    ├── 1201_TrendLife PowerPoint Deck.pptx
    └── README.md
```

#### Scenario: Logo usage guidelines

**Given:** Developer needs to add new brand logo
**When:** Developer reads `assets/logos/README.md`
**Then:**

- Logo specifications are documented (format, dimensions, DPI)
- Processing steps are provided (cropping, optimization)
- Usage constraints are clear (aspect ratio, minimum size)

**Rationale:** Organized asset management enables future expansion (TrendAI, white logos) and maintains quality
standards.

---

### Requirement: Precise Image Compositing with Alpha Blending

The system SHALL use Pillow library for pixel-perfect logo compositing with proper alpha channel handling.

**ID:** `logo-overlay-005`
**Priority:** High

#### Scenario: Logo overlay with transparency

**Given:** Logo is PNG with transparent background
**When:** Logo is overlaid on generated slide
**Then:**

- Alpha channel is properly preserved
- Logo edges are anti-aliased and smooth
- Background shows through transparent areas
- No white box or artifacts around logo

#### Scenario: Logo resizing maintains quality

**Given:** Logo needs to be resized to 12% of slide width
**When:** Logo is resized
**Then:**

- LANCZOS resampling algorithm is used
- Aspect ratio is maintained exactly
- Logo remains sharp at target size
- No pixelation or distortion occurs

#### Scenario: Lossless output format

**Given:** Logo overlay is complete
**When:** Final image is saved
**Then:**

- WebP format is used with lossless=True
- Quality is set to 95
- File size remains reasonable (<1MB per slide)
- Logo clarity is preserved

**Technical Requirements:**

- Use PIL/Pillow for image manipulation
- RGBA mode for all operations
- LANCZOS resampling for resize operations
- WebP lossless output format
- Alpha blending for compositing

**Rationale:** Pillow provides precise control over image quality while maintaining logo integrity, superior to
prompt-based logo generation.

---

### Requirement: Performance Targets for Logo Overlay

The system SHALL complete logo overlay operations within specified performance targets to maintain responsive user
experience.

**ID:** `logo-overlay-006`
**Priority:** Medium

#### Scenario: Single logo overlay performance

**Given:** Generated slide image is ready (1920×1080 pixels)
**When:** Logo overlay is performed
**Then:**

- Overlay completes in <200ms
- Memory usage stays below 100MB for single operation
- CPU usage is reasonable for background task

#### Scenario: Batch logo overlay performance

**Given:** 10 slides are generated in batch mode
**When:** Logo overlay is applied to all slides
**Then:**

- Total overlay time for 10 slides: <2 seconds
- Sequential processing (one at a time)
- Memory is released after each slide

**Performance Targets:**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Single overlay | <200ms | `time.time()` before/after |
| 10-slide batch | <2s total | Sum of individual timings |
| Memory per slide | <100MB | `tracemalloc` or similar |
| Output file size | <1MB | Actual file size check |

**Rationale:** Fast overlay operations ensure logo addition doesn't become a bottleneck in slide generation workflow.

---

### Requirement: Manual Override Capability

The system SHALL allow users to manually override logo positioning and opacity when needed.

**ID:** `logo-overlay-007`
**Priority:** Low

#### Scenario: Custom logo position override

**Given:** User needs logo in non-standard position
**When:** User provides manual override:

```python
overlay_logo(
    background_path=slide_path,
    logo_path=logo_path,
    output_path=output_path,
    layout_type='content',  # Override: force content layout
    opacity=0.8  # Override: 80% opacity
)
```

**Then:**

- Specified layout type is used instead of auto-detection
- Opacity is set to 80% as requested
- Manual configuration takes precedence over defaults

#### Scenario: No override provided

**Given:** User does not provide manual overrides
**When:** Logo overlay runs
**Then:**

- Automatic layout detection is used
- Default opacity (100%) is applied
- Standard behavior continues

**Rationale:** Manual override provides flexibility for edge cases while maintaining simple automatic behavior as
default.
