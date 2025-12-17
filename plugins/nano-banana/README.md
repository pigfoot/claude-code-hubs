# Nano Banana Plugin

Python scripting and Gemini image generation using uv with inline script dependencies.

## Features

- **Image Generation**: Generate images using Google's Gemini models
- **Image Editing**: Edit existing images with AI
- **Python Scripting**: Run Python scripts with uv using heredocs
- **Inline Dependencies**: Self-contained scripts with `# /// script` metadata

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `GOOGLE_API_KEY` environment variable set with a valid Gemini API key

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
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-cute-banana")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=["A cute banana character"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']
    )
)

for part in response.parts:
    if part.inline_data is not None:
        output_path = OUTPUT_DIR / "output.png"
        part.as_image().save(output_path)
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
