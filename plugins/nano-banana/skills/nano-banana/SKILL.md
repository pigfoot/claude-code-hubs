---

# === Required (All Platforms) ===

name: nano-banana
description: |
  Use when users request image generation, AI art creation, image editing with Gemini models, need help crafting prompts, or want brand-styled imagery. Handles both direct generation and interactive prompt design.

# === Claude Code / OpenAI Codex ===

allowed-tools: Bash Write Read AskUserQuestion
metadata:
  short-description: Unified image generation workflow with Gemini/Imagen models
  version: "0.0.9"

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

### API Selection Rule

#### BEFORE writing ANY code, determine which API to use

```python
model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"

# Select API based on model name
if "imagen" in model.lower():
    use_imagen_api = True   # → generate_images()
else:
    use_imagen_api = False  # → generate_content()
```

### Two COMPLETELY DIFFERENT APIs

These are **NOT interchangeable**. Using the wrong API will cause errors.

| | **Gemini Image** | **Imagen** |
|---|---|---|
| **API Method** | `generate_content()` | `generate_images()` |
| **Config Type** | `GenerateContentConfig` | `GenerateImagesConfig` |
| **Models** | `gemini-*-image*` | `imagen-*` |
| **Prompt Format** | `contents=[prompt]` (array) | `prompt=prompt` (string) |
| **Response** | `response.parts` | `response.generated_images` |
| **Special Config** | `response_modalities=['IMAGE']` | Not used |

#### Example model detection

```python
# These trigger Imagen API:
"imagen-4.0-generate-001" → generate_images()
"custom-imagen-v2" → generate_images()

# These trigger Gemini API:
"gemini-3-pro-image-preview" → generate_content()
"gemini-2.5-flash-image" → generate_content()
"custom-gemini-image" → generate_content()
```

### ❌ DOES NOT EXIST - Never Use These

If you find yourself writing these, **STOP** - you are using the wrong API:

| ❌ Wrong (Does NOT exist) | ✅ Correct |
|--------------------------|-----------|
| `types.ImageGenerationConfig` | Use `GenerateContentConfig` (Gemini) or `GenerateImagesConfig` (Imagen) |
| `generate_images()` + Gemini model | Use `generate_content()` for Gemini models |
| `generate_content()` + Imagen model | Use `generate_images()` for Imagen models |
| `response_modalities` in Imagen | Only use with Gemini's `GenerateContentConfig` |

### NANO_BANANA_MODEL: NEVER Override

**Rule:** If `NANO_BANANA_MODEL` is set, use it EXACTLY as-is.

❌ **WRONG - Do NOT do this:**

```python
model = os.environ.get("NANO_BANANA_MODEL", "gemini-3-pro-image")
if not model.endswith("-preview"):
    model = f"{model}-preview"  # ❌ NEVER modify user's model name
```

✅ **CORRECT:**

```python
model = os.environ.get("NANO_BANANA_MODEL")
if not model:
    # Only choose default when NANO_BANANA_MODEL is NOT set
    model = "gemini-3-pro-image-preview"
# Use model EXACTLY as-is - do NOT add suffixes or change names
```

#### Why this matters

- Custom endpoints have their own model names (e.g., `gemini-3-pro-image` without `-preview`)
- User explicitly set the model they want
- DO NOT apply Google's naming conventions to custom endpoints

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

1. Generate slide image with TrendLife colors (no logo in prompt)
2. Detect layout type from prompt content
3. Apply logo overlay with `logo_overlay.overlay_logo()`
4. Output final image with logo

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
logo_path = Path(__file__).parent / 'assets/logos/trendlife-logo.png'

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

### API Selection (CRITICAL - Check First)

| Model Name Contains | API to Use | Config Type |
|---------------------|------------|-------------|
| `imagen` | `generate_images()` | `GenerateImagesConfig` |
| Anything else | `generate_content()` | `GenerateContentConfig` |

#### See CRITICAL section above for complete details

### Unified Generation Workflow

All image generation uses the same fixed Python script with JSON config:

1. **Create Config:** Write JSON to system temp directory (NOT skill directory)
   - Use `Write` tool with path: `{temp_dir}/nano-banana-config-{timestamp}.json`
   - Get temp_dir from user's OS temp location (cross-platform)
