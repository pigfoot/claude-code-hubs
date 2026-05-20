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

Unified image generation workflow using a fixed Python script with JSON configuration. Eliminates AI
hallucinations by avoiding dynamic code generation.

Two modes:

- **Unified Generation**: detailed prompt → write JSON config → run `generate_images.py`
- **Interactive Prompting**: vague prompt or "help me craft" → guide user, then generate

## When to Use

- Image generation ("draw", "create", "generate"), slides, presentations
- Image editing with AI
- Prompt help ("help me craft", "improve my prompt")
- Brand styles ("use trendlife style", "notebooklm style")
- Reproducible generation ("use seed 42", "regenerate that image")

## Mode selection

- **Interactive Prompting**: prompt help requested OR prompt is <5 words
- **Unified Generation**: detailed prompt provided

---

## 🚨 CRITICAL: API Routing

The script picks the API based on `IMAGE_GEN_MODEL` and `reference_image`:

| Condition | API | Endpoint |
|-----------|-----|----------|
| `gpt-image-2`, no `reference_image`, no TrendLife featured | `client.images.generate()` | POST `/images/generations` |
| `gpt-image-2` + `reference_image` | `client.images.edit()` | POST `/images/edits` |
| `gpt-image-2` + `style: "trendlife"` + `layout: "featured"` | `client.images.edit()` (logo as image) | POST `/images/edits` |
| Gemini or other | `client.chat.completions.create()` | POST `/chat/completions` |

**gpt-image-2**: Always uses `quality="low"` — other values timeout or return 400. Seed and temperature
unsupported (silently ignored, one warning per job).

**Gemini** (`gemini-3-pro-image`, `gemini-3.1-flash-image`): use `chat.completions` with
`extra_body={"response_modalities": ["IMAGE"]}`.

```python
client.chat.completions.create(
    model=os.environ.get("IMAGE_GEN_MODEL") or "gemini-3-pro-image",
    messages=[{"role": "user", "content": prompt}],
    seed=seed,
    temperature=temperature,
    extra_body={"response_modalities": ["IMAGE"]},
)
```

## IMAGE_GEN_MODEL: NEVER override

If `IMAGE_GEN_MODEL` is set, use it EXACTLY as-is. Custom endpoints have their own model names —
do not append suffixes like `-preview`. Only choose a default when the env var is unset.

```python
model = os.environ.get("IMAGE_GEN_MODEL")
if not model:
    model = "gemini-3-pro-image"
# Use as-is — do NOT add suffixes
```

Full model × feature matrix: `references/api-compatibility.md`

---

## Unified Generation Workflow

1. **Create config** — write JSON to system temp dir (NOT skill directory):
   - `Write` tool → `{temp_dir}/nano-banana-config-{timestamp}.json`
2. **Execute** — `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py --config <temp_config_path>`
   - **CRITICAL**: use `${CLAUDE_SKILL_DIR}` prefix without `cd` — keeps cwd in user's project so relative
     paths in config resolve correctly.
   - ❌ `cd scripts && uv run --managed-python generate_images.py ...`
   - ✅ `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py ...`
3. **Track progress** — monitor progress/results files (background tasks)
4. **Return paths** — report generated image locations

5+ slides → automatic background execution. Details: `references/batch-generation.md`

### Config

Minimal:

```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-feature-name/"
}
```

- `output_dir` MUST be `./NNN-short-name/` (relative path, 3-digit number, kebab-case)
- No absolute paths, no `model` field (use env var), no `seed`/`temperature` for gpt-image-2

Full schema, format selection, layout field rules, gpt-image-2 examples: `references/config-reference.md`

### Seed & Temperature (Gemini only)

- "seed 42" → `"seed": 42`
- "regenerate with seed 392664860" → use seed from previous results JSON
- "temperature 0.5" / "temp 1.5" / "more creative" → `"temperature"` field
- Priority: `slide.seed` > `config.seed` > auto-generate

Same seed + same prompt + same temperature = identical image. Auto-seeds are recorded in
`{output_dir}/generation-results.json`.

Full parsing patterns + reproducibility detail: `references/temperature-seed.md`

### Style Detection

Detect `style: "trendlife"`, `style: "notebooklm"`, or natural language ("use trendlife style").

- **TrendLife**: Trend Red (#D71920), automatic logo overlay — see `references/logo-overlay.md` and
  `references/brand-styles.md`
- **NotebookLM**: clean presentation aesthetic. ⚠️ NEVER use "NotebookLM" name/logo in prompts
  (trademark) — see `references/slide-deck-styles.md`

Priority: inline spec → ask in Interactive Mode → no style (default).

### TrendLife layout field

| Value | Use for | Logo handling |
|-------|---------|---------------|
| `"featured"` | title, divider, closing | Logo as reference image, AI integrates naturally |
| `"content"` | information slides | Post-generation overlay, bottom-right corner |
| omitted | (auto-detect from keywords — less reliable) | — |

Always specify `layout` explicitly for TrendLife. Full detection rules + manual override:
`references/logo-overlay.md`

---

## Interactive Prompting Mode

Trigger: prompt help requested OR prompt <5 words.

| Step | Action |
|------|--------|
| 1. Gather | Check for reference images, existing prompts, inline style specs |
| 2. Clarify | `AskUserQuestion`: output type? subject? style? |
| 3. Select technique | Pick from 16+ patterns in `references/guide.md` |
| 4. Generate prompt | Apply technique + brand style + aspect ratio |
| 5. Present | Show prompt with explanation and variations |
| 6. Execute | Run via Unified Generation Workflow |

Brand style integration:

- **TrendLife** (`style: "trendlife"`): see `references/brand-styles.md`
- **NotebookLM** (`style: "notebooklm"`): use "clean professional presentation aesthetic" — never the
  "NotebookLM" name. See `references/slide-deck-styles.md`

Techniques and examples: `references/guide.md`

---

## References

| Topic | File |
|-------|------|
| API compatibility, model × feature matrix | `references/api-compatibility.md` |
| Batch / multi-slide generation | `references/batch-generation.md` |
| TrendLife brand specs | `references/brand-styles.md` |
| Config schema, layout field, format selection | `references/config-reference.md` |
| Example workflows (4 scenarios) | `references/examples.md` |
| Prompting techniques (16+) | `references/guide.md` |
| Logo overlay rules + manual override | `references/logo-overlay.md` |
| NotebookLM / infographic / data-viz styles | `references/slide-deck-styles.md` |
| Seed & temperature (Gemini only) | `references/temperature-seed.md` |
| Errors, debugging, RONE limitations | `references/troubleshooting.md` |
| Temperature & seed testing data | `../EXPERIMENT_RESULTS.md` |
