# Gemini Image Generation API - Complete Reference

This file contains complete code examples for Gemini image generation using `generate_content()` API.

---

## API Overview

**Method:** `client.models.generate_content()`
**Config:** `types.GenerateContentConfig`
**Models:** `gemini-3-pro-image-preview`, `gemini-2.5-flash-image`

---

## Basic Image Generation

Complete heredoc example with all features:

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
import os
import io
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image as PILImage

# User's prompt (replace with actual prompt)
user_prompt = "A cute banana character with sunglasses"

# Directory selection logic
# Claude decides based on conversation context and user intent:
# - Continuation of existing work → Specify existing directory
# - New unrelated topic → Use auto-increment
# - Uncertain → Ask user with AskUserQuestion

# Option 1: Reuse existing directory (for continuation)
# OUTPUT_DIR = Path("001-existing-topic")  # Manually specify

# Option 2: Auto-increment for new topic (default)
existing_folders = sorted([d for d in Path(".").iterdir()
                          if d.is_dir() and len(d.name) >= 4
                          and d.name[:3].isdigit() and d.name[3] == '-'])
if existing_folders:
    last_num = int(existing_folders[-1].name[:3])
    next_num = last_num + 1
else:
    next_num = 1

OUTPUT_DIR = Path(f"{next_num:03d}-cute-banana")  # Format: NNN-short-name

OUTPUT_DIR.mkdir(exist_ok=True)
print(f"Using output directory: {OUTPUT_DIR}")

# Configuration from environment variables
# IMPORTANT: If NANO_BANANA_MODEL is set, use it - DO NOT override
model = os.environ.get("NANO_BANANA_MODEL")
if not model:
    # Only choose model when NANO_BANANA_MODEL is not set
    # Claude decides based on user request:
    # - Use "gemini-2.5-flash-image" ONLY if user explicitly mentions speed/budget
    # - Use "gemini-3-pro-image-preview" (default) for quality, slides, or normal requests
    model = "gemini-3-pro-image-preview"  # Replace with appropriate choice

output_format = os.environ.get("NANO_BANANA_FORMAT", "webp").lower()
quality = int(os.environ.get("NANO_BANANA_QUALITY", "90"))

# Detect if lossless format is needed (for diagrams/slides)
# See "Lossless WebP Decision Logic" in SKILL.md Configuration section for complete rules
use_lossless = False  # Set to True for slide deck styles or explicit user request

# Initialize client with optional custom endpoint
base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
    exit(1)

try:
    if base_url:
        client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
    else:
        client = genai.Client(api_key=api_key)

    config_params = {
        'response_modalities': ['IMAGE'],
        'image_config': types.ImageConfig(
            aspect_ratio='16:9',  # "1:1", "16:9", "9:16", "4:3", "3:4"
            image_size='2K'       # "1K", "2K", "4K"
        )
    }

    response = client.models.generate_content(
        model=model,
        contents=[user_prompt],
        config=types.GenerateContentConfig(**config_params)
    )

    if not response.parts:
        print("Error: No image generated in response")
        exit(1)

except Exception as e:
    print(f"Error during image generation: {e}")
    exit(1)

for part in response.parts:
    if part.inline_data is not None:
        # Get google-genai Image object
        genai_image = part.as_image()

        # Convert to PIL Image from bytes
        pil_image = PILImage.open(io.BytesIO(genai_image.image_bytes))

        # Save with format conversion
        if output_format in ("jpg", "jpeg"):
            output_path = OUTPUT_DIR / "generated.jpg"
            pil_image.convert("RGB").save(output_path, "JPEG", quality=quality)
        elif output_format == "webp":
            output_path = OUTPUT_DIR / "generated.webp"
            if use_lossless:
                # Lossless WebP for slide decks (VP8L encoding)
                # Saves 20-30% vs PNG, zero quality loss (vs lossy: saves 95% but blurs)
                pil_image.save(output_path, "WEBP", lossless=True)
                print(f"Saved: {output_path} (WEBP lossless, optimized for slides)")
            else:
                # Lossy WebP for photos (VP8 encoding)
                pil_image.save(output_path, "WEBP", quality=quality)
                print(f"Saved: {output_path} (WEBP, quality={quality})")
        else:  # png (default fallback)
            output_path = OUTPUT_DIR / "generated.png"
            pil_image.save(output_path, "PNG")
            print(f"Saved: {output_path} (PNG)")

        # TrendLife Logo Overlay (ONLY for trendlife style)
        # Check if user requested TrendLife brand style
        if 'trendlife' in user_prompt.lower():
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from logo_overlay import overlay_logo, detect_layout_type

            # Detect layout type from prompt
            layout_type = detect_layout_type(user_prompt, slide_number=1)

            # Logo path
            logo_path = Path(__file__).parent / 'assets/logos/trendlife-logo.png'

            # Create temporary path for overlay
            temp_output = output_path.with_stem(output_path.stem + '_with_logo')

            try:
                # Apply logo overlay
                overlay_logo(
                    background_path=output_path,
                    logo_path=logo_path,
                    output_path=temp_output,
                    layout_type=layout_type
                )

                # Replace original with logo version
                temp_output.replace(output_path)
                print(f"Applied TrendLife logo overlay ({layout_type} layout)")
            except Exception as e:
                print(f"Warning: Logo overlay failed - {e}")
                # Continue without logo if overlay fails