2. **Execute Script:** `uv run --managed-python {base_dir}/generate_images.py --config <temp_config_path>`
   - `{base_dir}` is the skill base directory provided by Claude Code when loading the skill
   - **CRITICAL:** Use absolute path to script WITHOUT changing directory (no `cd` command)
   - **WRONG:** `cd {base_dir} && uv run --managed-python generate_images.py ...` ❌
   - **CORRECT:** `uv run --managed-python {base_dir}/generate_images.py ...` ✅
   - This ensures execution cwd remains in user's project directory, so relative paths in config work correctly
3. **Track Progress:** Monitor progress/results files (for background tasks)
4. **Return Paths:** Report generated image locations

#### IMPORTANT

- Always write config to system temp directory, NEVER to skill base directory
- Always use `{base_dir}/generate_images.py` for the script path (cross-platform compatible)

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
      "temperature": 0.8,  // Optional: 0.0-2.0 per-slide override
      "seed": 42           // Optional: integer for reproducible generation
    }
  ],
  "output_dir": "./001-feature-name/",  // MUST use NNN-short-name format
  "format": "webp",      // Optional: webp (default, RECOMMENDED), png, jpg
  "quality": 90,         // Optional: 1-100 (default: 90)
  "temperature": 1.0,    // Optional: 0.0-2.0 global default (default: 1.0)
  "seed": 12345          // Optional: integer global default (default: auto-generate)
}
```

#### Format Selection Guide

- **webp (RECOMMENDED)**: Default format, automatically uses lossless compression for presentation styles (trendlife,
  professional, data-viz). Same quality as PNG but 25-35% smaller file size.
- **png**: Only use if webp compatibility is a concern (rare). Larger file size.
- **jpg**: For photos only, not suitable for slides/diagrams (lossy compression).

### Temperature & Seed Parameters

#### ⚡ NEW: Reproducible Generation

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
- ❌ NO absolute paths (breaks cross-platform)
- ❌ NO plain names without numbers (e.g., `./slides/` is WRONG)
- ❌ NO `model` field (use NANO_BANANA_MODEL env var)

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
| `GEMINI_API_KEY not set` | `export GEMINI_API_KEY="your-key"` |
| `Model not found` | Check exact model name, use `-preview` suffix if needed |
| Wrong API used | Check CRITICAL section: Gemini vs Imagen |
| `ModuleNotFoundError` | Verify `# dependencies = ["google-genai", "pillow"]` |
| No image generated | Check `response.parts` (Gemini) or `response.generated_images` (Imagen) |
| `Invalid aspect ratio` | Use exact strings: `"16:9"`, `"1:1"`, `"9:16"` (with quotes) |

### Debug Steps

1. Verify API key: `echo $GEMINI_API_KEY`
2. Test with simple prompt: `"A red circle"`
3. Check response object: `print(response.parts)` or `print(response.generated_images)`
4. Review CRITICAL section if API errors occur

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| **Using `types.ImageGenerationConfig`** | **Does NOT exist - use `GenerateContentConfig` or `GenerateImagesConfig`** |
| **Using `generate_images()` with Gemini** | **Use `generate_content()` for Gemini models** |
| **Using `generate_content()` with Imagen** | **Use `generate_images()` for Imagen models** |
| Overriding `NANO_BANANA_MODEL` when set | Use model EXACTLY as-is - don't add suffixes |
| Using `google-generativeai` (old library) | Use `google-genai` (new library) |
| Using text models for image gen | Use image models only (`gemini-*-image*` or `imagen-*`) |
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
2. Execute: uv run --managed-python {base_dir}/generate_images.py --config {temp_config}
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
1. Create config with global seed:
   {
     "seed": 12345,
     "slides": [
       {"number": 1, "prompt": "Title slide: AI Safety", "style": "trendlife"},
       {"number": 2, "prompt": "Key features overview", "style": "trendlife"},
       {"number": 3, "prompt": "Technical architecture", "style": "trendlife"},
       {"number": 4, "prompt": "Use cases and benefits", "style": "trendlife"},
       {"number": 5, "prompt": "Thank you slide", "style": "trendlife"}
     ],
     "output_dir": "./004-ai-safety-deck/"
   }
2. Execute in background (5+ slides)
3. Monitor progress file
4. Results: 5 slides with TrendLife logo, all use seed 12345 + auto-incremented variation
```

## References

- **Advanced workflows**: `references/guide.md` (thinking, search grounding, 16+ prompting techniques)
- **Brand styles**: `references/brand-styles.md` (Trend Micro specs)
- **Slide decks**: `references/slide-deck-styles.md` (NotebookLM aesthetic, infographics, data viz)
- **Experiments**: `../EXPERIMENT_RESULTS.md` (temperature & seed testing results)
