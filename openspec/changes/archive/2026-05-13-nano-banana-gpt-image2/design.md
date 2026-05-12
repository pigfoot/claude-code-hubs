## Context

`generate_images.py` uses a single `client.chat.completions.create()` call for all models. This works for Gemini
(`gemini-3-pro-image`, `gemini-3.1-flash-image`) which expose image generation through the `chat.completions`
endpoint with `response_modalities: ["IMAGE"]`. gpt-image-2 is routed differently on the RONE proxy — it uses
the OpenAI Images API contract (`/images/generations` and `/images/edits`), and `chat.completions` returns 400.

Confirmed via testing (2026-05-12/13):
- gpt-image-2 + `chat.completions` → 400 "operation is unsupported"
- gpt-image-2 + `/images/generations` → ✅ (`client.images.generate()`)
- gpt-image-2 + `/images/edits` → ✅ (`client.images.edit()`, multipart, `quality=low` required)

## Goals / Non-Goals

**Goals:**
- Support gpt-image-2 text-to-image via `client.images.generate()`
- Support gpt-image-2 image editing (with reference image) via `client.images.edit()`
- Zero changes to Gemini code path
- Keep JSON config format backward-compatible (new field is optional)

**Non-Goals:**
- Inpainting / mask support (can be added later)
- gpt-image-2 seed/temperature control (API does not support these)
- Multi-image output per slide (`n > 1`)
- Automatic quality fallback / retry on timeout

## Decisions

### 1. Model-based routing in `generate_slide()`

Detect model at runtime: if `model == "gpt-image-2"`, dispatch to new gpt-image-2 paths; otherwise keep existing
`chat.completions` path.

**Why not a separate script?** The unified-generation spec requires all generation to go through
`generate_images.py`. A separate script would break that invariant and split maintenance burden.

**Why model name, not a config flag?** `IMAGE_GEN_MODEL` already controls model selection. Adding a separate
`api_backend` flag would be redundant and confusing. Model name is the authoritative signal.

### 2. Two sub-paths for gpt-image-2

| Condition | API Call |
|---|---|
| No `reference_image` in slide config | `client.images.generate()` |
| `reference_image` present | `client.images.edit()` |

**Why not always use `/images/edits`?** `/images/edits` requires an input image and costs more time (~37s min vs
~72s for `/images/generations`... wait, actually generations is slower). Both paths are needed because
`/images/edits` requires a source image and `/images/generations` does not.

### 3. `reference_image` as a slide-level config field

```json
{"number": 1, "prompt": "Add a blue border", "reference_image": "./source.png"}
```

Path is resolved relative to the working directory (same convention as `output_dir`). This keeps the config
self-contained and consistent with existing relative-path conventions.

**Why not pass image via env var?** Per-slide images cannot be expressed as env vars. Config field is the
natural place.

### 4. `quality=low` hardcoded for gpt-image-2

Both `/images/generations` and `/images/edits` default to `quality=low`. This is not user-configurable via the
existing `quality` config field (which controls output image compression, not API quality).

**Why hardcode?** Testing shows `quality=medium` takes ~110s and higher qualities timeout. The RONE proxy has a
~180s timeout. Exposing this as a user option risks silent timeouts with no clear error. A future change can
expose it once timeout handling is added.

**Naming conflict note:** The config's `quality` field (1–100, for image file compression) is distinct from
the API's `quality` param (`low`/`medium`/`high`). The gpt-image-2 API quality is internal to the script.

### 5. Response extraction — separate helper per path

- `chat.completions` path: `_extract_image_bytes()` (existing, reads `message.images[]`)
- `/images/generations` path: reads `response.data[0].b64_json` directly
- `/images/edits` path: reads `response.data[0].b64_json` directly

No shared helper — the response shapes are too different to unify cleanly.

## Risks / Trade-offs

- **Timeout on `/images/generations`** (~72s at `quality=low`) — Claude Code default tool timeout may need to be
  raised. Users should be informed. Mitigation: document in SKILL.md; consider background execution for gpt-image-2.
- **`reference_image` path resolution** — relative paths resolve from cwd, which may differ from config file
  location. Mitigation: document clearly; emit a clear error if file not found.
- **gpt-image-2 no seed support** — reproducibility is not possible for gpt-image-2 slides. Mitigation: document
  in SKILL.md; results JSON will omit `seed` for gpt-image-2 slides.
- **Mixed-model batches** — a config with both Gemini and gpt-image-2 slides works correctly (each slide routes
  independently) but results in very different per-slide timings. Not a bug but may surprise users.

## Open Questions

- Should gpt-image-2 slides always run in background given ~72s+ latency? (Current threshold is 5+ slides)
- Should `quality=medium` be exposed with a warning, or stay hardcoded to `low`?
