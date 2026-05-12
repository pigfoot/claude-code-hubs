## 1. Rewrite generate_images.py

- [x] 1.1 Update script header dependencies from `["google-genai", "pillow"]` to `["openai", "pillow"]`
- [x] 1.2 Remove all `from google import genai` and `from google.genai import types` imports
- [x] 1.3 Add `from openai import OpenAI` import
- [x] 1.4 Update env var reads: `NANO_BANANA_MODEL` → `IMAGE_GEN_MODEL`, `GEMINI_API_KEY`/`GOOGLE_API_KEY` → `RDSEC_API_KEY`, `GOOGLE_GEMINI_BASE_URL` → `IMAGE_GEN_BASE_URL`
- [x] 1.5 Update client initialization: `genai.Client(...)` → `OpenAI(api_key=..., base_url=...)`, exit with error if `RDSEC_API_KEY` or `IMAGE_GEN_BASE_URL` is missing
- [x] 1.6 Remove `detect_api_type()` function
- [x] 1.7 Remove `generate_slide_imagen()` function
- [x] 1.8 Rewrite `generate_slide_gemini()` → rename to `generate_slide()`, use `chat.completions.create(seed=seed, temperature=temperature, extra_body={"response_modalities": ["IMAGE"]})`
- [x] 1.9 Update reference image logic: TrendLife featured slides send logo via `image_url` (base64 data URI) in the messages list
- [x] 1.10 Update image extraction: read from `message.model_dump()["images"][0]["image_url"]["url"]`, add fallback to content list
- [x] 1.11 Update `main()` to remove Imagen branch and use the new single client
- [x] 1.12 Update docstring env var references (`NANO_BANANA_MODEL` → `IMAGE_GEN_MODEL`)

## 2. Update SKILL.md

- [x] 2.1 Replace all `NANO_BANANA_MODEL` references with `IMAGE_GEN_MODEL`
- [x] 2.2 Replace all `GEMINI_API_KEY` references with `RDSEC_API_KEY`
- [x] 2.3 Replace all `GOOGLE_GEMINI_BASE_URL` references with `IMAGE_GEN_BASE_URL` (note `/v1` suffix requirement)
- [x] 2.4 Update `primaryEnv` field if present
- [x] 2.5 Update troubleshooting section for env var error messages
- [x] 2.6 Replace `google-genai` troubleshooting with `openai` equivalents
- [x] 2.7 Bump SKILL.md metadata version

## 3. Update references/guide.md

- [x] 3.1 Update all heredoc examples: `from google import genai` → `from openai import OpenAI`
- [x] 3.2 Replace all `GOOGLE_GEMINI_BASE_URL` with `IMAGE_GEN_BASE_URL`
- [x] 3.3 Replace all `NANO_BANANA_MODEL` with `IMAGE_GEN_MODEL`
- [x] 3.4 Update dependencies comments from `["google-genai", "pillow"]` to `["openai", "pillow"]`

## 4. Update references/batch-generation.md

- [x] 4.1 Replace all `NANO_BANANA_MODEL` with `IMAGE_GEN_MODEL`
- [x] 4.2 Replace all `GEMINI_API_KEY` with `RDSEC_API_KEY`
- [x] 4.3 Replace all `GOOGLE_GEMINI_BASE_URL` with `IMAGE_GEN_BASE_URL`
- [x] 4.4 Update example code: `genai.Client` → `OpenAI`
- [x] 4.5 Update example code dependencies line

## 5. Update plugin README.md

- [x] 5.1 Update Quick Start / Setup section with new env var names
- [x] 5.2 Add migration table (old → new env var mapping)
- [x] 5.3 Add Recent Improvements section

## 6. Bump version numbers

- [x] 6.1 Update `plugins/nano-banana/.claude-plugin/plugin.json` version
- [x] 6.2 Update `plugins/nano-banana/skills/nano-banana/SKILL.md` metadata version
- [x] 6.3 Update root `README.md` Available Plugins version column

## 7. Remove test scripts

- [x] 7.1 Remove `scripts/test_openai_compat.py`
- [x] 7.2 Remove `scripts/test_seed_effect.py`
- [x] 7.3 Remove `scripts/test_seed_chat.py`
