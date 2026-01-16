---
name: nano-banana
description: Use when users request image generation, AI art creation, image editing with Gemini models, need help crafting prompts, or want brand-styled imagery. Handles both direct generation and interactive prompt design.
---

# Nano Banana

Quick Python scripting with Gemini/Imagen image generation using uv heredocs. **No files needed for one-off tasks.**

Supports two modes:
- **Direct Generation**: Run immediately with user's prompt
- **Interactive Prompting**: Guide user through prompt design with proven techniques

---

## 🚨 CRITICAL: Read This First

### API Selection Rule

**BEFORE writing ANY code, determine which API to use:**

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

**Example model detection:**
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

**Why this matters:**
- Custom endpoints have their own model names (e.g., `gemini-3-pro-image` without `-preview`)
- User explicitly set the model they want
- DO NOT apply Google's naming conventions to custom endpoints

### Complete Code Examples

For full working examples, see:
- **Gemini API:** `references/gemini-api.md`
- **Imagen API:** `references/imagen-api.md`

---

## When to Use

- Image generation ("draw", "create", "generate"), slides, presentations
- Image editing with AI
- Prompt help ("help me craft", "improve my prompt")
- Brand styles ("use style trend", "notebooklm style")

**Mode selection:**
- **Interactive Prompting**: User asks for prompt help OR prompt too vague (<5 words)
- **Direct Generation**: User provides detailed prompt

## Style Detection

**Detect:** `style: "trend"`, `style: "notebooklm"`, or natural language ("use style trend", "notebooklm style")

