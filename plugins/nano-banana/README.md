# Nano Banana Plugin

Python scripting and Gemini/Imagen image generation using uv with inline script dependencies.

## ✨ Recent Improvements (v0.0.9)

### Reproducible Generation & Parameter Control

- ✅ **Seed parameter** - Reproducible image generation with automatic seed tracking
  - Auto-generate timestamp-based seeds (recorded in results JSON)
  - Manual seed specification for exact reproduction
  - Per-slide or global seed configuration
- ✅ **Temperature parameter** - Experimental control over generation randomness (0.0-2.0)
  - Per-slide or global temperature configuration
  - Range validation and priority handling
- ✅ **Results tracking** - `generation-results.json` records actual seed and temperature used
- ✅ **Comprehensive testing** - 28+ test images validating seed reproducibility
- ✅ **Documentation** - Complete usage examples, natural language parsing guide, experiment results

#### Key Findings

- Seed: ✅ Highly effective - same seed produces visually identical images
- Temperature: ⚠️ Limited effect - changes output but unpredictable (recommend keeping default 1.0)

## Previous Improvements (v0.0.8)

### uv Compatibility Enhancement

- ✅ **PEP 723 for library modules** - Added inline dependency metadata to `logo_overlay.py`
- ✅ **Fixed intermittent failures** - Logo overlay now works when Claude creates temporary scripts
- ✅ **Documentation updates** - Added PEP 723 headers to all usage examples
- ✅ **Automatic dependency resolution** - `uv run` correctly installs Pillow even when importing logo_overlay

#### Previous Improvements (v0.0.7)

- ✅ **Zero hallucination rate** - Fixed Python script approach replaces dynamic code generation
- ✅ **Unified workflow** - Same process for 1-100 images (no more dual paths)
- ✅ **Minimal config** - Only `slides` + `output_dir` required, no model field
- ✅ **Cross-platform** - Windows UTF-8 encoding fix, system temp directory handling
- ✅ **Enhanced documentation** - NNN-short-name format enforcement, webp format guide
- ✅ **Path resolution** - Execute script with absolute path while maintaining user's cwd

#### Previous Improvements (v0.0.6)

- ✅ **TrendLife Brand Support** - Automatic logo overlay, brand colors
- ✅ **API documentation fixes** - Added missing `image_config` to basic examples

#### Previous Improvements (v0.0.4)

- ✅ **Batch generation** - Generate 5+ slides in background with 80% context reduction
- ✅ Fixed API confusion between Gemini and Imagen (automatic detection)
- ✅ Added Imagen support for multi-image generation
- ✅ Respect `NANO_BANANA_MODEL` environment variable (no more overrides)
- ✅ Reduced token consumption by 51% (795 → 387 lines in SKILL.md)

## Features

- **Unified Generation Workflow**: All image counts (1-100) use same fixed Python script with JSON config
- **Zero Hallucination**: Fixed script eliminates AI code generation errors (60% → 100% success rate)
- **Dual API Support**: Generate images using Gemini OR Imagen models (automatic detection)
- **Image Generation**: Gemini (quality, slides) or Imagen (multiple images, negative prompts)
- **Interactive Prompting**: Get help crafting effective prompts with best practices
- **Brand Style Support**: TrendLife (`style: "trendlife"`) with automatic logo overlay and NotebookLM styles
- **Cross-Platform**: Works on Windows, Linux, and macOS with proper encoding and path handling
- **Minimal Config**: Only `slides` + `output_dir` required, model via environment variable

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) environment variable set with a valid Gemini API key

## Quick Setup

### Option A: Claude Code Settings (Recommended)

Configure environment variables in `~/.claude/settings.json` so they're available to all skills.

#### macOS / Linux / WSL / Git Bash

```bash
# Replace with your actual API key
GEMINI_API_KEY="your-api-key-here"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed."
    echo "Install with: brew install jq (Mac) or apt install jq (Linux)"
    exit 1
fi

[[ ! -r "${HOME}/.claude/settings.json" ]] && mkdir -p "${HOME}/.claude" && echo "{}" > "${HOME}/.claude/settings.json"

jq "$(cat <<EOFSETTINGS
.env.GEMINI_API_KEY="${GEMINI_API_KEY}"
EOFSETTINGS
)" ${HOME}/.claude/settings.json > /tmp/temp.json && mv -f /tmp/temp.json ${HOME}/.claude/settings.json

echo "Configuration updated successfully"
```

#### Windows PowerShell

