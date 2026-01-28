# Change: TrendLife Brand Style with Logo Overlay

## Why

The nano-banana plugin currently has a "Trend Micro" style that provides generic Trend Micro branding. However, this
style:

1. **Lacks logo overlay** - No brand logo appears on generated slides
2. **Lacks specificity** - Named after corporate brand rather than product line (TrendLife)
3. **Missing layout intelligence** - No layout-specific logo positioning for different slide types

TrendLife is the primary product line requiring branded presentations with:

1. **Official brand colors** from the TrendLife PowerPoint template (Trend Red #D71920, Guardian Red #6F0000)
2. **TrendLife logo** that must appear correctly positioned on all slides
3. **Layout-specific logo positioning** (title, content, divider, and end slides require different placements)

Current AI image generation models cannot reliably render brand logos with sufficient quality and accuracy. Industry
best practice (Google's approach) recommends generating slide backgrounds with AI, then overlaying logos using precise
image compositing tools like Pillow.

## What Changes

This change **renames** the existing "Trend Micro" style to **"TrendLife"** and adds automated logo overlay support:

### Core Capabilities

1. **Brand Styling**
   - **Rename** "Trend Micro" section to "TrendLife" in `references/brand-styles.md`
   - Update style detection to use "trendlife" keyword (was: "trend")
   - Enhance existing TrendLife color palette with logo overlay support

2. **Logo Overlay System**
   - New `logo_overlay.py` module with four main functions:
     - `overlay_logo()` - Composite logo onto generated slides
     - `detect_layout_type()` - Auto-detect slide type from prompt
     - `calculate_logo_position()` - Compute placement coordinates
     - `resize_logo_proportional()` - Scale logo using PowerPoint's fixed aspect ratio (3.2:1)
   - **PowerPoint template-based positioning** (extracted from master slide XML):
     - All layouts use same position: bottom-right corner
     - Size: 17.2% of slide width (330×103px at 1920×1080)
     - Padding: 14px from right edge, 1px from bottom
     - Fixed aspect ratio: 3.2:1 (mimics PowerPoint's internal cropping behavior)
   - Support for opacity and custom positioning

3. **Asset Organization**
   - Create `assets/logos/` directory for brand logos
   - Move TrendLife PowerPoint template to `assets/templates/`
   - Store extracted logo: `assets/logos/trendlife-logo.png` (7769×1490px, 166 KB)

4. **Integration**
   - Update `SKILL.md` to document TrendLife style usage
   - Integrate logo overlay into single-slide generation workflow
   - Integrate logo overlay into batch generation (`generate_batch.py`)
   - Auto-trigger logo overlay when TrendLife style is detected

### Breaking Change

- **BREAKING:** "trend" style keyword is renamed to "trendlife"
- Users using `style: "trend"` must update to `style: "trendlife"`
- Rationale: Simplifies naming, avoids confusion between corporate brand and product brand

## Impact

### Affected Capabilities

- **brand-styling** (NEW) - TrendLife color palette and style definitions
- **logo-overlay** (NEW) - Logo compositing system
- **batch-generation** (MODIFIED) - Add logo overlay support for TrendLife style

### Affected Files

**New Files:**

- `plugins/nano-banana/skills/nano-banana/logo_overlay.py` - Logo overlay module
- `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png` - TrendLife logo asset
- `plugins/nano-banana/skills/nano-banana/assets/logos/README.md` - Logo usage guidelines
- `plugins/nano-banana/skills/nano-banana/assets/templates/1201_TrendLife PowerPoint Deck.pptx` - Reference template
- `plugins/nano-banana/skills/nano-banana/assets/templates/README.md` - Template documentation
- `plugins/nano-banana/skills/nano-banana/assets/README.md` - Assets directory overview

**Modified Files:**

- `plugins/nano-banana/skills/nano-banana/SKILL.md` - Add TrendLife style documentation
- `plugins/nano-banana/skills/nano-banana/references/brand-styles.md` - Add TrendLife section
- `plugins/nano-banana/skills/nano-banana/generate_batch.py` - Integrate logo overlay

### Testing Requirements

- Unit tests for logo overlay functions (positioning, resizing, detection)
- Integration tests for single-slide and batch generation
- Visual quality inspection across different resolutions (1920×1080, 2560×1440, 3840×2160)
- Layout type detection accuracy tests

### Performance Targets

- Logo overlay: <200ms per slide
- Total generation time: <15s per slide (including API call)
- Batch generation: <3 minutes for 10 slides
- Memory usage: <500MB peak

## Design Reference

Complete technical design and implementation details are documented in:

- [docs/plans/002-trendlife-style-improvement/design.md](/home/pigfoot/proj/claude-code-hubs/docs/plans/002-trendlife-style-improvement/design.md)

Key decisions:

- **Google hybrid approach** (AI generation + Pillow overlay) chosen over prompt-based logo generation for reliability
- **Layout detection** uses keyword matching + slide number heuristics
- **Lossless WebP** format for final output to preserve quality
- **Pillow library** for image compositing (already available in Python environment)
