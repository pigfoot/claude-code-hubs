# Logo Overlay (TrendLife Style)

## Automatic logo overlay

When `style: "trendlife"` is detected:

1. Detect layout type from prompt content (or use explicit `layout` field)
2. Build TrendLife-branded prompt with brand colors
3. **Featured layout** (title/divider/closing slides):
   - Logo passed as reference image to AI generation (Gemini: `image_url`; gpt-image-2: `/images/edits`)
   - AI integrates logo into the design naturally
4. **Content layout** (information slides):
   - Generate slide with brand colors only (no logo in prompt)
   - Apply logo overlay with `logo_overlay.overlay_logo()` post-generation
5. Output final image with logo

## Layout Detection Rules

Automatic detection based on keywords:

- **"title slide"**, **"cover slide"**, **"opening"** → title layout (15% logo, bottom-right)
- **"end slide"**, **"closing"**, **"thank you"**, **"conclusion"** → end layout (20% logo, center-bottom)
- **"divider"**, **"section break"** → divider layout (15% logo, bottom-right)
- **Slide number 1** (no keywords) → title layout (assumed opener)
- **Default** → content layout (12% logo, bottom-right)

## Manual Logo Overlay Override

Use when you need custom logo positioning. Must be run with `uv run` to ensure dependencies are available.

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pillow"]
# ///
# Run with: uv run --managed-python your_script.py

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from logo_overlay import overlay_logo, detect_layout_type

layout_type = detect_layout_type(prompt, slide_number=1)
# Or override: layout_type = 'title'  # 'title', 'content', 'divider', 'end'

logo_path = Path(__file__).parent / 'assets/logos/trendlife-2026-logo-light.png'

output_with_logo = output_path.with_stem(output_path.stem + '_with_logo')
overlay_logo(
    background_path=output_path,
    logo_path=logo_path,
    output_path=output_with_logo,
    layout_type=layout_type,
    opacity=1.0  # Optional: 0.0-1.0
)

output_with_logo.replace(output_path)
```

## Style Trigger Keywords

**Explicit:** `style: "trendlife"`

**Natural language:**

- "trendlife style"
- "use trendlife"
- "trendlife brand"
- "trendlife presentation"