```powershell
# Replace with your actual API key
$GEMINI_API_KEY = "your-api-key-here"

# Settings.json setup
$settingsPath = "$env:USERPROFILE\.claude\settings.json"
if (-not (Test-Path $settingsPath)) {
    New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude" | Out-Null
    "{}" | Out-File -Encoding utf8 $settingsPath
}

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

# Ensure env object exists
if (-not $settings.env) {
    $settings | Add-Member -Type NoteProperty -Name "env" -Value (New-Object PSObject) -Force
}

# Add or update environment variables (preserving existing ones)
$settings.env | Add-Member -Type NoteProperty -Name "GEMINI_API_KEY" -Value $GEMINI_API_KEY -Force

$settings | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $settingsPath

Write-Host "Configuration updated successfully" -ForegroundColor Green
```

#### Verify installation

```bash
# macOS / Linux
cat ~/.claude/settings.json

# Windows PowerShell
Get-Content (Join-Path $env:USERPROFILE ".claude\settings.json")
```

### Option B: Shell Environment Variables

```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export GEMINI_API_KEY="your-api-key-here"
```

### Option C: Project .env file

```bash
# Create .env file in your project directory
GEMINI_API_KEY=your-api-key-here
```

## Configuration

Customize plugin behavior using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NANO_BANANA_MODEL` | (Claude chooses) | **Specify model name** - determines API automatically:<br>• Contains `"imagen"` → Imagen API<br>• Otherwise → Gemini API<br>**IMPORTANT:** Used exactly as-is, no modifications |
| `NANO_BANANA_FORMAT` | `webp` | Output image format: `webp`, `jpg`, or `png` |
| `NANO_BANANA_QUALITY` | `90` | Image quality (1-100) for webp/jpg formats |
| `GOOGLE_GEMINI_BASE_URL` | (official API) | Custom API endpoint (for non-official deployments) |
| `GEMINI_API_KEY` | (falls back to `GOOGLE_API_KEY`) | API key (official or custom endpoint) |

### API Selection Logic

The plugin automatically selects the correct API based on the model name:

```python
# Automatic detection
if "imagen" in model.lower():
    use_imagen_api = True   # → generate_images()
else:
    use_gemini_api = True   # → generate_content()
```

#### Supported Models

- **Gemini**: `gemini-3-pro-image-preview`, `gemini-2.5-flash-image`, or custom names
- **Imagen**: `imagen-4.0-generate-001`, or custom names containing "imagen"

#### ⚠️ Custom Endpoints

- Model names from custom endpoints are used **exactly as-is**
- Do NOT add `-preview` or other suffixes
- Example: If your endpoint uses `gemini-3-pro-image` (no `-preview`), set it exactly like that

### Examples

#### Complete configuration (all variables)

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

#### Official Google API (default)

```bash
export GEMINI_API_KEY="your-api-key"  # Or GOOGLE_API_KEY (backward compatible)
# Model: Claude chooses Pro (default) or Flash (budget/fast) automatically
# Optional: force specific model or format
# export NANO_BANANA_MODEL="gemini-2.5-flash-image"
# export NANO_BANANA_FORMAT="jpg"
```

#### Custom Endpoint (self-hosted or proxy)

```bash
export GOOGLE_GEMINI_BASE_URL="https://your-api.example.com/v1"
export GEMINI_API_KEY="your-custom-api-key"
export NANO_BANANA_MODEL="gemini-3-pro-image"
export NANO_BANANA_FORMAT="webp"
export NANO_BANANA_QUALITY="90"
```

#### High-quality PNG for professional work

```bash
export NANO_BANANA_FORMAT="png"
```

#### Why WebP default

- Smaller file sizes (~30% smaller than JPEG at same quality)
- Better compression than PNG for photos
- Supports transparency (unlike JPEG)
- Widely supported in modern browsers and tools

**Note:** When using `NANO_BANANA_MODEL` with a custom model name, you typically need to set `GOOGLE_GEMINI_BASE_URL`
and `GEMINI_API_KEY` to match your custom deployment.

## Usage

The plugin operates in two modes automatically based on your request:

### Direct Generation Mode

Used when you provide a detailed prompt or inline style specification. Claude generates immediately.

#### Example 1: Detailed Prompt

```
User: "Generate a photorealistic image of a cute cat wearing sunglasses, sitting on a beach chair at sunset, golden hour lighting, 16:9 aspect ratio"

Claude: [Generates directly using gemini-3-pro-image-preview]
Output: 001-beach-cat/generated.webp
```

#### Example 2: With Brand Style (structured syntax)

```
User: "Generate a cybersecurity dashboard infographic, style: trend"

