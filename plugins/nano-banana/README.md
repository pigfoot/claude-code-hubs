# Nano Banana Plugin

Python scripting and Gemini image generation using uv with inline script dependencies.

## Features

- **Image Generation**: Generate images using Google's Gemini models
- **Image Editing**: Edit existing images with AI
- **Interactive Prompting**: Get help crafting effective prompts with best practices (integrated mode selection)
- **Brand Style Support**: Apply corporate brand guidelines (e.g., `style: "trend"` for Trend Micro brand colors)
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

**Complete configuration (all variables):**
```bash
# Required
export GEMINI_API_KEY="your-api-key"                    # Or GOOGLE_API_KEY

# Optional customization
export NANO_BANANA_MODEL="gemini-3-pro-image-preview"  # Override model choice
export NANO_BANANA_FORMAT="webp"                        # Output format (webp/jpg/png)
export NANO_BANANA_QUALITY="95"                         # Quality 1-100 (webp/jpg)

# For custom endpoints (self-hosted/proxy)
export GOOGLE_GEMINI_BASE_URL="https://api.example.com/v1"
```

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

The plugin operates in two modes automatically based on your request:

### Direct Generation Mode

Used when you provide a detailed prompt or inline style specification. Claude generates immediately.

**Example 1: Detailed Prompt**
```
User: "Generate a photorealistic image of a cute cat wearing sunglasses, sitting on a beach chair at sunset, golden hour lighting, 16:9 aspect ratio"

Claude: [Generates directly using gemini-3-pro-image-preview]
Output: 001-beach-cat/generated.webp
```

**Example 2: With Brand Style (structured syntax)**
```
User: "Generate a cybersecurity dashboard infographic, style: trend"

Claude: [Detects style:trend, applies Trend Micro brand colors, generates directly]
Output: 001-security-dashboard/generated.webp
# Colors: Trend Red #d71920, Guardian Red #6f0000, grays, black/white
```

**Example 3: With Brand Style (natural language)**
```
User: "Use style trend to generate an LLM introduction infographic"

Claude: [Detects "style trend" mention, applies Trend Micro colors, generates]
Output: 001-llm-intro/generated.webp
```

**Example 4: Image Editing**
```
User: "Edit 001-cute-cat/generated.webp and add a party hat"

Claude: [Loads image, generates with edit prompt]
Output: 002-party-hat/edited.webp
```

**Example 5: Slide Deck / Presentation (NotebookLM style)**
```
User: "Create a slide explaining how transformers work, use notebooklm style"

Claude: [Detects notebooklm style, uses professional infographic aesthetic with hub-spoke layout]
Output: 001-transformer-architecture/generated.webp
# Clean tech infographic with central attention mechanism, radiating key concepts
```

### Interactive Prompting Mode

Used when you request help crafting prompts or provide vague descriptions. Claude guides you through prompt design.

**Example 6: Explicit Prompting Request**
```
User: "Help me write a good prompt for a professional poster"

Claude:
  Step 1: Checking for style specifications... none found
  Step 2: Let me ask a few questions to craft the best prompt:

  Question 1: What type of image?
  - [ ] Photo/realistic
  - [x] Illustration/artistic
  - [ ] Infographic/educational
  - [ ] Product shot

  Question 2: What's the main subject?
  - [x] Concept/abstract
  - [ ] Person
  - [ ] Object/product

  Step 3: Based on your needs, I recommend Physical Object Framing technique
  Step 4: Generated prompt: "Magazine cover featuring [...]"
  Step 5: Here's your prompt, ready to use!
  Step 6: [Generates with crafted prompt]
```

**Example 7: Vague Prompt (triggers prompting)**
```
User: "Make a logo"

Claude:
  Your request is quite brief. Let me help you design a better prompt.

  Question 1: What type of logo?
  - Minimalist/geometric
  - Vintage/retro
  - Modern/gradient
  - Corporate/professional

  [Continues with prompting workflow...]
```

### Brand Style Support

**Supported styles:**
- `style: "trend"` or `style: trend` - **Trend Micro brand colors + NotebookLM slide aesthetic**
  - Automatically applies professional presentation style (polished infographic, clean layout, 16:9 format)
  - Colors: Trend Red #d71920 as hero, Guardian Red, grays, Dark Blue/Teal accents
  - **Uses lossless WebP** (VP8L) - saves 20-30% vs PNG, zero quality loss
  - Perfect for corporate slide decks, technical presentations, and professional infographics
- `style: "notebooklm"` or `notebooklm style` - **NotebookLM presentation aesthetic**
  - Professional infographics and slide decks
  - **Uses lossless WebP** (VP8L) - saves 20-30% vs PNG with no quality loss
- `use style trend` or `with trend colors` - Natural language detection
- `style: "custom"` - Claude will ask for your color preferences

When slide deck styles (Trend or NotebookLM) are specified, both brand guidelines and lossless WebP format are automatically applied for professional, on-brand, optimally-compressed slide deck imagery.

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
            output_path = OUTPUT_DIR / "generated.jpg"
            pil_image.convert("RGB").save(output_path, "JPEG", quality=quality)
        elif output_format == "webp":
            output_path = OUTPUT_DIR / "generated.webp"
            pil_image.save(output_path, "WEBP", quality=quality)
        else:  # png
            output_path = OUTPUT_DIR / "generated.png"
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