**Styles:**
- **Trend**: Trend Micro brand colors (Trend Red #d71920)
- **NotebookLM**: Clean presentation aesthetic (⚠️ **NEVER** use "NotebookLM" brand/logo in prompts)

**Priority:** Inline spec → Ask in Interactive Mode → No style (Direct Mode default)

## Quick Reference

### API Selection (CRITICAL - Check First)

| Model Name Contains | API to Use | Config Type |
|---------------------|------------|-------------|
| `imagen` | `generate_images()` | `GenerateImagesConfig` |
| Anything else | `generate_content()` | `GenerateContentConfig` |

**See CRITICAL section above for complete details.**

### Direct Generation Mode

| Task | Pattern |
|------|---------|
| **API Selection** | Check model name → use correct API (see above) |
| Generate image (Gemini) | `generate_content()` with `response_modalities=['IMAGE']` |
| Generate image (Imagen) | `generate_images()` with `prompt=string` |
| Edit image | `generate_content()` with `contents=[prompt, img]` |
| Model choice | Use `NANO_BANANA_MODEL` if set (don't override) |
| Output format | Default: `webp`, or `NANO_BANANA_FORMAT` (webp/jpg/png) |
| Output location | `NNN-short-name/` (e.g., `001-cute-banana/`) |
| Complete examples | See `references/gemini-api.md` or `references/imagen-api.md` |

### Interactive Prompting Mode

| Step | Action |
|------|--------|
| 1. Gather | Check for reference images, style specs |
| 2. Clarify | Ask 2-4 questions about output type, subject, style |
| 3. Select Technique | Choose from 16+ patterns (see references/guide.md) |
| 4. Generate Prompt | Apply technique, brand style, aspect ratio |
| 5. Present | Show prompt with explanation and variations |
| 6. Execute | Generate image with crafted prompt |

## Direct Generation Mode

### Core Pattern: Heredoc Scripts

**API Selection:**
```python
# Step 1: Determine which API to use (see CRITICAL section above)
model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
use_imagen_api = "imagen" in model.lower()
```

**Minimal Gemini Example:**
```python
# For Gemini models (gemini-*-image*)
response = client.models.generate_content(
    model=model,
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K")
    )
)
# Access: response.parts[0].as_image()
```

**Minimal Imagen Example:**
```python
# For Imagen models (imagen-*)
response = client.models.generate_images(
    model=model,
    prompt=prompt,  # Note: string, NOT array
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="1:1"
    )
)
# Access: response.generated_images[0].image
```

**Complete heredoc templates with directory handling, format conversion, and error handling:**
- **Gemini:** See `references/gemini-api.md`
- **Imagen:** See `references/imagen-api.md`

**Key requirements:**
- Use `google-genai` library (NOT `google-generativeai`)
- Inline script metadata: `# /// script` block with dependencies
- Required deps: `["google-genai", "pillow"]`

### Output Directory Naming

**Format:** `NNN-short-name/` (e.g., `001-cute-banana/`)

**Directory selection:**
- **Continuation** (editing/adding to existing work) → Reuse directory: `OUTPUT_DIR = Path("001-existing")`
- **New topic** (unrelated to previous) → Auto-increment: scan for highest NNN, create NNN+1
- **Uncertain** → Ask user with `AskUserQuestion`

**Auto-increment logic:** See complete code in `references/gemini-api.md` or `references/imagen-api.md`

### Configuration

Customize plugin behavior with environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NANO_BANANA_MODEL` | (Claude chooses) | Specify image generation model. If set, Claude will NOT override it. Valid models: `gemini-3-pro-image-preview` (quality), `gemini-2.5-flash-image` (speed) |
| `NANO_BANANA_FORMAT` | `webp` | Output format: `webp`, `jpg`, or `png` |
| `NANO_BANANA_QUALITY` | `90` | Image quality (1-100) for webp/jpg |
| `GOOGLE_GEMINI_BASE_URL` | (official API) | Custom API endpoint (for non-official deployments) |
| `GEMINI_API_KEY` | (falls back to `GOOGLE_API_KEY`) | API key (official or custom endpoint) |

**Model Selection Guidelines:**

When `NANO_BANANA_MODEL` is NOT set, Claude selects model based on user requirements:
- **Default**: `gemini-3-pro-image-preview` - Best quality, accurate colors, good text rendering (recommended for slides)
- **Speed/Budget**: `gemini-2.5-flash-image` - Faster generation, lower cost (ONLY when user explicitly requests speed/budget)

**IMPORTANT**: These are IMAGE generation models from the `gemini-image` API series. Do NOT use text generation models like `gemini-2.0-flash-exp`, `gemini-exp-1206`, or `gemini-2.0-flash-thinking-exp-*` - they are incompatible with image generation.

**Lossless WebP Logic:** Set `use_lossless = True` for:
- Slide deck styles (`style: trend` or `style: notebooklm`)
- User explicitly requests lossless/highest quality/for printing
- Default: `False` (photos)

### Image Editing

**Directory strategy:** Editing = continuation of same topic → **reuse the source image's directory**.

**Key difference:** Include the existing image in `contents=[]`

```python
from PIL import Image as PILImage

# Load existing image
img = PILImage.open("001-cute-banana/generated.webp")

# Pass image with prompt
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
```

**Complete heredoc template:** See `references/gemini-api.md` (Image Editing section)

### Image Configuration

**Aspect ratio and resolution (Gemini only):**
```python
image_config=types.ImageConfig(
    aspect_ratio="16:9",  # "1:1", "16:9", "9:16", "4:3", "3:4"
    image_size="2K"       # "1K", "2K", "4K"
)
```

**Common ratios:** 16:9 (slides), 1:1 (social), 9:16 (stories), 4:3 (documents)
**Resolutions:** 1K (drafts), 2K (default), 4K (high-res prints)

**Complete specs:** See `references/gemini-api.md`

### Workflow: Small Scripts, Iterate

1. Run ONE script → Check output → Done or refine?
2. Don't: orchestrate, auto-chain, build systems
3. Do: Small heredoc scripts, manual evaluation between steps

### Multi-Slide Generation

**Automatic Mode Selection:**
- **5+ slides** → Batch mode (background task, progress tracking, 80% context reduction)
- **1-4 slides** → Direct execution (immediate feedback, current behavior)

**Batch Mode Quick Reference (5+ slides):**
1. Create config JSON with all slide specs
2. Start background task: `uv run generate_batch.py --config /tmp/slides_config.json` with `run_in_background=True`
3. Poll `/tmp/nano-banana-progress.json` every 10-15s to update user
4. Read `/tmp/nano-banana-results.json` when complete

**IMPORTANT:** Script MUST be run with `uv run` (handles dependencies automatically)

**Complete workflow, code examples, and schemas:** See `references/batch-generation.md`

### Red Flags - STOP and Use Heredoc

If you're thinking any of these thoughts, you're over-engineering:
- "This might be reused later"
- "Let me create proper structure"
- "I'll document this for reference"
- "Let me build a workflow system"
- "I should make this configurable"
- "This is complex, I need proper files"

**All of these mean: Use heredoc. It's a one-off task.**

## Interactive Prompting Mode

**When to use:** User requests prompt help ("help me craft", "improve my prompt") or prompt is too vague (<5 words).

### Workflow

1. **Gather** - Check for reference images, existing prompts, inline style specs (`style: "trend"`)
2. **Clarify** - Use `AskUserQuestion`: Output type? Subject? Style preference?
3. **Select Technique** - Choose from 16+ patterns in `references/guide.md`
4. **Generate Prompt** - Apply technique + brand style + aspect ratio
5. **Present** - Show prompt with explanation and variations
6. **Execute** - Generate using Direct Generation Mode

**Brand Style Integration:**

- **NotebookLM style** (`style: "notebooklm"`):
  - Apply aesthetic: polished tech infographic, clean slide layout, minimal text
  - ⚠️ **NEVER** use "NotebookLM" brand/logo/name in prompts (trademark violation)
  - ✅ Use: "clean professional presentation aesthetic", "modern tech infographic style"
  - See `references/slide-deck-styles.md` for complete specs

- **Trend Micro style** (`style: "trend"`):
  - Colors: Trend Red (#d71920), Guardian Red (#6f0000), Grays (#58595b-#e6e7e8)
  - See `references/brand-styles.md` for complete specs

**Complete techniques and examples:** See `references/guide.md`

## Files vs Heredoc

**Use heredoc** (default) for one-off tasks. **Create files** only when:
- Will be run multiple times
- User explicitly asks for a file
- Complex script needing iteration/debugging

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
| Creating permanent `.py` files | Use heredoc for one-off tasks |
| Saving to flat files | Use `NNN-short-name/` directories |
| Using PIL to draw/edit | Use Gemini/Imagen API with image in `contents` |

## References

- **Advanced workflows**: `references/guide.md` (thinking, search grounding, 16+ prompting techniques)
- **Brand styles**: `references/brand-styles.md` (Trend Micro specs)
- **Slide decks**: `references/slide-deck-styles.md` (NotebookLM aesthetic, infographics, data viz)
