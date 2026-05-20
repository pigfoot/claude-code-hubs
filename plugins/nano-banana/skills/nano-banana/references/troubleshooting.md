# Troubleshooting

## Most common errors

| Error | Quick Fix |
|-------|-----------|
| `RDSEC_API_KEY not set` | `export RDSEC_API_KEY=<your-token>` |
| `IMAGE_GEN_BASE_URL not set` | `export IMAGE_GEN_BASE_URL="https://api.rdsec.trendmicro.com/prod/aiendpoint/v1"` |
| `Model not found` | Check exact model name in `IMAGE_GEN_MODEL` |
| `ModuleNotFoundError` | Verify `# dependencies = ["openai", "pillow"]` in script header |
| No image generated | Check that endpoint returns data in `message.images` field |
| `401 Unauthorized` | Verify `RDSEC_API_KEY` is a valid JWT token with endpoint permissions |

## Debug steps

1. Verify API key: `echo $RDSEC_API_KEY`
2. Verify endpoint URL: `echo $IMAGE_GEN_BASE_URL` (must end with `/v1`)
3. Test with simple prompt: `"A red circle"`
4. Review API routing rules in SKILL.md if API errors occur

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Using `types.ImageGenerationConfig` | Does NOT exist — use `GenerateContentConfig` or `GenerateImagesConfig` |
| Using `generate_images()` with Gemini | Use `generate_content()` for Gemini models |
| Using `generate_content()` with Imagen | Use `generate_images()` for Imagen models |
| Overriding `IMAGE_GEN_MODEL` when set | Use model EXACTLY as-is — don't add suffixes |
| Using `google-genai` library | Use `openai` library with OpenAI-compatible endpoint |
| Using text models for image gen | Use image models only (e.g., `gemini-3-pro-image`) |
| Saving to flat files | Use `NNN-short-name/` directories |
| Using PIL to draw/edit | Use Gemini/Imagen API with image in `contents` |

## Script execution failures

### 1. "Logo file is Git LFS pointer" or "cannot identify image file"

Most common issue: user doesn't have Git LFS installed.

```bash
# Install Git LFS (once per machine)
git lfs install

# Pull actual files (in the plugin directory)
git lfs pull
```

Git LFS install: <https://git-lfs.com/>. Re-run the image generation command after install.

### 2. "command not found: uv"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install docs: <https://docs.astral.sh/uv/>

### 3. Python version issues

The script requires Python 3.11–3.13. Python 3.14 breaks pydantic-core (an openai dependency).

- The `--managed-python` flag lets uv auto-download a compatible version
- If download fails: `uv python install 3.13`
- Check: internet connection and disk space

### 4. Permission denied or download errors

- Check write permissions in uv cache directory (usually `~/.local/share/uv/`)
- Verify firewall/proxy settings allow uv to download Python

### 5. Missing dependencies (openai, pillow)

- Dependencies are auto-installed by `uv run` via PEP 723 metadata
- If user bypasses uv and runs script with python directly, ImportError appears
- Always use `uv run --managed-python ${CLAUDE_SKILL_DIR}/scripts/generate_images.py`

## RONE endpoint limitations

| Feature | Status | Notes |
|---------|--------|-------|
| `gpt-image-2` text-to-image (`/images/generations`) | ✅ Working | Use `quality: "low"` to avoid timeout |
| `gpt-image-2` image editing (`/images/edits`) | ✅ Working | Multipart form data + `quality: "low"` (~37–152s) |
| Gemini image generation (`chat.completions`) | ✅ Working | Primary workflow for this skill |
| Gemini image editing (`/images/edits`) | ❌ Not working | LiteLLM Vertex AI credential issue; use `chat.completions` with `image_url` parts |

### gpt-image-2 `/images/edits` — correct usage

Send as multipart form data (do NOT set `Content-Type` manually):

```python
files = {"image": ("image.png", img_bytes, "image/png")}
data = {
    "model": "gpt-image-2",
    "prompt": "edit instruction",
    "n": "1",
    "size": "1024x1024",
    "quality": "low",
}
resp = requests.post(f"{BASE_URL}/images/edits",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files=files, data=data, timeout=300)
# Response: resp.json()["data"][0]["b64_json"]
```

### Timeout reference (May 8 probe sweep)

| Endpoint | `quality` | Time | Use? |
|----------|-----------|------|------|
| `/images/generations` | `low` | ~72s | ✅ |
| `/images/generations` | `medium` | ~110s | ⚠️ slow |
| `/images/generations` | `auto` / omitted | timeout | ❌ |
| `/images/generations` | `high` | timeout | ❌ |
| `/images/edits` | `low` | ~37–152s | ✅ |
| `/images/edits` | omitted / `auto` / `high` | timeout / 400 | ❌ |
| `/images/edits` | `standard` / `hd` | 400 | ❌ |

**Rule:** All gpt-image-2 calls use `quality="low"` — the script enforces this automatically.