EOF
```

---

## Image Editing

Load existing image and include in request:

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
import os
import io
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image as PILImage

# Directory selection: Editing existing image = same topic
# Reuse the source image's directory for edited output
OUTPUT_DIR = Path("001-cute-banana")  # Same directory as source image
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"Using output directory: {OUTPUT_DIR}")

# Configuration from environment variables
# IMPORTANT: If NANO_BANANA_MODEL is set, use it - DO NOT override
model = os.environ.get("NANO_BANANA_MODEL")
if not model:
    # Only choose model when NANO_BANANA_MODEL is not set
    model = "gemini-3-pro-image-preview"  # Replace with appropriate choice

output_format = os.environ.get("NANO_BANANA_FORMAT", "webp").lower()
quality = int(os.environ.get("NANO_BANANA_QUALITY", "90"))

# Initialize client
base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
    exit(1)

try:
    if base_url:
        client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
    else:
        client = genai.Client(api_key=api_key)

    # Load existing image
    img = PILImage.open("001-cute-banana/generated.webp")

    response = client.models.generate_content(
        model=model,
        contents=[
            "Add a party hat to this character",
            img  # Pass PIL Image directly
        ],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )

    if not response.parts:
        print("Error: No image generated in response")
        exit(1)

except FileNotFoundError as e:
    print(f"Error: Input image not found: {e}")
    exit(1)
except Exception as e:
    print(f"Error during image editing: {e}")
    exit(1)

for part in response.parts:
    if part.inline_data is not None:
        genai_image = part.as_image()
        pil_image = PILImage.open(io.BytesIO(genai_image.image_bytes))

        if output_format in ("jpg", "jpeg"):
            output_path = OUTPUT_DIR / "edited.jpg"
            pil_image.convert("RGB").save(output_path, "JPEG", quality=quality)
        elif output_format == "webp":
            output_path = OUTPUT_DIR / "edited.webp"
            pil_image.save(output_path, "WEBP", quality=quality)
        else:  # png
            output_path = OUTPUT_DIR / "edited.png"
            pil_image.save(output_path, "PNG")

        print(f"Saved: {output_path}")
EOF
```

---

## Image Configuration

### Aspect Ratio and Resolution

```python
config_params = {
    'response_modalities': ['IMAGE'],
    'image_config': types.ImageConfig(
        aspect_ratio="16:9",  # "1:1", "16:9", "9:16", "4:3", "3:4"
        image_size="2K"       # "1K", "2K", "4K" (UPPERCASE required)
    )
}

config = types.GenerateContentConfig(**config_params)
```

### Common Aspect Ratios

| Aspect Ratio | Use Cases | Best For |
|--------------|-----------|----------|
| **16:9** | Presentation slides, modern displays, YouTube thumbnails | Widescreen presentations, video content |
| **4:3** | Traditional presentations, documents | Classic PowerPoint format, printed slides |
| **1:1** | Social media posts, profile images | Instagram posts, icons, square designs |
| **9:16** | Mobile vertical, stories | Instagram/TikTok stories, mobile-first content |
| **3:4** | Print materials, posters | Printed documents, portrait orientation |

### Resolution Recommendations

- **1K**: Quick drafts, previews (faster generation)
- **2K**: Standard quality for most use cases (recommended default)
- **4K**: High-resolution prints, detailed graphics (slower generation)

---

## Code Snippets

### Minimal Example (for SKILL.md)

```python
response = client.models.generate_content(
    model=model,  # gemini-3-pro-image-preview or gemini-2.5-flash-image
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)
```

### Client Initialization

```python
from google import genai

base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if base_url:
    client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
else:
    client = genai.Client(api_key=api_key)
```

### Processing Response

```python
for part in response.parts:
    if part.inline_data:
        genai_image = part.as_image()
        pil_image = PILImage.open(io.BytesIO(genai_image.image_bytes))
        pil_image.save("output.webp", "WEBP")
```
