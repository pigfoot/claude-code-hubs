---

# === Required (All Platforms) ===

name: nano-banana
description: |
  Use when users request image generation, AI art creation, image editing with Gemini models, need help crafting prompts, or want brand-styled imagery. Handles both direct generation and interactive prompt design.

# === Claude Code / OpenAI Codex ===

allowed-tools: Bash Write Read AskUserQuestion
metadata:
  short-description: Unified image generation workflow via OpenAI-compatible API
  version: "0.2.0"
  openclaw:
    primaryEnv: RDSEC_API_KEY

# === GitHub Copilot ===

license: MIT
---

# Nano Banana

Unified image generation workflow using a fixed Python script with JSON configuration. Eliminates AI hallucinations by
avoiding dynamic code generation.

Supports two modes:

- **Unified Generation**: All image requests use generate_images.py with JSON config
- **Interactive Prompting**: Guide user through prompt design with proven techniques

---

## 🚨 CRITICAL: Read This First

### API Routing by Model

The script routes API calls based on `IMAGE_GEN_MODEL`:

| Condition | API Call | Endpoint |
|-----------|----------|----------|
| `gpt-image-2` (no `reference_image`, no TrendLife featured) | `client.images.generate()` | POST `/images/generations` |
| `gpt-image-2` + `reference_image` | `client.images.edit()` | POST `/images/edits` |
| `gpt-image-2` + `style: "trendlife"` + `layout: "featured"` | `client.images.edit()` (logo as image) | POST `/images/edits` |
| Any other model (Gemini, etc.) | `client.chat.completions.create()` | POST `/chat/completions` |

**gpt-image-2**: Always uses `quality="low"` — other values timeout or return 400.
Seed and temperature are not supported and will be silently ignored (one warning per job).

**Gemini models** (`gemini-3-pro-image`, `gemini-3.1-flash-image`): Use `chat.completions` with `response_modalities=["IMAGE"]`:

```python
client.chat.completions.create(
    model=os.environ.get("IMAGE_GEN_MODEL") or "gemini-3-pro-image",
    messages=[{"role": "user", "content": prompt}],
    seed=seed,
    temperature=temperature,
    extra_body={"response_modalities": ["IMAGE"]},
)
```

### IMAGE_GEN_MODEL: NEVER Override

**Rule:** If `IMAGE_GEN_MODEL` is set, use it EXACTLY as-is.

❌ **WRONG - Do NOT do this:**

```python
model = os.environ.get("IMAGE_GEN_MODEL", "gemini-3-pro-image")
if not model.endswith("-preview"):
    model = f"{model}-preview"  # ❌ NEVER modify user's model name
```

✅ **CORRECT:**

```python
model = os.environ.get("IMAGE_GEN_MODEL")
if not model:
    # Only choose default when IMAGE_GEN_MODEL is NOT set
    model = "gemini-3-pro-image"
# Use model EXACTLY as-is - do NOT add suffixes or change names
```

#### Why this matters

- Custom endpoints have their own model names (e.g., `gemini-3-pro-image` without `-preview`)
- User explicitly set the model they want
- DO NOT apply naming conventions to custom endpoint models

---

## When to Use

- Image generation ("draw", "create", "generate"), slides, presentations
- Image editing with AI
- Prompt help ("help me craft", "improve my prompt")
- Brand styles ("use style trend", "notebooklm style")
- Reproducible generation ("use seed 42", "regenerate that image")

### Mode selection

- **Interactive Prompting**: User asks for prompt help OR prompt too vague (<5 words)
- **Unified Generation**: User provides detailed prompt (uses generate_images.py)

### Parsing User Intent for Seed & Temperature

#### Extract seed from user message

- "seed 42" → `"seed": 42`
- "use seed 392664860" → `"seed": 392664860`
- "regenerate with the same seed" → Use seed from previous results JSON
- "seed: 123" (inline) → `"seed": 123`

