## Why

`generate_images.py` currently only supports Gemini models via `chat.completions`. gpt-image-2 is now available on
the RONE endpoint but requires different API paths — `/images/generations` for text-to-image and `/images/edits` for
image editing — neither of which the current script handles.

## What Changes

- Add `/images/generations` code path to `generate_images.py` for gpt-image-2 text-to-image
- Add `/images/edits` code path to `generate_images.py` for gpt-image-2 image editing (with reference image input)
- Route requests automatically based on model name (`gpt-image-2` → new paths, everything else → existing `chat.completions`)
- Add `reference_image` field to slide config for editing mode
- Update SKILL.md with gpt-image-2 usage, timeout guidance, and capability matrix

## Capabilities

### New Capabilities

- `gpt-image2-generation`: Text-to-image via `/images/generations` — response format, size options, quality
  constraints (`low`/`medium` only, `quality=low` recommended to stay within ~72s)
- `gpt-image2-editing`: Image editing via `/images/edits` multipart — reference image input, size constraints,
  response format (`data[0].b64_json`), quality constraint (`low` only, ~37–152s)

### Modified Capabilities

- `unified-generation`: Config schema gains optional `reference_image` field (path to source image) per slide;
  routing logic added to dispatch gpt-image-2 to new endpoints while keeping existing Gemini path unchanged

## Impact

- `plugins/nano-banana/skills/nano-banana/scripts/generate_images.py` — new code paths, routing logic
- `plugins/nano-banana/skills/nano-banana/SKILL.md` — usage docs, capability matrix, timeout table
- Config JSON schema — new optional `reference_image` field per slide
- No breaking changes — existing Gemini workflows unaffected; gpt-image-2 opt-in via `IMAGE_GEN_MODEL`

## Confirmed Behaviour (from testing 2026-05-12/13)

| API Path | Quality | Time | Status |
|---|---|---|---|
| `chat.completions` (gpt-image-2) | any | 2.7s | ❌ 400 unsupported |
| `/images/generations` | `low` | ~72s | ✅ |
| `/images/generations` | `medium` | ~110s | ✅ |
| `/images/edits` | `low` | ~37s | ✅ |
| `/images/edits` | omitted/auto/high | — | ❌ timeout/400 |