Claude: [Detects style:trend, applies Trend Micro brand colors, generates directly]
Output: 001-security-dashboard/generated.webp
# Colors: Trend Red #d71920, Guardian Red #6f0000, grays, black/white
```

#### Example 3: With Brand Style (natural language)

```
User: "Use style trend to generate an LLM introduction infographic"

Claude: [Detects "style trend" mention, applies Trend Micro colors, generates]
Output: 001-llm-intro/generated.webp
```

#### Example 4: Image Editing

```
User: "Edit 001-cute-cat/generated.webp and add a party hat"

Claude: [Loads image, generates with edit prompt]
Output: 002-party-hat/edited.webp
```

#### Example 5: Slide Deck / Presentation (NotebookLM style)

```
User: "Create a slide explaining how transformers work, use notebooklm style"

Claude: [Detects notebooklm style, uses professional infographic aesthetic with hub-spoke layout]
Output: 001-transformer-architecture/generated.webp
# Clean tech infographic with central attention mechanism, radiating key concepts
```

### Interactive Prompting Mode

Used when you request help crafting prompts or provide vague descriptions. Claude guides you through prompt design.

#### Example 6: Explicit Prompting Request

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

#### Example 7: Vague Prompt (triggers prompting)

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

### Style Support

#### Brand Styles

**Specify with:** `style: "stylename"` or natural language

| Style | Syntax | Colors | Use Case |
|-------|--------|--------|----------|
| **Trend Micro** | `style: "trend"` or "use style trend" | Trend Red (#d71920), Guardian Red, grays | Corporate presentations, tech slides |
| **NotebookLM** | `style: "notebooklm"` or "notebooklm style" | Professional aesthetic (⚠️ no branding) | Clean presentation slides, infographics |
| **Custom** | `style: "custom"` | Your choice | Claude asks for color preferences |

#### Slide Deck Visual Styles

#### Available when creating slides/presentations

| Visual Style | Best For | Characteristics |
|--------------|----------|-----------------|
| **Professional** | Business reports, tech presentations | Deep blue background (#003366), clean typography, neon accents |
| **Blackboard** | Educational content, tutorials | Green/black board, chalk texture, hand-drawn feel |
| **Data Viz** | Charts, metrics, analytics | High contrast, clean gridlines, pictogram callouts |
| **Process Flow** | Step-by-step guides, workflows | Numbered steps, connecting arrows, geometric shapes |
| **Overview** | Concept summaries, topic intros | Bento grid layout, pastel colors, icon-driven |

**Claude automatically chooses the most appropriate visual style** based on your content type. To request a specific
style:

```
"Create a professional infographic explaining CI/CD pipelines"
"Make a blackboard-style tutorial slide for sorting algorithms"
"Generate a data viz slide showing Q4 metrics"
```

#### Automatic Features for Slide Decks

When creating slides/presentations:

- ✅ **Lossless WebP** format (VP8L encoding)
  - 20-30% smaller than PNG
  - Zero quality loss
  - Perfect for text and icons
- ✅ **16:9 aspect ratio** (default for presentations)
- ✅ **2K resolution** (optimal for displays)

**Priority:** Inline spec → Ask in Interactive Mode → No style (Direct Mode default)

## Multi-Slide Generation: Context Window Optimization

### The Problem

When generating multiple images (e.g., 10 slides for a presentation), each image's output accumulates in the
conversation context:

- **Per image output:** ~150-200 tokens (generation logs, paths, status)
- **10 slides:** 1,500-2,000 tokens consumed
- **Risk:** Context window fills quickly, reducing available space for conversation

### Solutions Evaluated

#### Option 1: Current Approach (Direct Execution)

Execute Python script 10 times sequentially in the main conversation.

#### Option 1: Token Consumption

- Main context: **1,500-2,000 tokens**
- API cost: Low (single conversation)

#### Option 1: Pros

- ✅ Simple implementation
- ✅ Immediate feedback per image
- ✅ Easy debugging with visible output

#### Option 1: Cons

- ❌ Context accumulates quickly
- ❌ Verbose output fills conversation

---

#### Option 2: Subagent Approach

Spawn independent subagent for each slide generation.

#### Option 2: Token Consumption

- Main context: **~1,400 tokens** (Task tool calls + results)
- Total API cost: **~32,000 tokens** (10 subagents × 3,200 tokens each)

#### Cost Breakdown per Subagent

- System prompt: ~1,000 tokens
- Skill loading (nano-banana): ~1,500 tokens
- Task understanding + execution: ~500 tokens
- Output: ~200 tokens

#### Pros

- ✅ Isolated context per image
- ✅ Parallel execution possible
- ✅ Cleaner main conversation

#### Cons

- ❌ **15x higher API cost** (32,000 vs 2,000 tokens)
- ❌ Slow startup overhead (2-5s per subagent)
- ❌ Complex coordination (error handling, retries, timeouts)
- ❌ Rate limit risks with parallel execution
- ❌ Overkill for simple batch generation

---

#### Option 3: Background Bash + Progress File ✅ (Selected)

Run batch generation in background task, poll progress file periodically.

#### Option 3: Token Consumption

- Main context: **~390 tokens total**
  - Start background task: ~20 tokens
  - Poll progress (3 times): ~120 tokens
  - Read final results: ~250 tokens
- API cost: Same as current (no additional subagents)

#### Workflow

1. Create slides configuration JSON
2. Start background task with `Bash(run_in_background=True)`
3. Python script writes progress to `/tmp/nano-banana-progress.json`
4. Poll progress file every 10-15 seconds
5. Read final results from `/tmp/nano-banana-results.json`

#### Option 3: Pros

- ✅ **80% context reduction** (1,800 → 390 tokens)
- ✅ **Zero additional API cost** (same as current)
- ✅ **Fastest execution** (Python runs at full speed, no subagent overhead)
- ✅ **Progress tracking** (can show updates to user)
- ✅ **Low complexity** (simpler than subagent coordination)

#### Option 3: Cons

- ❌ Requires polling mechanism
- ❌ Less immediate feedback (progress shown in batches)

### Comparison Table

| Method | Main Context | Total API Cost | Speed | Complexity | Best For |
|--------|--------------|----------------|-------|------------|----------|
| **Direct Execution** | 1,800 tokens | Low | Medium | Low | **1-4 images** (auto-selected) |
| **Subagent** | 1,400 tokens | 32,000 tokens<br>**(+1,500%)** ❌ | Medium | High | Each image needs Claude's reasoning |
| **Background Bash** ✅ | **390 tokens<br>(-80%)** ✅ | **Low (0% increase)** ✅ | **Fast** ✅ | Low-Medium | **5+ images** (auto-selected) |

### Current Implementation (v0.0.5+)

The skill now automatically uses Background Bash approach for 5+ slides:

```python
# 1. Create slides configuration
slides_config = {
    "slides": [
        {"number": 1, "prompt": "CI/CD pipeline overview", "style": "professional"},
        {"number": 2, "prompt": "Build stage architecture", "style": "professional"},
        {"number": 3, "prompt": "Testing pyramid", "style": "data-viz"},
        # ... up to slide 10
    ],
    "output_dir": "/path/to/deck/",
    "format": "webp",
    "quality": 90
}