#### Extract temperature from user message

- "temperature 0.5" → `"temperature": 0.5`
- "temp 1.5" → `"temperature": 1.5`
- "lower temperature" → `"temperature": 0.5` (suggest conservative value)
- "higher temperature" → `"temperature": 1.5` (suggest exploratory value)
- "more creative" → `"temperature": 1.5`
- "temperature: 0.8" (inline) → `"temperature": 0.8`

#### Combined examples

```
User: "Generate a robot image, seed 42, temperature 0.8"
→ Config: {"slides": [{"number": 1, "prompt": "robot", "seed": 42, "temperature": 0.8}]}

User: "Regenerate that image with seed 392664860"
→ Config: {"slides": [{"number": 1, "prompt": "<previous_prompt>", "seed": 392664860}]}

User: "Create 3 slides with same seed 100"
→ Config: {"seed": 100, "slides": [{...}, {...}, {...}]}
```

#### If user asks about reproducibility

- Explain that seed enables regenerating the same image
- Mention that results JSON automatically records seeds
- Show example of how to use seed from previous generation

## Style Detection

**Detect:** `style: "trendlife"`, `style: "notebooklm"`, or natural language ("use trendlife style", "notebooklm style")

### Styles

- **TrendLife**: Trend Micro's TrendLife product brand (Trend Red #D71920) with automatic logo overlay
- **NotebookLM**: Clean presentation aesthetic (⚠️ **NEVER** use "NotebookLM" brand/logo in prompts)

**Priority:** Inline spec → Ask in Interactive Mode → No style (Direct Mode default)

---

## Logo Overlay (TrendLife Style)

### TrendLife style includes automatic logo overlay

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

### Layout Detection Rules

#### Automatic detection based on keywords

- **"title slide"**, **"cover slide"**, **"opening"** → title layout (15% logo, bottom-right)
- **"end slide"**, **"closing"**, **"thank you"**, **"conclusion"** → end layout (20% logo, center-bottom)
- **"divider"**, **"section break"** → divider layout (15% logo, bottom-right)
- **Slide number 1** (no keywords) → title layout (assumed opener)
- **Default** → content layout (12% logo, bottom-right)

### Manual Logo Overlay Override

Use when you need custom logo positioning:

**IMPORTANT:** This script must be run with `uv run` to ensure dependencies are available.

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["pillow"]
# ///
# Run with: uv run --managed-python your_script.py

# After image generation, before final output
from pathlib import Path
import sys

# Import logo overlay module
sys.path.insert(0, str(Path(__file__).parent))
from logo_overlay import overlay_logo, detect_layout_type

# Detect layout type (or specify manually)
layout_type = detect_layout_type(prompt, slide_number=1)
# Or override: layout_type = 'title'  # 'title', 'content', 'divider', 'end'

# Logo path
logo_path = Path(__file__).parent / 'assets/logos/trendlife-2026-logo-light.png'

# Apply logo overlay
output_with_logo = output_path.with_stem(output_path.stem + '_with_logo')
overlay_logo(
    background_path=output_path,
    logo_path=logo_path,
    output_path=output_with_logo,
    layout_type=layout_type,
    opacity=1.0  # Optional: 0.0-1.0
)

