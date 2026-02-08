# brand-styling Specification (Delta)

## ADDED Requirements

### Requirement: Title Slide Reference Image Integration

The system SHALL use TrendLife logo as a reference image when generating title/cover slides with Gemini API,
enabling professional brand integration by AI.

**ID:** `brand-styling-005`
**Priority:** High

#### Scenario: Title slide uses logo as reference image (Gemini API)

**WHEN** Generating a TrendLife title slide using Gemini API
**THEN**:

- Layout type is detected as "title"
- Logo file loaded as PIL Image: `assets/logos/trendlife-2026-logo-light.png`
- Git LFS pointer check performed on logo file
- Logo passed to Gemini as reference image in contents array: `contents = [prompt, logo_image]`
- Prompt enhanced with title slide instructions (see Title Slide Prompt Enhancement)
- AI generates cover design incorporating logo professionally
- Logo appears integrated in final image (not corner overlay)

#### Scenario: Content slide uses standard brand colors (no reference image)

**WHEN** Generating a TrendLife content slide (non-title)
**THEN**:

- Layout type is detected as "content", "divider", or "end"
- Logo is NOT passed as reference image
- Standard brand color prompt enhancement applied
- AI generates slide with brand colors only
- Logo added via post-processing overlay

#### Scenario: Imagen API title slide falls back to overlay

**WHEN** Generating a TrendLife title slide using Imagen API
**THEN**:

- Warning logged: "Imagen API does not support reference images for TrendLife title slides"
- Prompt enhanced with brand colors (standard enhancement)
- Image generated without reference logo
- Logo added via post-processing overlay (bottom-right corner)
- Result is functional but not as polished as Gemini

#### Scenario: Git LFS pointer detected during reference image loading

**WHEN** Loading logo as reference image and file is Git LFS pointer
**THEN**:

- PIL Image.open() fails
- Git LFS detection logic identifies pointer file
- Error message printed with installation instructions
- Function returns error: "Logo file is Git LFS pointer - run git lfs pull"
- Slide generation fails for this slide

**Rationale:** Gemini API's multi-modal content support enables passing logo as reference image, allowing AI to
create professional cover designs with integrated branding. This is superior to simple corner overlays for
title slides.

**Reference Image API Usage:**

```python
from PIL import Image as PILImage

# Load logo as reference
logo_image = PILImage.open(logo_path)

# Pass as multi-modal content to Gemini
contents = [prompt, logo_image]
response = client.models.generate_content(
    model=model,
    contents=contents,
    config=config
)
```

---

### Requirement: Title Slide Prompt Enhancement

The system SHALL enhance prompts for TrendLife title slides with specific instructions for logo integration
and brand compliance.

**ID:** `brand-styling-006`
**Priority:** High

#### Scenario: Title slide prompt includes logo integration instructions

**WHEN** Generating a TrendLife title slide with reference image
**THEN**:

- Base prompt is preserved (user's original text)
- Prompt is appended with title slide enhancement:

  ```
  This is a title/cover slide for TrendLife (Trend Micro presentations).
  Create a professional cover design that incorporates the TrendLife logo provided as reference image.
  Use TrendLife brand colors:
  - Trend Red (#D71920) for title and accents
  - Supporting colors: Guardian Red (#6F0000), Dark gray (#57585B), Medium gray (#808285), Light gray (#E7E6E6)
  - Black (#000000) for text, white (#FFFFFF) for backgrounds
  IMPORTANT: Use the exact logo from the reference image - DO NOT modify, redraw, or stylize the logo.
  Position it prominently (typically center or upper area).
  Keep the design clean and professional.
  ```

#### Scenario: Content slide prompt uses standard enhancement

**WHEN** Generating a TrendLife content slide (non-title)
**THEN**:

- Base prompt is preserved
- Prompt is appended with standard brand color enhancement (existing behavior)
- No logo integration instructions (logo will be overlaid)

#### Scenario: Logo trademark protection in prompt

**WHEN** Title slide prompt is enhanced
**THEN**:

- Prompt includes: "IMPORTANT: Use the exact logo from the reference image - DO NOT modify, redraw, or stylize the logo"
- AI is instructed to treat logo as immutable trademark
- Logo positioning suggested but not mandated: "typically center or upper area"
- Design flexibility maintained while protecting brand integrity

**Rationale:** Title slides require different prompt enhancement than content slides to guide AI toward
professional cover design. Logo trademark protection is critical - AI must not alter or redraw the logo.

---

### Requirement: Reference Image Documentation

The system SHALL document the reference image feature and its limitations in brand styling documentation.

**ID:** `brand-styling-007`
**Priority:** Medium

#### Scenario: Reference image feature documented in brand-styles.md

**WHEN** Claude reads `references/brand-styles.md`
**THEN**:

- Reference image feature is documented for title slides
- Gemini API support is noted
- Imagen API limitation is documented (no reference image support)
- Logo path updated to 2026 version
- Usage examples show correct API invocation

#### Scenario: SKILL.md explains title slide behavior

**WHEN** Claude reads SKILL.md
**THEN**:

- Title slide special handling is documented
- Difference between title and content slides explained
- Reference image concept is explained for Claude's usage
- Git LFS requirements are emphasized (logo file needed for reference)

#### Scenario: Logo specifications updated for 2026 file

**WHEN** Claude reads `assets/logos/README.md`
**THEN**:

- 2026 logo dimensions documented: 2780×511 pixels
- File name documented: `trendlife-2026-logo-light.png`
- Git LFS management noted
- Usage context includes reference image feature

**Rationale:** Documentation ensures Claude understands when and how to use reference images, and what
limitations exist (Imagen API). Logo file updates must be reflected in all documentation.

---

### Requirement: Logo File Path Update in Brand Styling

The system SHALL reference the 2026 TrendLife logo file in all brand styling documentation and code.

**ID:** `brand-styling-008`
**Priority:** High

#### Scenario: Brand style documentation uses 2026 logo path

**WHEN** Documentation references TrendLife logo
**THEN**:

- Path is: `assets/logos/trendlife-2026-logo-light.png`
- Legacy path `trendlife-logo.png` is NOT mentioned
- Dimensions reflect 2026 file: 2780×511

#### Scenario: Code examples show correct logo path

**WHEN** SKILL.md or brand-styles.md includes code examples
**THEN**:

- Logo path in examples: `"assets/logos/trendlife-2026-logo-light.png"`
- Example code is syntactically correct
- Path is relative to script location

**Rationale:** Logo file path must be consistent across all documentation to avoid confusion and ensure correct
file is loaded.
