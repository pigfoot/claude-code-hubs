# logo-overlay Specification (Delta)

## MODIFIED Requirements

### Requirement: Automatic Logo Overlay for Brand Styles

The system SHALL automatically overlay brand logos on AI-generated slides when a brand style (e.g., TrendLife)
is detected, EXCEPT for title/cover slides where logo is included during generation.

**ID:** `logo-overlay-001`
**Priority:** High

#### Scenario: TrendLife content slide triggers logo overlay

**WHEN** User generates a content slide (non-title) with TrendLife style
**THEN**:

- TrendLife logo is automatically loaded from `assets/logos/trendlife-2026-logo-light.png`
- Logo is overlaid on the generated image
- Logo positioning is determined by layout type
- Final image includes logo with pixel-perfect placement

#### Scenario: TrendLife title slide skips logo overlay

**WHEN** User generates a title/cover slide with TrendLife style
**THEN**:

- Layout type is detected as "title"
- Logo overlay step is SKIPPED (logo already in generated image)
- Generated image is returned as-is
- No post-processing overlay performed
- Title slide has logo integrated by AI during generation

#### Scenario: Non-brand style skips logo overlay

**WHEN** User generates a slide without brand style
**THEN**:

- No logo overlay is performed
- Generated image is returned as-is
- Processing time is not impacted

#### Scenario: Logo overlay failure with Git LFS detection

**WHEN** Logo file is a Git LFS pointer or corrupted
**THEN**:

- Git LFS pointer detection logic runs
- If LFS pointer: Error message with installation instructions
- If other error: Original error logged
- Generated image is returned without logo (for non-fatal errors)
- User is notified: "Warning: Logo overlay failed for slide N: ..."
- Generation continues for remaining slides

**Rationale:** Title slides use logo as reference image during AI generation for professional integration.
Only content, divider, and end slides need post-processing overlay. Logo file path updated to 2026 version.
Git LFS detection improves error handling.

---

### Requirement: Layout-Specific Logo Positioning

The system SHALL position logos differently based on detected slide layout type (content, divider, end),
EXCLUDING title slides which do not receive post-processing overlay.

**ID:** `logo-overlay-002`
**Priority:** High

#### Scenario: Content slide logo positioning

**WHEN** Layout type is detected as "content" and overlay is applied
**THEN**:

- Logo is placed in bottom-right corner
- Logo width is 12% of slide width
- Padding: 40px from right edge, 30px from bottom edge
- Opacity: 100%

#### Scenario: Divider slide logo positioning

**WHEN** Layout type is detected as "divider" and overlay is applied
**THEN**:

- Logo is placed in bottom-right corner
- Logo width is 15% of slide width
- Padding: 40px from right edge, 30px from bottom edge
- Opacity: 100%

#### Scenario: End slide logo positioning

**WHEN** Layout type is detected as "end" and overlay is applied
**THEN**:

- Logo is placed in center-bottom position
- Logo width is 20% of slide width
- Padding: 0px horizontal (centered), 50px from bottom edge
- Opacity: 100%

#### Scenario: Title slide positioning not applicable

**WHEN** Layout type is detected as "title"
**THEN**:

- Post-processing overlay is NOT applied
- Logo positioning logic is NOT invoked
- Title slide logo is positioned by AI during generation (not overlay)

**Updated Position Configuration:**

| Layout | Overlay Applied? | Position | Size Ratio | Padding (H, V) | Opacity |
|--------|------------------|----------|------------|----------------|---------|
| title | **NO** (skipped) | N/A (AI-generated) | N/A | N/A | N/A |
| content | YES | bottom-right | 12% | 40px, 30px | 100% |
| divider | YES | bottom-right | 15% | 40px, 30px | 100% |
| end | YES | center-bottom | 20% | 0px, 50px | 100% |
| default | YES | bottom-right | 12% | 40px, 30px | 100% |

**Rationale:** Title slides use logo as reference image for AI generation, requiring different handling than
other layout types. Positioning table updated to reflect this architectural change.

---

## ADDED Requirements

### Requirement: Logo File Path Update

The system SHALL use the 2026 TrendLife logo file (`trendlife-2026-logo-light.png`) for all logo operations,
replacing the legacy logo file.

**ID:** `logo-overlay-008`
**Priority:** High

#### Scenario: Logo loaded from 2026 file path

**WHEN** System needs to load TrendLife logo
**THEN**:

- Logo path is: `assets/logos/trendlife-2026-logo-light.png`
- File dimensions: 2780×511 pixels
- File format: PNG with transparency
- Git LFS managed (requires git lfs pull)

#### Scenario: Percentage-based sizing adapts to new logo dimensions

**WHEN** Logo is resized for overlay
**THEN**:

- Resize calculation uses percentage of slide width (12%, 15%, or 20%)
- Aspect ratio maintained (2780:511 ≈ 5.44:1)
- LANCZOS resampling used for quality
- Final size adapts automatically to new logo dimensions

#### Scenario: Legacy logo file not used

**WHEN** System searches for logo files
**THEN**:

- Path `assets/logos/trendlife-logo.png` is NOT referenced
- Legacy file (7693×1360) is NOT loaded
- Only 2026 logo file is used

**Rationale:** 2026 TrendLife logo is the current brand asset. Percentage-based sizing in existing code
automatically adapts to new dimensions (2780×511 vs. old 7693×1360) without positioning logic changes.
