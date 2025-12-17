---
name: nano-banana
description: This skill should be used for Python scripting and Gemini image generation. Use when users ask to generate images, create AI art, edit images with AI, or run Python scripts with uv. Trigger phrases include "generate an image", "create a picture", "draw", "make an image of", "nano banana", or any image generation request.
---

# Nano Banana Skill

Python scripting with Gemini image generation using uv. Write small, focused scripts using heredocs for quick tasks—no files needed for one-off operations.

## Choosing Your Approach

**Quick image generation**: Use heredoc with inline Python for one-off image requests.

**Complex workflows**: When multiple steps are needed (generate -> refine -> save), break into separate scripts and iterate.

**Scripting tasks**: For non-image Python tasks, use the same heredoc pattern with `uv run`.

## Writing Scripts

Execute Python inline using heredocs with inline script metadata for dependencies:

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
    contents=["A cute banana character with sunglasses"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']
    )
)

for part in response.parts:
    if part.inline_data is not None:
        image = part.as_image()
        output_path = OUTPUT_DIR / "generated.png"
        image.save(output_path)
        print(f"Image saved to {output_path}")
EOF
```

The `# /// script` block declares dependencies inline using TOML syntax. This makes scripts self-contained and reproducible.

**Why these dependencies:**
- `google-genai` - Gemini API client
- `pillow` - Required for `.as_image()` method (converts base64 to PIL Image) and saving images

**Only write to files when:**
- The script needs to be reused multiple times
- The script is complex and requires iteration
- The user explicitly asks for a saved script

### Basic Template

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-example")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

# Generate image
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=["YOUR PROMPT HERE"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']
    )
)

# Save result
for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        output_path = OUTPUT_DIR / "output.png"
        image.save(output_path)
        print(f"Saved: {output_path}")
EOF
```

## Key Principles

1. **Small scripts**: Each script should do ONE thing (generate, refine, save)
2. **Evaluate output**: Always save images and print status to decide next steps
3. **Dynamic directories**: Save images to `NNN-<short-name>/` directories (see Output Directory Naming)
4. **Stateless execution**: Each script runs independently, no cleanup needed

## Output Directory Naming

Generated images are saved to dynamically named directories in the current working directory:

### Format
```
NNN-<short-name>/
```

### Naming Rules
1. **Sequence Number (NNN)**: Three-digit zero-padded (001, 002, 003...)
   - Check existing `NNN-*` directories in current working directory
   - Use next available number for new topics
2. **Short Name**: 2-4 words from user request
   - action-noun format: `user-auth`, `oauth2-api`, `cute-cat`
   - preserve technical terms: OAuth2, API, JWT, SSO, K8s
   - kebab-case, max 30 characters

### Session Tracking
- **First request**: Create new directory with next sequence number
- **Same topic**: Reuse the same directory for related generations
- **New topic**: Create new directory with next sequence number

### Examples
| User Request | Directory |
|--------------|-----------|
| "Generate user authentication flow" | `001-user-auth-flow` |
| "Create OAuth2 API mockup" | `002-oauth2-api` |
| "Draw a cute cat profile picture" | `003-cute-cat-profile` |
| "Make a logo for my startup" | `004-startup-logo` |

### Directory Setup in Scripts
```python
from pathlib import Path

# Claude sets OUTPUT_DIR based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-user-auth")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

# Save images to OUTPUT_DIR
image.save(OUTPUT_DIR / "output.png")
print(f"Saved: {OUTPUT_DIR}/output.png")
```

## Workflow Loop

Follow this pattern for complex tasks:

1. **Write a script** to generate/process one image
2. **Run it** and observe the output
3. **Evaluate** - did it work? Check the saved image
4. **Decide** - refine prompt or task complete?
5. **Repeat** until satisfied

## Image Configuration

Configure aspect ratio and resolution:

```python
config=types.GenerateContentConfig(
    response_modalities=['IMAGE'],
    image_config=types.ImageConfig(
        aspect_ratio="16:9",  # "1:1", "16:9", "9:16", "4:3", "3:4"
        image_size="2K"       # "1K", "2K", "4K" (uppercase required)
    )
)
```

## Models

- `gemini-2.5-flash-image` - Fast, general purpose image generation
- `gemini-3-pro-image-preview` - Advanced, professional asset production (Nano Banana Pro)

**Default to `gemini-3-pro-image-preview` (Nano Banana Pro)** for all image generation unless:
- The user explicitly requests a different model
- The user wants to save budget/costs
- The user specifies a simpler or quick generation task

Nano Banana Pro provides higher quality results and should be the recommended choice.

## Text + Image Output

To receive both text explanation and image:

```python
config=types.GenerateContentConfig(
    response_modalities=['TEXT', 'IMAGE']
)
```

## Image Editing

Edit existing images by including them in the request:

```bash
uv run - << 'EOF'
# /// script
# dependencies = ["google-genai", "pillow"]
# ///
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

# Output directory - Claude sets based on user request (format: NNN-short-name)
OUTPUT_DIR = Path("001-image-edit")  # <-- Claude replaces this dynamically
OUTPUT_DIR.mkdir(exist_ok=True)

client = genai.Client()

# Load existing image
img = Image.open("input.png")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[
        "Add a party hat to this character",
        img
    ],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE']
    )
)

for part in response.parts:
    if part.inline_data is not None:
        output_path = OUTPUT_DIR / "edited.png"
        part.as_image().save(output_path)
        print(f"Saved: {output_path}")
EOF
```

## Debugging Tips

1. **Print response.parts** to see what was returned
2. **Check for text parts** - model may include explanations
3. **Save images immediately** to verify output visually
4. **Use Read tool** to view saved images after generation

## Error Recovery

If a script fails:
1. Check error message for API issues
2. Verify GOOGLE_API_KEY is set
3. Try simpler prompt to isolate the issue
4. Check image format compatibility for edits

## Advanced Scenarios

For complex workflows including thinking process, Google Search grounding, multi-turn conversations, and professional asset production, load `references/guide.md`.