# 2. Start background task (MUST use 'uv run')
task_id = Bash(
    command="uv run /path/to/generate_batch.py --config /tmp/slides_config.json",
    run_in_background=True
)
# Output: "Started background task: task_abc123"

# 3. Poll progress periodically
Read("/tmp/nano-banana-progress.json")
# → {"current": 3, "total": 10, "status": "generating slide 3...", "completed": ["slide-1.webp", "slide-2.webp"]}

# 4. Read final results when complete
Read("/tmp/nano-banana-results.json")
# → {"completed": 10, "outputs": ["/path/to/deck/slide-1.webp", ...], "duration": "45s"}
```

#### Context in Main Conversation

```
Generating 10 slides in background...
Progress: 3/10 slides completed (30%)
Progress: 7/10 slides completed (70%)
✓ All 10 slides completed in 45s
  Results: /path/to/deck/
  Files: slide-1.webp through slide-10.webp
```

**Total context:** ~390 tokens (vs 1,800 with current approach)

### Decision Rationale

#### Why Background Bash won

1. **Cost Efficiency:** Subagent approach costs 15x more API tokens for the same result
2. **Performance:** No subagent startup overhead, Python runs at native speed
3. **Simplicity:** Easier to implement and maintain than subagent coordination
4. **Context Optimization:** 80% reduction in context usage (critical for long conversations)
5. **Scalability:** Works equally well for 5 slides or 50 slides

#### When Subagent still makes sense

- Each slide requires Claude's judgment/reasoning (e.g., auto-selecting visual style based on content analysis)
- Slides are completely independent and benefit from parallel processing
- User doesn't care about API cost

**Current Status:** Feature planned for future release. Current implementation uses direct execution (best for 1-3
images).

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
