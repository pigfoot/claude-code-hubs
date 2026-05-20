# Config Reference

## Minimal config

```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-feature-name/"
}
```

## Full config

```json
{
  "slides": [
    {
      "number": 1,
      "prompt": "...",
      "style": "trendlife",
      "layout": "featured",
      "temperature": 0.8,
      "seed": 42,
      "reference_image": "./src.png"
    }
  ],
  "output_dir": "./001-feature-name/",
  "format": "webp",
  "quality": 90,
  "temperature": 1.0,
  "seed": 12345
}
```

## gpt-image-2 example

```json
{
  "slides": [
    {"number": 1, "prompt": "A futuristic cityscape at night"},
    {"number": 2, "prompt": "Add a moon to the sky", "reference_image": "./001-city/slide-01.webp"}
  ],
  "output_dir": "./002-city-edit/"
}
```

## Format selection

- **webp (RECOMMENDED)**: Default. Lossless for presentation styles. Same quality as PNG, 25–35% smaller.
- **png**: Only if webp compatibility is a concern.
- **jpg**: Photos only — lossy, unsuitable for slides/diagrams.

## Layout field (TrendLife only)

Controls logo integration strategy.

- **`"featured"`** — title slides, dividers, closing slides
  - Logo used as reference image during AI generation
  - Gemini: passed as `image_url` in `chat.completions`
  - gpt-image-2: passed as `image` param in `/images/edits`
  - AI integrates logo naturally
- **`"content"`** — information slides
  - Logo overlaid in bottom-right corner (50px, 25px padding)
  - Fixed positioning; consistent across content slides
- **Omitted/null** — auto-detection from prompt keywords (less reliable; specify explicitly)

Examples:

```json
{"number": 1, "prompt": "Product Launch 2026", "style": "trendlife", "layout": "featured"}
{"number": 3, "prompt": "Part 2: Technical Details", "style": "trendlife", "layout": "featured"}
{"number": 6, "prompt": "Thank You", "style": "trendlife", "layout": "featured"}
{"number": 2, "prompt": "Key features and benefits", "style": "trendlife", "layout": "content"}
```

When generating JSON for TrendLife presentations:

1. Analyze each slide's purpose (not just keywords)
2. Title/cover/divider/closing → `"layout": "featured"`
3. Information/data/content → `"layout": "content"`
4. Always specify `layout` explicitly — don't rely on auto-detection

## Field rules

- ✅ `output_dir` MUST be relative path with `NNN-short-name/` format: `./001-feature-name/`
  - Examples: `./001-ai-safety/`, `./002-threat-detection/`, `./003-user-onboarding/`
- ✅ `reference_image` MUST be a relative path (e.g., `"./source.png"`) — gpt-image-2 only; triggers `/images/edits`
- ❌ NO absolute paths (breaks cross-platform)
- ❌ NO plain names without numbers (e.g., `./slides/` is WRONG)
- ❌ NO `model` field (use `IMAGE_GEN_MODEL` env var)
- ❌ NO `seed` or `temperature` for gpt-image-2 slides (unsupported; silently ignored)

## Output directory behavior

- Relative paths resolve to user's current working directory
- Script is executed with absolute path, but cwd remains in user's directory
- Use sequential numbering for different presentation topics

## Config file location

Always write config to system temp directory, never to skill base directory.

```
# Linux/macOS: /tmp/nano-banana-config-{timestamp}.json
# Windows:     %TEMP%/nano-banana-config-{timestamp}.json
```
