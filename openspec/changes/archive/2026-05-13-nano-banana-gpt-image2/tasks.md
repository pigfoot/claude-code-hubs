## 1. generate_images.py — Model Routing

- [x] 1.1 Add `reference_image` field handling in `load_config()` — validate it exists if specified, reject absolute paths
- [x] 1.2 Update `generate_slide()` signature to accept `reference_image: Optional[str]`
- [x] 1.3 Add model-based routing: if `model == "gpt-image-2"` dispatch to new path, else keep existing `chat.completions` path
- [x] 1.4 Wire `reference_image` from slide config through to `generate_slide()` in `main()`

## 2. generate_images.py — gpt-image-2 Text-to-Image

- [x] 2.1 Implement `_generate_gpt_image2()` — calls `client.images.generate()` with `quality="low"`, `size="1024x1024"`
- [x] 2.2 Extract image bytes from `response.data[0].b64_json`
- [x] 2.3 Emit warning and skip `seed`/`temperature` params when model is gpt-image-2
- [x] 2.4 Omit `seed` from results JSON for gpt-image-2 slides

## 3. generate_images.py — gpt-image-2 Image Editing

- [x] 3.1 Implement `_edit_gpt_image2()` — reads reference image bytes, calls `client.images.edit()` multipart with `quality="low"`, `size="1024x1024"`
- [x] 3.2 Resolve `reference_image` path relative to cwd; return clear error if not found
- [x] 3.3 Extract image bytes from `response.data[0].b64_json`
- [x] 3.4 Emit warning and skip `seed`/`temperature` for edit slides

## 4. Testing

- [x] 4.1 Test gpt-image-2 text-to-image via `/images/generations` with `quality=low` — confirm 200 + `b64_json`
- [x] 4.2 Test gpt-image-2 image editing via `/images/edits` with a real reference image — confirm 200 + `b64_json`
- [x] 4.3 Test mixed-model batch (Gemini slide + gpt-image-2 slide) — both succeed, routed correctly
- [x] 4.4 Test missing `reference_image` file — confirm slide fails with clear error, batch continues
- [x] 4.5 Test Gemini model unchanged — confirm existing `chat.completions` path not affected

## 5. SKILL.md Updates

- [x] 5.1 Update capability matrix table (gpt-image-2 `/images/generations` ✅, `/images/edits` ✅)
- [x] 5.2 Add `reference_image` field to config examples in SKILL.md
- [x] 5.3 Add gpt-image-2 timeout guidance (always use `quality=low`; `/images/generations` ~72s, `/images/edits` ~37s)
- [x] 5.4 Document that `seed` and `temperature` are not supported for gpt-image-2 slides
- [x] 5.5 Bump plugin version (SKILL.md metadata, plugin.json, README.md, root README.md)
