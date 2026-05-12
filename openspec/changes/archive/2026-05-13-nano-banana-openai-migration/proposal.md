## Why

nano-banana currently uses the `google-genai` library to call the Gemini native API, but the backend LiteLLM proxy also exposes an OpenAI-compatible route (`/v1/`). Testing confirmed that `seed` works correctly through the `chat.completions` standard parameter on this route, while `extra_body` seed on `images.generate` is silently dropped. Switching to the `openai` library unifies the protocol, removes the Google-specific SDK dependency, and makes `seed` actually effective.

## What Changes

- **BREAKING** Rename environment variables: `NANO_BANANA_MODEL` → `IMAGE_GEN_MODEL`, `GOOGLE_GEMINI_BASE_URL` → `IMAGE_GEN_BASE_URL` (must include `/v1` suffix), `GEMINI_API_KEY` / `GOOGLE_API_KEY` → `RDSEC_API_KEY`
- Remove `google-genai` dependency, add `openai` library
- Remove Imagen API path (`generate_slide_imagen()`) and `detect_api_type()` logic
- All image generation switched to `client.chat.completions.create()` with `extra_body={"response_modalities": ["IMAGE"]}`
- `seed` and `temperature` become standard `chat.completions` parameters (previously genai config kwargs)
- Reference image (TrendLife featured slide) switched to `image_url` in messages
- Image bytes extracted from `message.images[0].image_url.url` (LiteLLM non-standard field)
- Update all documentation (SKILL.md, guide.md, batch-generation.md, README.md) for new env var names and code examples

## Capabilities

### New Capabilities
- `openai-compat-client`: Image generation using the `openai` library via an OpenAI-compatible endpoint, covering client initialization, `chat.completions` calls, and image extraction from `message.images`

### Modified Capabilities
- `batch-generation`: Env var names change (NANO_BANANA_MODEL → IMAGE_GEN_MODEL, GEMINI_API_KEY → RDSEC_API_KEY) — spec-level behavior change
- `unified-generation`: Imagen path removed, API client switched from `google-genai` to `openai` — spec-level behavior change

## Impact

- `plugins/nano-banana/skills/nano-banana/scripts/generate_images.py` — major rewrite
- `plugins/nano-banana/skills/nano-banana/SKILL.md` — env vars, code examples, troubleshooting
- `plugins/nano-banana/skills/nano-banana/references/guide.md` — all heredoc examples
- `plugins/nano-banana/skills/nano-banana/references/batch-generation.md` — env vars and examples
- `plugins/nano-banana/README.md` — env var documentation
- Dependencies: `google-genai` removed, `openai` added (script header)
- Users must update env var names in `.env` or shell configuration