# Replace original with logo version
output_with_logo.replace(output_path)
```

### Style Trigger Keywords

**Explicit:** `style: "trendlife"`

#### Natural Language

- "trendlife style"
- "use trendlife"
- "trendlife brand"
- "trendlife presentation"

## Quick Reference

### API Routing Decision (CRITICAL - Check First)

| `IMAGE_GEN_MODEL` | `reference_image` | API Used |
|-------------------|-------------------|----------|
| `gpt-image-2` | absent | `client.images.generate()` — POST `/images/generations` |
| `gpt-image-2` | present | `client.images.edit()` — POST `/images/edits` |
| `gemini-*` or any other | any | `client.chat.completions.create()` — POST `/chat/completions` |

#### See CRITICAL section above for complete details

### Unified Generation Workflow

All image generation uses the same fixed Python script with JSON config:

1. **Create Config:** Write JSON to system temp directory (NOT skill directory)
   - Use `Write` tool with path: `{temp_dir}/nano-banana-config-{timestamp}.json`
   - Get temp_dir from user's OS temp location (cross-platform)
2. **Execute Script:** `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --config <temp_config_path>`
   - **CRITICAL:** Use `${CLAUDE_SKILL_DIR}` prefix WITHOUT changing directory (no `cd` command)
   - **WRONG:** `cd scripts && uv run --managed-python generate_images.py ...` ❌
   - **CORRECT:** `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py ...` ✅
   - This ensures execution cwd remains in user's project directory, so relative paths in config work correctly
3. **Track Progress:** Monitor progress/results files (for background tasks)
4. **Return Paths:** Report generated image locations

#### IMPORTANT

- Always write config to system temp directory, NEVER to skill base directory
- Always use `${CLAUDE_SKILL_DIR}/scripts/generate_images.py` for the script path

#### Config Requirements

#### Minimal Config (recommended)

```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-feature-name/"  // MUST use NNN-short-name format
}
```

#### Full Config (optional fields)

```json
{
  "slides": [
    {
      "number": 1,
      "prompt": "...",
      "style": "trendlife",
      "layout": "featured",       // Optional: "featured" or "content" (auto-detect if omitted)
      "temperature": 0.8,         // Optional: 0.0-2.0 per-slide override (Gemini only)
      "seed": 42,                 // Optional: integer for reproducible generation (Gemini only)
      "reference_image": "./src.png"  // Optional: relative path; triggers /images/edits for gpt-image-2
    }
  ],
  "output_dir": "./001-feature-name/",  // MUST use NNN-short-name format
  "format": "webp",      // Optional: webp (default, RECOMMENDED), png, jpg
  "quality": 90,         // Optional: 1-100 (default: 90)
  "temperature": 1.0,    // Optional: 0.0-2.0 global default (default: 1.0, Gemini only)
  "seed": 12345          // Optional: integer global default (default: auto-generate, Gemini only)
}
```

#### gpt-image-2 Config Example

```json
{
  "slides": [
    {"number": 1, "prompt": "A futuristic cityscape at night"},
    {"number": 2, "prompt": "Add a moon to the sky", "reference_image": "./001-city/slide-01.webp"}
  ],
  "output_dir": "./002-city-edit/"
}
```

#### Format Selection Guide

- **webp (RECOMMENDED)**: Default format, automatically uses lossless compression for presentation styles (trendlife,
  professional, data-viz). Same quality as PNG but 25-35% smaller file size.
- **png**: Only use if webp compatibility is a concern (rare). Larger file size.
- **jpg**: For photos only, not suitable for slides/diagrams (lossy compression).

#### Layout Field (TrendLife Only)

**Purpose:** Control logo integration strategy for TrendLife brand slides

**Valid values:**

- **`"featured"`** - For title slides, dividers, and closing slides
  - Logo is used as **reference image** during AI generation (both Gemini and gpt-image-2)
  - Gemini: logo passed as `image_url` in `chat.completions`
  - gpt-image-2: logo passed as `image` param in `/images/edits`
  - AI naturally integrates logo into the overall design
  - Provides creative, professional branding

- **`"content"`** - For content/information slides
  - Logo is **overlaid** in bottom-right corner (50px, 25px padding)
  - Fixed positioning ensures logo doesn't interfere with content
  - Consistent across all content slides

- **Omitted or `null`** - Auto-detection (backwards compatibility)
  - System attempts to detect layout from prompt keywords
  - Less reliable than explicit specification

**When to use each:**

```json
// Title/cover slides
{"number": 1, "prompt": "Product Launch 2026", "style": "trendlife", "layout": "featured"}

