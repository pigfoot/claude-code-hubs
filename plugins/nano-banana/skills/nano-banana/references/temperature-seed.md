# Temperature & Seed Parameters (Gemini only)

> **gpt-image-2**: Seed and temperature are **not supported** by the RONE endpoint.
> The script emits a warning (once per job) and ignores both fields.
> Use Gemini models if you need reproducible generation.

## Seed parameter (recommended)

Enable reproducible image generation.

- Same seed + same prompt + same temperature = visually identical image
- Default: auto-generated timestamp-based seed (recorded in results JSON)
- Use case: "I like this image, regenerate it exactly"

User natural language patterns:

- "use seed 42"
- "regenerate with seed 392664860"
- "same seed as before"
- "seed: 123" (inline spec)

Config examples:

```json
// Global seed (all slides use same seed)
{"seed": 42, "slides": [...]}

// Per-slide seed
{"slides": [
  {"number": 1, "prompt": "...", "seed": 42},
  {"number": 2, "prompt": "...", "seed": 123}
]}

// No seed specified (auto-generate, recorded in results)
{"slides": [...]}
```

## Results tracking

All generated images record their actual seed in `{output_dir}/generation-results.json`:

```json
{
  "outputs": [
    {"slide": 1, "path": "slide-01.png", "seed": 392664860, "temperature": 1.0}
  ]
}
```

## Temperature parameter (experimental)

Range 0.0–2.0. Gemini 3 official guidance: keep default 1.0.

- ⚠️ Limited impact observed in testing — changes output but effect is unpredictable
- No clear "low = conservative, high = creative" pattern
- Changes generation result when combined with same seed

Patterns:

- "temperature 0.5"
- "use lower temperature"
- "more creative (temperature 1.5)"
- "temperature: 0.8"

Recommendation:

- ✅ Use seed for reproducibility (highly effective)
- ⚠️ Use temperature conservatively for experimentation only
- 💡 Keep default 1.0 unless exploring variations

## Priority rules

- `slide.temperature` > `config.temperature` > 1.0 (default)
- `slide.seed` > `config.seed` > auto-generate

## Parsing user intent

### Seed

- "seed 42" → `"seed": 42`
- "use seed 392664860" → `"seed": 392664860`
- "regenerate with the same seed" → use seed from previous results JSON
- "seed: 123" (inline) → `"seed": 123`

### Temperature

- "temperature 0.5" → `"temperature": 0.5`
- "temp 1.5" → `"temperature": 1.5`
- "lower temperature" → `"temperature": 0.5`
- "higher temperature" / "more creative" → `"temperature": 1.5`
- "temperature: 0.8" (inline) → `"temperature": 0.8`

### Combined examples

```
User: "Generate a robot image, seed 42, temperature 0.8"
→ Config: {"slides": [{"number": 1, "prompt": "robot", "seed": 42, "temperature": 0.8}]}

User: "Regenerate that image with seed 392664860"
→ Config: {"slides": [{"number": 1, "prompt": "<previous_prompt>", "seed": 392664860}]}

User: "Create 3 slides with same seed 100"
→ Config: {"seed": 100, "slides": [{...}, {...}, {...}]}
```
