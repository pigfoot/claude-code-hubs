# Imagen API - Complete Reference

This file contains complete code examples for Imagen image generation using `generate_images()` API.

---

## API Overview

**Method:** `client.models.generate_images()`
**Config:** `types.GenerateImagesConfig`
**Models:** `imagen-4.0-generate-001`, custom Imagen models

**Key Differences from Gemini API:**
- Use `prompt=` (string) NOT `contents=[]` (array)
- Can generate multiple images in one call (`number_of_images`)
- Supports `negative_prompt` parameter
- Different config class: `GenerateImagesConfig`

---

## Basic Image Generation

Complete heredoc example:

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

# Directory selection logic (same as Gemini)
existing_folders = sorted([d for d in Path(".").iterdir()
                          if d.is_dir() and len(d.name) >= 4
                          and d.name[:3].isdigit() and d.name[3] == '-'])
if existing_folders:
    last_num = int(existing_folders[-1].name[:3])
    next_num = last_num + 1
else:
    next_num = 1

OUTPUT_DIR = Path(f"{next_num:03d}-imagen-test")
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"Using output directory: {OUTPUT_DIR}")

# Configuration
# IMPORTANT: If NANO_BANANA_MODEL is set, use it - DO NOT override
model = os.environ.get("NANO_BANANA_MODEL")
if not model:
    model = "imagen-4.0-generate-001"  # Default Imagen model

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

    # Generate image(s) using Imagen API
    response = client.models.generate_images(
        model=model,
        prompt=user_prompt,  # String, NOT array
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",  # Optional
            negative_prompt="blurry, low quality",  # Optional
            include_rai_reason=True,  # Optional
            output_mime_type="image/jpeg"  # Optional
        )
    )

    if not response.generated_images:
        print("Error: No images generated in response")
        exit(1)

except Exception as e:
    print(f"Error during image generation: {e}")
    exit(1)

# Process generated images
for idx, generated_image in enumerate(response.generated_images):
    # Get the Image object
    img = generated_image.image

    # Convert to PIL Image from bytes
    pil_image = PILImage.open(io.BytesIO(img.image_bytes))

    # Save with format conversion
    if output_format in ("jpg", "jpeg"):
        output_path = OUTPUT_DIR / f"generated-{idx+1}.jpg"
        pil_image.convert("RGB").save(output_path, "JPEG", quality=quality)
    elif output_format == "webp":
        output_path = OUTPUT_DIR / f"generated-{idx+1}.webp"
        pil_image.save(output_path, "WEBP", quality=quality)
    else:  # png
        output_path = OUTPUT_DIR / f"generated-{idx+1}.png"
        pil_image.save(output_path, "PNG")

    print(f"Saved: {output_path}")

    # TrendLife Logo Overlay (ONLY for trendlife style)
    # Check if user requested TrendLife brand style
    if 'trendlife' in user_prompt.lower():
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from logo_overlay import overlay_logo, detect_layout_type

        # Detect layout type from prompt
        layout_type = detect_layout_type(user_prompt, slide_number=idx+1)

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

## Multiple Images Generation

Generate multiple images in one call:

```python
response = client.models.generate_images(
    model="imagen-4.0-generate-001",
    prompt="A professional product photo of running shoes",
    config=types.GenerateImagesConfig(
        number_of_images=4,  # Generate 4 variations
        aspect_ratio="1:1",
        negative_prompt="blurry, distorted, low resolution"
    )
)

# Access all images
for idx, generated_image in enumerate(response.generated_images):
    img = generated_image.image
    # Process each image...
```

---

## GenerateImagesConfig Parameters

Complete list of available parameters:

```python
config = types.GenerateImagesConfig(
    # Core parameters
    number_of_images=1,           # How many images to generate
    prompt_enhancement=True,       # Enhance the prompt automatically

    # Image properties
    aspect_ratio="16:9",          # "1:1", "16:9", "9:16", "4:3", "3:4"
    image_size="1K",              # "1K", "2K", "4K"

    # Quality control
    negative_prompt="blurry, low quality",
    guidance_scale=7.5,           # Prompt adherence (higher = stricter)
    seed=42,                      # For reproducible results

    # Output format
    output_mime_type="image/jpeg",  # "image/jpeg", "image/png", "image/webp"
    output_compression_quality=90,   # 0-100

    # Safety and metadata
    include_rai_reason=True,      # Include Responsible AI info
    include_safety_attributes=True,
    safety_filter_level="block_some",

    # Advanced
    person_generation="allow",    # Person generation policy
    add_watermark=False,          # Add watermark to images
    language="en"                 # Prompt language
)
```

---

## Code Snippets

### Minimal Example (for SKILL.md)

```python
response = client.models.generate_images(
    model="imagen-4.0-generate-001",
    prompt="A cute banana character",
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="1:1"
    )
)

for generated_image in response.generated_images:
    img = generated_image.image
    pil_image = PILImage.open(io.BytesIO(img.image_bytes))
    pil_image.save("output.webp")
```

### With Negative Prompt

```python
config = types.GenerateImagesConfig(
    number_of_images=1,
    aspect_ratio="16:9",
    negative_prompt="blurry, distorted, low resolution, bad anatomy",
    guidance_scale=8.0  # Higher = stronger prompt adherence
)
```

### High Quality Settings

```python
config = types.GenerateImagesConfig(
    number_of_images=1,
    aspect_ratio="1:1",
    image_size="4K",
    output_mime_type="image/png",
    guidance_scale=9.0,
    prompt_enhancement=True
)
```

---

## API Comparison: Imagen vs Gemini

| Feature | Imagen | Gemini |
|---------|--------|--------|
| **API Method** | `generate_images()` | `generate_content()` |
| **Config Type** | `GenerateImagesConfig` | `GenerateContentConfig` |
| **Prompt** | `prompt="string"` | `contents=["string"]` |
| **Multiple images** | ✅ `number_of_images` | ❌ One per call |
| **Negative prompt** | ✅ Supported | ❌ Not available |
| **Aspect ratio** | ✅ Supported | ✅ Supported |
| **Image size** | ✅ 1K/2K/4K | ✅ 1K/2K/4K |
| **Response** | `response.generated_images` | `response.parts` |

---

## Troubleshooting

### Common Errors

**Error: "Model not found"**
- Check model name spelling: `imagen-4.0-generate-001`
- Verify custom endpoint supports Imagen

**Error: "Invalid config parameter"**
- Using `response_modalities`? → That's Gemini only
- Using `image_config`? → Use flat parameters in `GenerateImagesConfig`

**No images returned:**
- Check `response.generated_images` (NOT `response.parts`)
- Verify prompt doesn't violate content policy
- Try simpler prompt to test connection