// Section dividers
{"number": 3, "prompt": "Part 2: Technical Details", "style": "trendlife", "layout": "featured"}

// Closing slides
{"number": 6, "prompt": "Thank You", "style": "trendlife", "layout": "featured"}

// Content slides (everything else)
{"number": 2, "prompt": "Key features and benefits", "style": "trendlife", "layout": "content"}
{"number": 4, "prompt": "Performance metrics", "style": "trendlife", "layout": "content"}
```

**IMPORTANT:** When generating JSON configs for TrendLife presentations:

1. **Analyze each slide's purpose** (not just keywords)
2. **Title/cover/divider/closing** → `"layout": "featured"`
3. **Information/data/content** → `"layout": "content"`
4. **Always specify `layout` explicitly** for TrendLife slides (don't rely on auto-detection)

### Temperature & Seed Parameters

> **gpt-image-2**: Seed and temperature are **not supported** by the RONE endpoint.
> The script will emit a warning (once per job) and ignore both fields.
> Use Gemini models if you need reproducible generation.

#### ⚡ NEW: Reproducible Generation (Gemini only)

#### Seed Parameter (Recommended)

**Purpose:** Enable reproducible image generation

#### How it works

- Same seed + same prompt + same temperature = visually identical image
- Default: Auto-generated timestamp-based seed (recorded in results JSON)
- Use case: "I like this image, regenerate it exactly"

#### Seed: User natural language patterns

- "use seed 42"
- "regenerate with seed 392664860"
- "same seed as before"
- "seed: 123" (inline spec)

#### Config examples

```json
// Global seed (all slides use same seed)
{"seed": 42, "slides": [...]}

// Per-slide seed (each slide has different seed)
{"slides": [
  {"number": 1, "prompt": "...", "seed": 42},
  {"number": 2, "prompt": "...", "seed": 123}
]}

// No seed specified (auto-generate and record)
{"slides": [...]}  // Results JSON will contain: "seed": 1738051234
```

#### Results tracking

- All generated images record their actual seed in `{output_dir}/generation-results.json`
- Example output:

```json
{
  "outputs": [
    {"slide": 1, "path": "slide-01.png", "seed": 392664860, "temperature": 1.0}
  ]
}
```

#### Temperature Parameter (Experimental)

**Purpose:** Control randomness in generation (0.0-2.0)

**Official guidance:** Gemini 3 recommends keeping default value 1.0

#### Effect

- ⚠️ **Limited impact observed in testing** - changes output but effect is unpredictable
- No clear "low temperature = conservative, high temperature = creative" pattern
- Changes generation result when combined with same seed

#### Temperature: User natural language patterns

- "temperature 0.5"
- "use lower temperature"
- "more creative (temperature 1.5)"
- "temperature: 0.8" (inline spec)

#### Recommendation

- ✅ Use seed for reproducibility (highly effective)
- ⚠️ Use temperature conservatively for experimentation only
- 💡 Keep default 1.0 unless exploring variations

#### Priority rules

- slide.temperature > config.temperature > 1.0 (default)
- slide.seed > config.seed > auto-generate

#### Field Rules

- ✅ `output_dir` MUST be relative path with NNN-short-name format: `./001-feature-name/`
  - NNN = 3-digit number (001, 002, etc.)
  - short-name = brief descriptive name (lowercase, hyphens)
  - Examples: `./001-ai-safety/`, `./002-threat-detection/`, `./003-user-onboarding/`
- ✅ `reference_image` MUST be a relative path (e.g., `"./source.png"`) — gpt-image-2 only; triggers `/images/edits`
- ❌ NO absolute paths (breaks cross-platform)
- ❌ NO plain names without numbers (e.g., `./slides/` is WRONG)
- ❌ NO `model` field (use IMAGE_GEN_MODEL env var)
- ❌ NO `seed` or `temperature` for gpt-image-2 slides (unsupported; silently ignored)

#### Output Directory Behavior

- Relative paths resolve to user's current working directory
- Script is executed with absolute path, but cwd remains in user's directory
- Use sequential numbering for different presentation topics

#### Example: Config File Creation

```bash
# Linux/macOS: Write to /tmp/
Write tool: /tmp/nano-banana-config-1234567890.json

