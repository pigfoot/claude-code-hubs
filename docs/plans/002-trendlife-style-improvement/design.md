# Design: TrendLife Style Implementation

## Overview

This document specifies the design for implementing TrendLife brand style in the nano-banana plugin using the Google hybrid approach: AI-generated images with precise Pillow-based logo overlay.

**Approach:** Generate branded slide backgrounds with Gemini/Imagen, then overlay Trend Micro logo using Pillow for pixel-perfect accuracy.

---

## Architecture

### High-Level Workflow

```
User Request
    ↓
Style Detection: "trendlife"
    ↓
┌─────────────────────────────────────┐
│  Phase 1: Image Generation          │
│  - Gemini/Imagen API                │
│  - TrendLife color palette in prompt│
│  - No logo in generated image       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Phase 2: Logo Overlay              │
│  - Load generated image (Pillow)    │
│  - Load logo asset                  │
│  - Calculate position based on      │
│    layout type                      │
│  - Composite with alpha blending    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Phase 3: Output                    │
│  - Save as lossless WebP            │
│  - Return file path                 │
└─────────────────────────────────────┘
```

### Component Breakdown

**1. Style Configuration (brand-styles.md)**
- Define TrendLife color palette
- Specify prompt template
- Reference logo asset path
- Define layout-specific logo positions

**2. Logo Asset Management**
- Store logo files in skill directory
- Support multiple logo variants (light/dark, different sizes)
- PNG format with transparency

**3. Image Generation (existing)**
- Use Gemini/Imagen API
- Inject TrendLife colors into prompt
- Generate without logo

**4. Logo Overlay Engine (new)**
- Pillow-based composition
- Position calculation
- Alpha blending
- Quality preservation

**5. Batch Generation Support (existing)**
- Apply logo overlay in batch mode
- Progress tracking includes overlay step

---

## Detailed Design

### 1. Style Configuration Structure

**Location:** `plugins/nano-banana/skills/nano-banana/references/brand-styles.md`

**New Section: TrendLife**

```markdown
## TrendLife

Corporate brand identity for Trend Micro's "Life" product line.

### Color Palette

**Primary Colors:**
| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Trend Red** | `#D71920` | Primary brand color, accents |
| **Guardian Red** | `#6F0000` | Supporting elements, intensity |
| Trend Red 80% | `#DE543B` | Tinted variations |
| Trend Red 40% | `#EDA389` | Light tinted variations |
| Black | `#000000` | Strong contrast |
| White | `#FFFFFF` | Clean backgrounds |

**Grays (Neutral Palette):**
| Gray Level | Hex Code |
|------------|----------|
| Dark Gray | `#57585B` |
| Medium Gray | `#808285` |
| Light Gray | `#E7E6E6` |

### Prompt Template

When `style: "trendlife"` is detected, append this to the user's prompt:

```
Use TrendLife brand colors for Trend Micro presentations:
- Primary: Trend Red (#D71920) for key elements and accents
- Guardian Red (#6F0000) for supporting elements and depth
- Neutral palette: Dark gray (#57585B), medium gray (#808285), light gray (#E7E6E6)
- Black (#000000) and white (#FFFFFF) for contrast
Keep the design clean, professional, and suitable for corporate presentations.
DO NOT include any logos or brand text - these will be added separately.
```

### Logo Configuration

**Logo Asset:**
- Path: `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png`
- Source: Extracted from TrendLife template (image3.png), cropped via srcRect
- Format: PNG with transparency (RGBA)
- Dimensions: 7693×1360 pixels (5.66:1 aspect ratio after srcRect crop)
- File size: ~150 KB

**Logo Positioning (All Layouts):**

**Based on actual TrendLife PowerPoint template slideLayout configuration (slideLayout11-19):**

| Property | Value |
|----------|-------|
| Position | Bottom-right corner (fixed for all layouts) |
| Size | 15.34% of slide width (294.6px at 1920×1080) |
| Padding (calibrated) | 17px from right edge, 20px from bottom |
| Visible Content Padding | 22px from right edge, 20px from bottom (measured) |
| Aspect Ratio | 5.66:1 (from PowerPoint srcRect crop) |
| Opacity | 100% |

