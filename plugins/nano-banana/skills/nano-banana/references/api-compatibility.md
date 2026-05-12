# API Compatibility Matrix

RONE endpoint capability reference for nano-banana image generation.
Last verified: 2026-05-13.

## Model × Feature Matrix

| Feature | gemini-3-pro-image<br>`chat.completions` | gpt-image-2<br>`/images/generations` | gpt-image-2<br>`/images/edits` |
|---------|:---:|:---:|:---:|
| Text-to-image | ✅ | ✅ | ❌ |
| Image generation with reference | ✅ | ❌ | ✅ |
| Image editing | ✅ | ❌ | ✅ |
| Inpainting (mask) | ❓ untested | ❌ | ✅ (API supports) |
| Seed control | ✅ | ❌ | ❌ |
| Temperature | ✅ | ❌ | ❌ |
| Script support | ✅ | ✅ | ✅ |

> `gemini-3.1-flash-image` behaves identically to `gemini-3-pro-image` (both use `chat.completions`).

## gpt-image-2 Timeout Reference

From May 8 probe sweep (Michael Fu, UX-AS):

| API | Quality | Time | Recommendation |
|-----|---------|------|----------------|
| `/images/generations` | `low` | ~72s | ✅ use |
| `/images/generations` | `medium` | ~110s | ⚠️ slow |
| `/images/generations` | `auto` / omitted | timeout | ❌ |
| `/images/generations` | `high` | timeout | ❌ |
| `/images/edits` | `low` | ~37–152s | ✅ use |
| `/images/edits` | omitted / auto / high | timeout / 400 | ❌ |
| `/images/edits` | `standard` / `hd` | 400 | ❌ |

**Rule:** Always use `quality="low"` for all gpt-image-2 calls.

## API Path Decision Tree

```
IMAGE_GEN_MODEL == "gpt-image-2"?
├── Yes
│   ├── style=="trendlife" AND layout=="featured"?
│   │   └── Yes → POST /images/edits (logo as image param, quality=low)
│   ├── slide has reference_image?
│   │   ├── Yes → POST /images/edits (multipart, quality=low)
│   │   └── No  → POST /images/generations (JSON, quality=low)
│   └── seed / temperature → ignored (warn once per job)
└── No (Gemini or other)
    └── chat.completions + response_modalities=["IMAGE"]
```

## gpt-image-2 Known Constraints

- **`chat.completions` unsupported** — returns 400 "operation is unsupported"
  (RONE proxy routes gpt-image-2 via Azure OpenAI Images API, not LiteLLM chat path)
- **`/images/edits` requires `image` parameter** — cannot be used for text-to-image; `image` is mandatory
- **Seed not supported** — `/images/generations` and `/images/edits` do not accept `seed`
- **Temperature not supported** — same as above
- **Transparent background not supported** — `background: "transparent"` is rejected
- **`input_fidelity` not configurable** — gpt-image-2 always processes input at high fidelity; omit this parameter
- **Size** — use verified GPT pixel sizes only: `1024x1024`, `1024x1536`, `1536x1024`, `1024x1792`, `1792x1024`, `2048x2048`

## Gemini via chat.completions

- Response image in `choices[0].message.images[].image_url.url` (LiteLLM non-standard field)
- Fallback: `choices[0].message.content[]` image_url parts
- Reference image: pass as `image_url` content part with `data:image/png;base64,...`

## References

- [RDSec_One_Support thread — gpt-image-2 follow-up (2026-05-12)](https://teams.microsoft.com/l/message/19:30f59149137649be85abbba50c7f4617@thread.tacv2/1778557586181?tenantId=3e04753a-ae5b-42d4-a86d-d6f05460f9e4&groupId=3e59784e-87f1-45d9-9393-0472c3c885a7&parentMessageId=1778557586181&teamName=RDSec-Service-Public&channelName=RDSec_One_Support&createdTime=1778557586181)
  - Ryan Duff (SE-NA): confirmed `/images/edits` fixed; FlyBot code samples for both paths
  - Michael Fu (UX-AS): timeout probe data; implementation notes for multipart edits
  - Teddy Peng (RD-AS): Gemini `/images/edits` still broken (LiteLLM Vertex AI credential issue)
- [Image generation guide — OpenAI API](https://developers.openai.com/api/docs/guides/image-generation)
  - Confirms `/images/edits` requires `image` parameter — text-to-image ❌ is correct
  - Clear separation between `/images/generations` (text-to-image) and `/images/edits` (image editing)
- [Create image edit — OpenAI API Reference](https://developers.openai.com/api/docs/reference/images/createEdit)
  - gpt-image-2 supports `quality` parameter; `input_fidelity` cannot be set (always high fidelity)
  - Transparent background not supported
- [EDIT endpoint refusing gpt-image models — OpenAI Community](https://community.openai.com/t/edit-endpoint-images-edits-refusing-gpt-image-models/1375581)
  - Model validation errors reported on public OpenAI API;
    RONE (Azure) endpoint behaves differently — confirmed working in testing
- [GPT Image 2 API Guide — WaveSpeed Blog](https://wavespeed.ai/blog/posts/gpt-image-2-api-guide/)
  - Third-party wrapper documentation; endpoint mapping matches official API