# Windows: Write to %TEMP%
Write tool: C:/Users/<user>/AppData/Local/Temp/nano-banana-config-1234567890.json
```

#### Multi-Slide Generation

- **Any slide count** → Uses same workflow (generate_images.py)
- **5+ slides** → Automatic background execution with progress tracking
- **Context efficient** → <500 tokens for any slide count

**Complete workflow details:** See `references/batch-generation.md`

### Interactive Prompting Mode

| Step | Action |
|------|--------|
| 1. Gather | Check for reference images, style specs |
| 2. Clarify | Ask 2-4 questions about output type, subject, style |
| 3. Select Technique | Choose from 16+ patterns (see references/guide.md) |
| 4. Generate Prompt | Apply technique, brand style, aspect ratio |
| 5. Present | Show prompt with explanation and variations |
| 6. Execute | Generate image with crafted prompt |

## Interactive Prompting Mode

**When to use:** User requests prompt help ("help me craft", "improve my prompt") or prompt is too vague (<5 words).

### Workflow

1. **Gather** - Check for reference images, existing prompts, inline style specs (`style: "trend"`)
2. **Clarify** - Use `AskUserQuestion`: Output type? Subject? Style preference?
3. **Select Technique** - Choose from 16+ patterns in `references/guide.md`
4. **Generate Prompt** - Apply technique + brand style + aspect ratio
5. **Present** - Show prompt with explanation and variations
6. **Execute** - Generate using unified generation workflow (generate_images.py)

#### Brand Style Integration

- **NotebookLM style** (`style: "notebooklm"`):
  - Apply aesthetic: polished tech infographic, clean slide layout, minimal text
  - ⚠️ **NEVER** use "NotebookLM" brand/logo/name in prompts (trademark violation)
  - ✅ Use: "clean professional presentation aesthetic", "modern tech infographic style"
  - See `references/slide-deck-styles.md` for complete specs

- **Trend Micro style** (`style: "trend"`):
  - Colors: Trend Red (#d71920), Guardian Red (#6f0000), Grays (#58595b-#e6e7e8)
  - See `references/brand-styles.md` for complete specs

**Complete techniques and examples:** See `references/guide.md`

## Debugging

### Most Common Errors

| Error | Quick Fix |
|-------|-----------|
| `RDSEC_API_KEY not set` | `export RDSEC_API_KEY=<your-token>` |
| `IMAGE_GEN_BASE_URL not set` | `export IMAGE_GEN_BASE_URL="https://api.rdsec.trendmicro.com/prod/aiendpoint/v1"` |
| `Model not found` | Check exact model name in `IMAGE_GEN_MODEL` |
| `ModuleNotFoundError` | Verify `# dependencies = ["openai", "pillow"]` in script header |
| No image generated | Check that endpoint returns data in `message.images` field |
| `401 Unauthorized` | Verify `RDSEC_API_KEY` is a valid JWT token with endpoint permissions |

### Debug Steps

1. Verify API key: `echo $RDSEC_API_KEY`
2. Verify endpoint URL: `echo $IMAGE_GEN_BASE_URL` (must end with `/v1`)
3. Test with simple prompt: `"A red circle"`
4. Review CRITICAL section if API errors occur

### Known Limitations (RONE Endpoint)

| Feature | Status | Notes |
|---------|--------|-------|
| `gpt-image-2` text-to-image (`/images/generations`) | ✅ Working | Use `quality: "low"` to avoid timeout |
| `gpt-image-2` image editing (`/images/edits`) | ✅ Working | Fixed; use multipart form data + `quality: "low"` (~37-152s) |
| Gemini image generation (`chat.completions`) | ✅ Working | Primary workflow for this skill |
| Gemini image editing (`/images/edits`) | ❌ Not working | LiteLLM Vertex AI credential issue; use `chat.completions` with `image_url` parts instead |