**Position Calculations (16:9, 1920×1080 reference):**
- Logo width: `slide_width × 0.1534 = 294.6px`
- Logo height: `logo_width × (logo.height / logo.width) = 52.0px` (maintains native aspect)
- Logo position (frame): `x = slide_width - logo_width - 17px = 1608.4px`
- Logo position (frame): `y = slide_height - logo_height - 20px = 1008.0px`

**Calibration Notes:**
- XML EMU values give frame padding: (16.5, 20.5) → rounded to (17, 21)
- PowerPoint screenshot measurement gives visible content padding: (22, 20)
- Difference due to logo file's internal transparent margins (~6px right, ~3px top)
- Final code setting (17, 20) produces visible content padding of (22, 20)
- Matches PowerPoint exactly (verified via screenshot comparison)

**srcRect Cropping:**
- Original image3.png: 12532×1490 (8.4:1)
- srcRect values: l=0, t=1, r=38620, b=8728 (removes 38.62% right, 8.73% bottom)
- Cropped logo: 7692×1359 (5.66:1) - matches PowerPoint frame aspect ratio
- With `noChangeAspect=1`, displays complete "TRENDLIFE" text without distortion

### Style Guidelines

1. **Color Usage:**
   - Trend Red (#D71920) as primary accent
   - Guardian Red (#6F0000) for intensity
   - Neutral grays for backgrounds and structure
   - High contrast with black/white

2. **Design Principles:**
   - Clean, professional corporate aesthetic
   - Minimal text, maximum visual impact
   - Suitable for executive presentations

3. **Logo Treatment:**
   - Never distort or skew logo
   - Maintain minimum clear space around logo
   - Always use transparent PNG with full color
```

---

### 2. Logo Asset Directory Structure

**New Directory:**
```
plugins/nano-banana/skills/nano-banana/assets/
└── logos/
    ├── trendmicro-logo.png          # Primary logo (extracted from template)
    ├── trendmicro-logo-white.png    # White version (for dark backgrounds)
    └── README.md                    # Logo usage guidelines
```

**assets/logos/README.md:**
```markdown
# Brand Logo Assets

## Trend Micro Logo

**Source:** Official TrendLife PowerPoint template (image1.png)

**Usage:**
- Primary logo: Use on light backgrounds
- White logo: Use on dark backgrounds (if needed in future)

**Guidelines:**
- Never distort aspect ratio
- Maintain minimum clear space (10% of logo width)
- Always use PNG with transparency
- Never recreate or modify logo

**License:** Trend Micro brand assets, internal use only
```

---

### 3. Logo Overlay Implementation

**New Module:** `plugins/nano-banana/skills/nano-banana/logo_overlay.py`

```python
#!/usr/bin/env python3
"""
Logo overlay utilities for brand-styled slide generation.

Provides precise logo compositing using Pillow for pixel-perfect
brand element placement.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image as PILImage

# Logo positioning presets for 16:9 slides
# Based on actual TrendLife PowerPoint template slideLayout configuration
# Calibrated via screenshot comparison to match visible content position
LOGO_POSITIONS = {
    'title': {
        'position': 'bottom-right',
        'size_ratio': 0.1534,  # 15.34% of slide width (294.6px at 1920×1080)
        'padding': (17, 20),  # Calibrated to match PowerPoint visible content position
        'opacity': 1.0
    },
    'content': {
        'position': 'bottom-right',
        'size_ratio': 0.1534,  # Same size for all layouts (from template)
        'padding': (17, 20),
        'opacity': 1.0
    },
    'divider': {
        'position': 'bottom-right',
        'size_ratio': 0.1534,
        'padding': (17, 20),
        'opacity': 1.0
    },
    'end': {
        'position': 'bottom-right',  # All layouts use same position in template
        'size_ratio': 0.1534,
        'padding': (17, 20),
        'opacity': 1.0
    },
    'default': {
        'position': 'bottom-right',
        'size_ratio': 0.1534,
        'padding': (17, 20),
        'opacity': 1.0
    }
}


def calculate_logo_position(
    slide_width: int,
    slide_height: int,
    logo_width: int,
    logo_height: int,
    position: str,
    padding: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Calculate logo position coordinates based on placement strategy.

    Args:
        slide_width: Slide width in pixels
        slide_height: Slide height in pixels
        logo_width: Logo width in pixels
        logo_height: Logo height in pixels
        position: Position strategy ('bottom-right', 'center-bottom', etc.)
        padding: (x_padding, y_padding) in pixels

    Returns:
        (x, y) coordinates for logo top-left corner
    """
    x_pad, y_pad = padding

    if position == 'bottom-right':
        x = slide_width - logo_width - x_pad
        y = slide_height - logo_height - y_pad
    elif position == 'center-bottom':
        x = (slide_width - logo_width) // 2
        y = slide_height - logo_height - y_pad
    elif position == 'top-right':
        x = slide_width - logo_width - x_pad
        y = y_pad
    elif position == 'top-left':
        x = x_pad
        y = y_pad
    else:
        # Default to bottom-right
        x = slide_width - logo_width - x_pad
        y = slide_height - logo_height - y_pad

    return (x, y)


def resize_logo_proportional(
    logo: PILImage.Image,
    target_width: int
) -> PILImage.Image:
    """
    Resize logo to match PowerPoint template dimensions.

    Uses fixed aspect ratio from PowerPoint template (3.2:1 = 330×103px)
    instead of logo file's native aspect ratio. This mimics PowerPoint's
    internal cropping behavior.

    Args:
        logo: PIL Image object
        target_width: Desired width in pixels

    Returns:
        Resized logo image
    """
    # PowerPoint template uses fixed aspect ratio: 330×103 = 3.2:1
    # This effectively crops the logo regardless of source aspect ratio
    target_aspect_ratio = 103 / 330  # 0.3121
    target_height = int(target_width * target_aspect_ratio)

    return logo.resize(
        (target_width, target_height),
        PILImage.Resampling.LANCZOS  # High-quality resampling
    )


def overlay_logo(
    background_path: Path,
    logo_path: Path,
    output_path: Path,
    layout_type: str = 'default',
    opacity: Optional[float] = None
) -> Path:
    """
    Overlay logo on generated slide image with precise positioning.

    Args:
        background_path: Path to generated slide image
        logo_path: Path to logo PNG with transparency
        output_path: Path for output image
        layout_type: Layout type ('title', 'content', 'divider', 'end', 'default')
        opacity: Optional opacity override (0.0-1.0)

    Returns:
        Path to output image

    Raises:
        FileNotFoundError: If background or logo file not found
        ValueError: If layout_type is invalid
    """
    # Validate inputs
    if not background_path.exists():
        raise FileNotFoundError(f"Background image not found: {background_path}")
    if not logo_path.exists():
        raise FileNotFoundError(f"Logo not found: {logo_path}")

    # Get positioning configuration
    if layout_type not in LOGO_POSITIONS:
        layout_type = 'default'

    config = LOGO_POSITIONS[layout_type]
    final_opacity = opacity if opacity is not None else config['opacity']

    # Load images
    background = PILImage.open(background_path).convert('RGBA')
    logo = PILImage.open(logo_path).convert('RGBA')

    # Calculate target logo size
    slide_width, slide_height = background.size
    target_logo_width = int(slide_width * config['size_ratio'])

    # Resize logo proportionally
    logo_resized = resize_logo_proportional(logo, target_logo_width)

    # Apply opacity if needed
    if final_opacity < 1.0:
        alpha = logo_resized.split()[3]  # Get alpha channel
        alpha = alpha.point(lambda p: int(p * final_opacity))
        logo_resized.putalpha(alpha)

    # Calculate position
    logo_width, logo_height = logo_resized.size
    position = calculate_logo_position(
        slide_width, slide_height,
        logo_width, logo_height,
        config['position'],
        config['padding']
    )

    # Composite logo onto background
    background.paste(logo_resized, position, logo_resized)

    # Convert back to RGB if saving as JPEG, keep RGBA for PNG/WebP
    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
        background = background.convert('RGB')

    # Save with high quality
    if output_path.suffix.lower() == '.webp':
        background.save(output_path, 'WEBP', quality=95, lossless=True)
    elif output_path.suffix.lower() in ['.jpg', '.jpeg']:
        background.save(output_path, 'JPEG', quality=95, optimize=True)
    elif output_path.suffix.lower() == '.png':
        background.save(output_path, 'PNG', optimize=True)
    else:
        # Default to WebP
        background.save(output_path, 'WEBP', quality=95, lossless=True)

    return output_path


def detect_layout_type(prompt: str, slide_number: Optional[int] = None) -> str:
    """
    Detect layout type from prompt content for logo positioning.

    Args:
        prompt: User's slide prompt
        slide_number: Optional slide number (1-based)

    Returns:
        Layout type string ('title', 'content', 'divider', 'end', 'default')
    """
    prompt_lower = prompt.lower()

    # Title slide detection
    if any(word in prompt_lower for word in ['title slide', 'cover slide', 'opening']):
        return 'title'

    # End slide detection
    if any(word in prompt_lower for word in ['end slide', 'closing', 'thank you', 'conclusion']):
        return 'end'

    # Divider slide detection
    if any(word in prompt_lower for word in ['divider', 'section break', 'chapter']):
        return 'divider'

    # First slide is usually title
    if slide_number == 1:
        return 'title'

    # Default to content slide
    return 'content'
```

---

### 4. Integration with Existing Code

**Modify:** `plugins/nano-banana/skills/nano-banana/SKILL.md`

**Add section after "Style Detection":**

```markdown
## Logo Overlay (TrendLife Style)

**TrendLife style includes automatic logo overlay:**

When `style: "trendlife"` is detected:
1. Generate slide image with TrendLife colors (no logo in prompt)
2. Detect layout type from prompt content
3. Apply logo overlay with `logo_overlay.overlay_logo()`
4. Output final image with logo

**Layout Detection:**
- "title slide" → title layout (17.2% logo, bottom-right)
- "end slide" / "thank you" → end layout (17.2% logo, bottom-right)
- "divider" / "section" → divider layout (17.2% logo, bottom-right)
- Default → content layout (17.2% logo, bottom-right)

**Note:** All layouts use the same logo size and position per PowerPoint template master slide configuration.

**Manual Override:**
```python
# In heredoc script, after generation:
from logo_overlay import overlay_logo

overlay_logo(
    background_path=generated_image_path,
    logo_path=Path(__file__).parent / 'assets/logos/trendmicro-logo.png',
    output_path=final_output_path,
    layout_type='title',  # or 'content', 'divider', 'end'
    opacity=1.0
)
```
```

**Update heredoc template in SKILL.md:**

Add after image generation and before final output:

```python
# Apply TrendLife logo overlay if style is trendlife
if 'trendlife' in prompt.lower() or config.get('style') == 'trendlife':
    from pathlib import Path
    import sys

    # Import logo overlay module
    sys.path.insert(0, str(Path(__file__).parent))
    from logo_overlay import overlay_logo, detect_layout_type

    # Detect layout type
    layout_type = detect_layout_type(prompt, slide_number=1)

    # Logo path
    logo_path = Path(__file__).parent / 'assets/logos/trendmicro-logo.png'

    # Create temporary path for overlay
    temp_output = output_path.with_stem(output_path.stem + '_with_logo')

    # Apply logo
    overlay_logo(
        background_path=output_path,
        logo_path=logo_path,
        output_path=temp_output,
        layout_type=layout_type
    )

    # Replace original with logo version
    temp_output.replace(output_path)
```

---

### 5. Batch Generation Integration

**Modify:** `plugins/nano-banana/skills/nano-banana/generate_batch.py`

**Add logo overlay support in `generate_slide_gemini()` and `generate_slide_imagen()`:**

```python
def generate_slide_gemini(client: genai.Client, slide: Dict,
                          output_dir: Path, model: str,
                          output_format: str, quality: int) -> Tuple[bool, Optional[str], Optional[str]]:
    """Generate single slide using Gemini API with optional logo overlay."""
    try:
        # ... existing generation code ...

        # Save initial image
        initial_output = output_dir / f"slide-{slide_num:02d}_temp.{output_format}"
        # ... save logic ...

        # Check if logo overlay needed
        if slide.get('style') == 'trendlife':
            from logo_overlay import overlay_logo, detect_layout_type

            # Detect layout
            layout_type = detect_layout_type(
                slide['prompt'],
                slide_number=slide['number']
            )

            # Logo path
            logo_path = Path(__file__).parent / 'assets/logos/trendmicro-logo.png'

            # Final output path
            final_output = output_dir / f"slide-{slide_num:02d}.{output_format}"

            # Apply logo
            overlay_logo(
                background_path=initial_output,
                logo_path=logo_path,
                output_path=final_output,
                layout_type=layout_type
            )

            # Remove temp file
            initial_output.unlink()
            output_path = final_output
        else:
            # Rename temp to final
            output_path = output_dir / f"slide-{slide_num:02d}.{output_format}"
            initial_output.rename(output_path)

        # Get file size
        size_kb = output_path.stat().st_size // 1024

        return True, str(output_path), None

    except Exception as e:
        return False, None, str(e)
```

**Update config schema in batch-generation.md:**

```json
{
    "slides": [
        {
            "number": 1,
            "prompt": "Title slide for TrendLife presentation",
            "style": "trendlife"  // Triggers logo overlay
        }
    ],
    "output_dir": "/path/to/output/",
    "model": "gemini-3-pro-image-preview",
    "format": "webp",
    "quality": 90
}
```

---

## API Specifications

### Style Trigger

**Keyword Detection:**
- `style: "trendlife"` (explicit)
- `"use trendlife style"` (natural language)
- `"trendlife brand"` (natural language)

**Configuration:**
```python
{
    'style': 'trendlife',
    'layout_type': 'title',  # Optional: 'title', 'content', 'divider', 'end'
    'logo_opacity': 1.0      # Optional: 0.0-1.0
}
```

### Function Signatures

**logo_overlay.py:**

```python
def overlay_logo(
    background_path: Path,
    logo_path: Path,
    output_path: Path,
    layout_type: str = 'default',
    opacity: Optional[float] = None
) -> Path:
    """Overlay logo on background image."""
    ...

def detect_layout_type(
    prompt: str,
    slide_number: Optional[int] = None
) -> str:
    """Detect layout type from prompt."""
    ...

def calculate_logo_position(
    slide_width: int,
    slide_height: int,
    logo_width: int,
    logo_height: int,
    position: str,
    padding: Tuple[int, int]
) -> Tuple[int, int]:
    """Calculate logo coordinates."""
    ...

def resize_logo_proportional(
    logo: PILImage.Image,
    target_width: int
) -> PILImage.Image:
    """Resize logo maintaining aspect ratio."""
    ...
```

---

## Migration Plan

### Phase 1: Setup (Day 1)

- [ ] Create `assets/logos/` directory
- [ ] Extract and save logo from TrendLife template
- [ ] Create `logo_overlay.py` module with core functions
- [ ] Add TrendLife section to `brand-styles.md`

### Phase 2: Core Implementation (Day 2-3)

- [ ] Implement `overlay_logo()` function
- [ ] Implement `detect_layout_type()` function
- [ ] Implement position calculation logic
- [ ] Add unit tests for logo overlay

### Phase 3: Integration (Day 4)

- [ ] Update SKILL.md with TrendLife documentation
- [ ] Integrate logo overlay into single-slide workflow
- [ ] Integrate logo overlay into batch generation
- [ ] Update heredoc templates

### Phase 4: Testing (Day 5)

- [ ] Test single-slide generation with TrendLife style
- [ ] Test batch generation with mixed layouts
- [ ] Test different image resolutions
- [ ] Test logo positioning on various layouts
- [ ] Visual quality inspection

### Phase 5: Documentation & Deployment (Day 6)

- [ ] Update README with TrendLife examples
- [ ] Create example slides showcasing TrendLife style
- [ ] Update plugin version to 0.0.6
- [ ] Create migration guide from "trend" to "trendlife"

---

## Testing Strategy

### Unit Tests

**Test File:** `plugins/nano-banana/skills/nano-banana/test_logo_overlay.py`

```python
"""Unit tests for logo overlay functionality."""

import pytest
from pathlib import Path
from PIL import Image as PILImage
from logo_overlay import (
    overlay_logo,
    detect_layout_type,
    calculate_logo_position,
    resize_logo_proportional
)

def test_calculate_logo_position_bottom_right():
    """Test bottom-right positioning calculation."""
    x, y = calculate_logo_position(
        slide_width=1920,
        slide_height=1080,
        logo_width=295,
        logo_height=52,
        position='bottom-right',
        padding=(17, 20)
    )
    assert x == 1920 - 295 - 17  # 1608
    assert y == 1080 - 52 - 20   # 1008

def test_calculate_logo_position_center_bottom():
    """Test center-bottom positioning calculation."""
    x, y = calculate_logo_position(
        slide_width=1920,
        slide_height=1080,
        logo_width=400,
        logo_height=100,
        position='center-bottom',
        padding=(0, 50)
    )
    assert x == (1920 - 400) // 2
    assert y == 1080 - 100 - 50

def test_detect_layout_type_title():
    """Test title slide detection."""
    assert detect_layout_type("Create a title slide for our product") == 'title'
    assert detect_layout_type("Opening cover slide") == 'title'

def test_detect_layout_type_end():
    """Test end slide detection."""
    assert detect_layout_type("Create an end slide with thank you message") == 'end'
    assert detect_layout_type("Closing slide") == 'end'

def test_detect_layout_type_first_slide():
    """Test first slide defaults to title."""
    assert detect_layout_type("Some generic content", slide_number=1) == 'title'

def test_detect_layout_type_content():
    """Test content slide detection."""
    assert detect_layout_type("Show our product features", slide_number=3) == 'content'

def test_resize_logo_proportional():
    """Test logo resizing uses PowerPoint's fixed aspect ratio."""
    # Create dummy logo (any size, any aspect ratio)
    logo = PILImage.new('RGBA', (7769, 1490), color='red')

    resized = resize_logo_proportional(logo, target_width=330)

    assert resized.width == 330
    assert resized.height == 103  # Fixed 3.2:1 ratio from PowerPoint template

# Integration test (requires actual image files)
def test_overlay_logo_integration(tmp_path):
    """Test full logo overlay workflow."""
    # Create dummy background
    background = PILImage.new('RGB', (1920, 1080), color='white')
    bg_path = tmp_path / 'background.png'
    background.save(bg_path)

    # Create dummy logo
    logo = PILImage.new('RGBA', (400, 200), color=(215, 25, 32, 255))
    logo_path = tmp_path / 'logo.png'
    logo.save(logo_path)

    # Output path
    output_path = tmp_path / 'output.webp'

    # Run overlay
    result = overlay_logo(
        background_path=bg_path,
        logo_path=logo_path,
        output_path=output_path,
        layout_type='content'
    )

    assert result == output_path
    assert output_path.exists()

    # Verify output
    output = PILImage.open(output_path)
    assert output.size == (1920, 1080)
```

### Integration Tests

**Test Scenarios:**

1. **Single Slide Generation:**
   - Generate slide with `style: "trendlife"`
   - Verify logo is overlaid
   - Check logo position matches layout type
   - Verify image quality (lossless WebP)

2. **Batch Generation:**
   - Generate 5 slides with different layout types
   - Verify all slides have correctly positioned logos
   - Check consistency across batch

3. **Layout Type Detection:**
   - Test title slide detection
   - Test content slide detection
   - Test end slide detection
   - Test first slide defaults to title

4. **Different Resolutions:**
   - Test with 1920×1080 (Full HD)
   - Test with 2560×1440 (2K)
   - Test with 3840×2160 (4K)
   - Verify logo scales proportionally

5. **Error Handling:**
   - Missing logo file
   - Missing background image
   - Invalid layout type
   - Corrupted image files

### Manual QA Checklist

- [ ] Logo is sharp and clear (no blur)
- [ ] Logo maintains correct aspect ratio (not squashed/stretched)
- [ ] Logo position is consistent across slides
- [ ] Logo has appropriate padding from edges
- [ ] Colors match TrendLife palette exactly
- [ ] Output file size is reasonable (<1MB per slide)
- [ ] Lossless WebP format preserves quality
- [ ] Works with both Gemini and Imagen models

---

## Performance Considerations

### Benchmarks (Target)

- Logo overlay: <200ms per slide
- Total generation time: <15s per slide (including API call)
- Memory usage: <500MB during processing
- Batch generation: <3 minutes for 10 slides

### Optimization Strategies

1. **Reuse Logo Object:**
   - Load logo once, reuse for multiple slides
   - Cache resized logo versions

2. **Parallel Processing:**
   - In batch mode, parallelize logo overlay for multiple slides
   - Use `concurrent.futures` for thread-based parallelism

3. **Image Format:**
   - Use lossless WebP for optimal quality/size ratio
   - Avoid unnecessary format conversions

4. **Memory Management:**
   - Close PIL images after use
   - Use context managers for file operations

---

## Backward Compatibility

### Existing "Trend" Style

**Decision:** Keep both "trend" and "trendlife" styles

**"trend" style:**
- Remains unchanged
- No logo overlay
- For general Trend Micro branding

**"trendlife" style:**
- New implementation
- Includes logo overlay
- Specifically for TrendLife product presentations

### Migration Path

**For users currently using "trend" style:**

```python
# Old way (still works)
style: "trend"  # No logo overlay

# New way for TrendLife presentations
style: "trendlife"  # With logo overlay
```

**Documentation update:**
- Add section explaining difference between "trend" and "trendlife"
- Provide examples of when to use each
- No breaking changes for existing users

---

## Future Enhancements

### Phase 2 Features (Future)

1. **Multiple Logo Variants:**
   - White logo for dark backgrounds
   - Different sizes for different contexts
   - Automatic logo selection based on background color

2. **TrendAI Style:**
   - Implement second template (TrendAI)
   - Similar logo overlay approach
   - Different color palette

3. **Custom Logo Positions:**
   - Allow users to specify exact coordinates
   - Support for multiple logos per slide
   - Corner detection to avoid overlap with content

4. **Advanced Composition:**
   - Shadows and effects for logo
   - Gradient overlays for better logo visibility
   - Adaptive positioning based on image content

5. **Template Presets:**
   - Pre-defined slide sequences
   - Common presentation structures
   - One-command deck generation

---

## Success Metrics

### Quality Metrics

- [ ] Logo placement accuracy: 100% (pixel-perfect)
- [ ] Logo clarity: No visible blur or artifacts
- [ ] Color accuracy: Match TrendLife palette exactly
- [ ] User satisfaction: Positive feedback on logo quality

### Performance Metrics

- [ ] Logo overlay time: <200ms per slide
- [ ] Total generation time: <15s per slide
- [ ] Batch generation: <3min for 10 slides
- [ ] Memory usage: <500MB peak

### Adoption Metrics

- [ ] Documentation completeness: 100%
- [ ] Test coverage: >90%
- [ ] Example slides: Minimum 5 diverse examples
- [ ] User feedback: Collect and incorporate

---

## Appendix

### A. Logo Extraction Script

Used to extract logo from TrendLife template:

```bash
cd /tmp && mkdir trendlife-extracted
cd trendlife-extracted
unzip "plugins/nano-banana/skills/nano-banana/assets/templates/1201_TrendLife PowerPoint Deck.pptx"
cp ppt/media/image1.png /path/to/assets/logos/trendmicro-logo.png
```

### B. Color Verification

Verify colors in generated slides match specification:

```python
from PIL import Image
import colorsys

def verify_colors(image_path, expected_colors):
    """Check if image contains expected brand colors."""
    img = Image.open(image_path).convert('RGB')
    pixels = list(img.getdata())

    # Create histogram of colors
    color_counts = {}
    for pixel in pixels:
        hex_color = '#{:02x}{:02x}{:02x}'.format(*pixel)
        color_counts[hex_color] = color_counts.get(hex_color, 0) + 1

    # Check for expected colors
    for color in expected_colors:
        # Allow some tolerance for JPEG compression
        found = False
        for counted_color in color_counts:
            if color_distance(color, counted_color) < 10:
                found = True
                break
        if not found:
            print(f"Warning: Expected color {color} not found")
```

### C. Reference Implementation Timeline

**Week 1:**
- Day 1-2: Research and design (✅ Complete)
- Day 3-4: Core implementation
- Day 5: Integration and testing

**Week 2:**
- Day 1-2: Bug fixes and refinement
- Day 3: Documentation
- Day 4-5: Example creation and deployment

---

## Approval & Sign-off

**Design Reviewed By:** [User approval pending]

**Implementation Start Date:** TBD

**Target Completion Date:** TBD

**Version:** 0.0.6 (nano-banana plugin)
