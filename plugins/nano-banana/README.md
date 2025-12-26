# Nano Banana Plugin

Python scripting and Gemini image generation using uv with inline script dependencies.

## Features

- **Image Generation**: Generate images using Google's Gemini models
- **Image Editing**: Edit existing images with AI
- **Python Scripting**: Run Python scripts with uv using heredocs
- **Inline Dependencies**: Self-contained scripts with `# /// script` metadata

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable set with a valid Gemini API key

## Configuration

Customize plugin behavior using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NANO_BANANA_MODEL` | (Claude chooses: Pro or Flash) | Force specific model (overrides Claude's choice) |
| `NANO_BANANA_FORMAT` | `webp` | Output image format: `webp`, `jpg`, or `png` |
| `NANO_BANANA_QUALITY` | `90` | Image quality (1-100) for webp/jpg formats |
| `GOOGLE_GEMINI_BASE_URL` | (official API) | Custom API endpoint (for non-official deployments) |
| `GEMINI_API_KEY` | (falls back to `GOOGLE_API_KEY`) | API key (official or custom endpoint) |

### Examples

**Official Google API (default):**
```bash
export GEMINI_API_KEY="your-api-key"  # Or GOOGLE_API_KEY (backward compatible)
# Model: Claude chooses Pro (default) or Flash (budget/fast) automatically
# Optional: force specific model or format
# export NANO_BANANA_MODEL="gemini-2.5-flash-image"
# export NANO_BANANA_FORMAT="jpg"
```

**Custom Endpoint (self-hosted or proxy):**
```bash
export GOOGLE_GEMINI_BASE_URL="https://your-api.example.com/v1"
export GEMINI_API_KEY="your-custom-api-key"
export NANO_BANANA_MODEL="gemini-3-pro-image"
export NANO_BANANA_FORMAT="webp"
export NANO_BANANA_QUALITY="90"
```

**High-quality PNG for professional work:**
```bash
export NANO_BANANA_FORMAT="png"
```

**Why WebP default?**
- Smaller file sizes (~30% smaller than JPEG at same quality)
- Better compression than PNG for photos
- Supports transparency (unlike JPEG)
- Widely supported in modern browsers and tools

**Note:** When using `NANO_BANANA_MODEL` with a custom model name, you typically need to set `GOOGLE_GEMINI_BASE_URL` and `GEMINI_API_KEY` to match your custom deployment.

## Usage

The skill activates when you ask Claude to generate images or run Python scripts. Example triggers:

- "Generate an image of..."
- "Create a picture..."
- "Draw..."
- "nano banana"

## Quick Example

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

OUTPUT_DIR = Path("001-cute-banana")
OUTPUT_DIR.mkdir(exist_ok=True)

# Configuration from environment variables
model = os.environ.get("NANO_BANANA_MODEL")
if not model:
    # Claude chooses based on user context:
    # - gemini-3-pro-image-preview: default, high quality (recommended)
    # - gemini-2.5-flash-image: if user wants budget/fast/simple generation
    model = "gemini-3-pro-image-preview"  # <-- Claude replaces based on user request

output_format = os.environ.get("NANO_BANANA_FORMAT", "webp").lower()
quality = int(os.environ.get("NANO_BANANA_QUALITY", "90"))

# Initialize client with optional custom endpoint
base_url = os.environ.get("GOOGLE_GEMINI_BASE_URL")
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if base_url:
    client = genai.Client(api_key=api_key, http_options={'base_url': base_url})
else:
    client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=model,
    contents=["A cute banana character"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']
    )
)

for part in response.parts:
    if part.inline_data is not None:
        # Get google-genai Image object
        genai_image = part.as_image()

        # Convert to PIL Image from bytes
        pil_image = PILImage.open(io.BytesIO(genai_image.image_bytes))

        # Save with format conversion
        if output_format in ("jpg", "jpeg"):
            output_path = OUTPUT_DIR / "output.jpg"
            pil_image.convert("RGB").save(output_path, "JPEG", quality=quality)
        elif output_format == "webp":
            output_path = OUTPUT_DIR / "output.webp"
            pil_image.save(output_path, "WEBP", quality=quality)
        else:  # png
            output_path = OUTPUT_DIR / "output.png"
            pil_image.save(output_path, "PNG")

        print(f"Saved: {output_path}")
EOF
```

## Installation

```bash
/plugin install nano-banana@pigfoot
```

## Resources
- [Cloned from NikiforovAll](https://github.com/NikiforovAll/claude-code-rules/tree/main/plugins/handbook-nano-banana)
- [Official Prompting Guide](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/) - Learn how to structure your prompts effectively.
- [How to prompt Nano Banana Pro](https://www.fofr.ai/nano-banana-pro-guide)