#### gpt-image-2 `/images/edits` — Correct Usage

Send as **multipart form data** (do NOT set `Content-Type` manually):

```python
files = {"image": ("image.png", img_bytes, "image/png")}
data = {
    "model": "gpt-image-2",
    "prompt": "edit instruction",
    "n": "1",
    "size": "1024x1024",   # must be a verified GPT pixel size
    "quality": "low",       # REQUIRED — other values risk timeout
}
resp = requests.post(f"{BASE_URL}/images/edits",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files=files, data=data, timeout=300)
# Response: resp.json()["data"][0]["b64_json"]
```

#### Timeout Reference (from May 8 probe sweep, Michael Fu UX-AS)

| Endpoint | `quality` | Time | Use? |
|----------|-----------|------|------|
| `/images/generations` | `low` | ~72s | ✅ |
| `/images/generations` | `medium` | ~110s | ⚠️ slow |
| `/images/generations` | `auto` / omitted | timeout | ❌ |
| `/images/generations` | `high` | timeout | ❌ |
| `/images/edits` | `low` | ~37–152s | ✅ |
| `/images/edits` | omitted / `auto` / `high` | timeout / 400 | ❌ |
| `/images/edits` | `standard` / `hd` | 400 | ❌ |

**Rule:** All gpt-image-2 calls use `quality="low"` — the script enforces this automatically.

