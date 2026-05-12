## Context

nano-banana currently uses the `google-genai` library to call the Gemini native API at paths like `/v1beta/models/...`. The backend is a LiteLLM proxy (`https://api.rdsec.trendmicro.com/prod/aiendpoint`) that exposes both the Gemini native route and an OpenAI-compatible route at `/v1/`.

Testing confirmed (2026-05-06):
- `images.generate() + extra_body seed` → seed has no effect (dropped by proxy for Gemini; Azure backend returns 400 for gpt-image-2)
- `chat.completions() + seed=` → seed works (standard parameter, correctly forwarded to Gemini generationConfig.seed)
- `chat.completions() + messages[image_url]` → reference images work
- Image is returned in `message.images[]` (LiteLLM non-standard field, not `content`)
- `gpt-image-2 + images.generate()` → works for basic generation
- `gpt-image-2 + chat.completions()` → 400 "unsupported operation" (Azure backend)
- `gpt-image-2 + seed (any path)` → not supported (Azure backend rejects the parameter)

## Goals / Non-Goals

**Goals:**
- Replace `google-genai` with `openai` library
- Rename env vars (NANO_BANANA_MODEL → IMAGE_GEN_MODEL, GOOGLE_GEMINI_BASE_URL → IMAGE_GEN_BASE_URL, GEMINI_API_KEY → RDSEC_API_KEY)
- Make `seed` and `temperature` actually effective via `chat.completions` standard parameters
- Continue supporting reference images (TrendLife featured slides)
- Remove the Imagen API path

**Non-Goals:**
- Supporting non-LiteLLM OpenAI-compatible endpoints
- Backward compatibility with old env var names (one-time breaking change)
- Changing any image style or prompt logic

## Decisions

### D1: Use chat.completions for all generation, not images.generate

`images.generate()` is simpler but `seed` via `extra_body` does not work, and it does not support reference images. `chat.completions()` handles both, and a single code path reduces branching.

```python
client.chat.completions.create(
    model=model,
    messages=[...],
    seed=seed,            # standard parameter, effective
    temperature=temperature,
    extra_body={"response_modalities": ["IMAGE"]},
)
```

**Alternative considered:** `images.generate()` path + `extra_body seed` → confirmed ineffective by testing, rejected.

**Extended investigation (2026-05-06) — gpt-image-2 compatibility:**

Testing confirmed that `gpt-image-2` cannot use the `chat.completions` path (Azure backend returns 400 "unsupported operation"). It only works via `images.generate()`. However, `seed` via `extra_body` is also rejected by the Azure backend for `gpt-image-2` (400 "Unknown parameter: 'seed'"). This is consistent with the OpenAI API specification: `images.generate()` has never had a `seed` parameter for any model.

Additionally, a known LiteLLM bug ([#24621](https://github.com/BerriAI/litellm/issues/24621)) causes `extra_body` to be stripped in the `images.generate()` path before the request reaches the Gemini backend, confirming that seed cannot reach Gemini via that route either.

**Conclusion:** `seed` is only achievable via `chat.completions` with Gemini models. OpenAI image models (`gpt-image-2`, `gpt-image-1`, `dall-e-*`) are out of scope for this change — they require `images.generate()` (no seed support) and a separate code path that is not needed by current users.

### D2: IMAGE_GEN_BASE_URL must include /v1 suffix

The OpenAI library does not add `/v1` automatically. LiteLLM's OpenAI-compatible routes are under `/v1/`. The URL is used as-is; documentation requires the `/v1` suffix.

### D3: Extract image from message.images with defensive fallback

LiteLLM places the image in the non-standard `message.images` field (accessible via `model_dump()`). A fallback to the `content` list is added in case LiteLLM changes this behavior in a future version.

```python
raw = msg.model_dump()
images = raw.get("images") or []
# fallback: check content list
```

### D4: Remove detect_api_type() and generate_slide_imagen()

The Imagen path relies on `client.models.generate_images()` (genai-specific). After switching libraries it cannot be supported. Remove entirely per requirements; no emulation.

### D5: Change script dependencies to ["openai", "pillow"]

Direct replacement in the uv inline script header. No other changes needed.

## Risks / Trade-offs

- **message.images is a LiteLLM non-standard field** → A LiteLLM upgrade could change the response structure. The content list fallback reduces risk, but if both paths fail, manual debugging is required.

- **Breaking change: env var rename** → Existing users must update `.env` and shell config. README and SKILL.md must provide a clear migration table.

- **Imagen removal** → Any user relying on Imagen models (model name containing "imagen") will break. No known production use cases.

- **OpenAI image models not supported** → `gpt-image-2`, `gpt-image-1`, and `dall-e-*` require `images.generate()` and do not support `seed`. These models are explicitly out of scope. If future users request them, a separate code path with model detection would be needed, accepting the loss of seed reproducibility for those models.

## Migration Plan

1. Rewrite `generate_images.py` (library, env vars, API calls)
2. Update `SKILL.md` (env var references, troubleshooting)
3. Update `guide.md` and `batch-generation.md` (heredoc examples)
4. Update `README.md` (env var documentation)
5. Bump version in `plugin.json`, `SKILL.md`, root `README.md`

Rollback: `git revert` (no database migration, code only).

## Open Questions

None. All technical questions were resolved by testing before this design was written.