**Reference:** [RDSec_One_Support — gpt-image-2 image editing follow-up (2026-05-12)](https://teams.microsoft.com/l/message/19:30f59149137649be85abbba50c7f4617@thread.tacv2/1778557586181?tenantId=3e04753a-ae5b-42d4-a86d-d6f05460f9e4&groupId=3e59784e-87f1-45d9-9393-0472c3c885a7&parentMessageId=1778557586181&teamName=RDSec-Service-Public&channelName=RDSec_One_Support&createdTime=1778557586181)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| **Using `types.ImageGenerationConfig`** | **Does NOT exist - use `GenerateContentConfig` or `GenerateImagesConfig`** |
| **Using `generate_images()` with Gemini** | **Use `generate_content()` for Gemini models** |
| **Using `generate_content()` with Imagen** | **Use `generate_images()` for Imagen models** |
| Overriding `IMAGE_GEN_MODEL` when set | Use model EXACTLY as-is - don't add suffixes |
| Using `google-genai` library | Use `openai` library with OpenAI-compatible endpoint |
| Using text models for image gen | Use image models only (e.g., `gemini-3-pro-image`) |
| Saving to flat files | Use `NNN-short-name/` directories |
| Using PIL to draw/edit | Use Gemini/Imagen API with image in `contents` |

## Example Workflows

### Scenario 1: First Generation (Auto Seed)

```
User: "Generate a modern office interior"

Assistant actions:
1. Create config WITHOUT seed (auto-generate):
   {
     "slides": [{"number": 1, "prompt": "Modern office interior with natural lighting"}],
     "output_dir": "./001-office-design/"
   }
2. Execute: uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --config {temp_config}
3. Read results: ./001-office-design/generation-results.json
   → {"outputs": [{"slide": 1, "path": "slide-01.png", "seed": 392664860}]}
4. Report to user: "Generated at ./001-office-design/slide-01.png (seed: 392664860)"
```

### Scenario 2: Reproduce Previous Image

```
User: "I love that office image! Regenerate it with seed 392664860"

Assistant actions:
1. Create config WITH seed:
   {
     "slides": [{"number": 1, "prompt": "Modern office interior with natural lighting", "seed": 392664860}],
     "output_dir": "./002-office-design-v2/"
   }
2. Execute script
3. Result: Visually identical image
```

### Scenario 3: Explore Variations

```
User: "Generate 3 variations of a robot holding flowers, use different temperatures"

Assistant actions:
1. Create config with per-slide temperatures:
   {
     "seed": 42,  // Same seed for comparison
     "slides": [
       {"number": 1, "prompt": "A cute robot holding flowers", "temperature": 0.5},
       {"number": 2, "prompt": "A cute robot holding flowers", "temperature": 1.0},
       {"number": 3, "prompt": "A cute robot holding flowers", "temperature": 1.5}
     ],
     "output_dir": "./003-robot-variations/"
   }
2. Execute script
3. Result: 3 different compositions (temperature effect)
```

### Scenario 4: Batch with Consistent Style

```
User: "Create 5 presentation slides with TrendLife style, use same seed"

Assistant actions:
1. Create config with global seed and appropriate layout for each slide:
   {
     "seed": 12345,
     "slides": [
       {"number": 1, "prompt": "AI Safety: Building Secure Systems", "style": "trendlife", "layout": "featured"},  // Title
       {"number": 2, "prompt": "Key features overview", "style": "trendlife", "layout": "content"},  // Content
       {"number": 3, "prompt": "Technical architecture", "style": "trendlife", "layout": "content"},  // Content
       {"number": 4, "prompt": "Use cases and benefits", "style": "trendlife", "layout": "content"},  // Content
       {"number": 5, "prompt": "Thank You - Contact Us", "style": "trendlife", "layout": "featured"}  // Closing
     ],
     "output_dir": "./004-ai-safety-deck/"
   }
2. Execute in background (5+ slides)
3. Monitor progress file
4. Results:
   - Slide 1 (featured): Logo integrated naturally by AI into title design
   - Slides 2-4 (content): Logo overlaid in bottom-right corner
   - Slide 5 (featured): Logo integrated naturally by AI into closing design
   - All slides use seed 12345 for visual consistency
```

## Common Errors and Solutions

If script execution fails, check these common issues:

### 1. "Logo file is Git LFS pointer" or "cannot identify image file"

**Most common issue**: User doesn't have Git LFS installed

- Logo files are managed by Git LFS - without it, you get text pointer files instead of images
- **Solution**:

  ```bash
  # Install Git LFS (once per machine)
  git lfs install

  # Pull actual files (in the plugin directory)
  git lfs pull
  ```

- Git LFS install: <https://git-lfs.com/>
- After installing, re-run the image generation command

### 2. "command not found: uv"

- User needs to install uv: <https://docs.astral.sh/uv/>
- **Solution**: Ask user to run:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 3. "Python 3.14+ recommended" or "Python 3.9+ required"

- First run with `--managed-python` downloads Python 3.14+ automatically
- If download fails, user can pre-install: `uv python install 3.14`
- Script supports Python 3.9+ as fallback but 3.14+ is recommended
- **Check**: Internet connection and disk space

### 4. Permission denied or download errors

- Check write permissions in uv cache directory (usually `~/.local/share/uv/`)
- **Verify**: Firewall/proxy settings allow uv to download Python

### 5. Missing dependencies (openai, pillow)

- Dependencies are automatically installed by `uv run` via PEP 723 metadata
- If user bypasses uv and runs script directly with python, they'll see standard ImportError
- **Solution**: Always use `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py`

## References

- **API compatibility**: `references/api-compatibility.md` (model × feature matrix, gpt-image-2 timeout data, API routing)
- **Advanced workflows**: `references/guide.md` (thinking, search grounding, 16+ prompting techniques)
- **Brand styles**: `references/brand-styles.md` (Trend Micro specs)
- **Slide decks**: `references/slide-deck-styles.md` (NotebookLM aesthetic, infographics, data viz)
- **Experiments**: `../EXPERIMENT_RESULTS.md` (temperature & seed testing results)
