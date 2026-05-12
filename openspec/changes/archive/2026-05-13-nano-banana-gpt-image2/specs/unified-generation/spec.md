## ADDED Requirements

### Requirement: Slide config supports optional reference_image field

The JSON slide config SHALL accept an optional `reference_image` field containing a relative path
to a source image for model-supported editing workflows.

**ID:** `unified-generation-007`
**Priority:** High

#### Scenario: Config with reference_image is valid

- **WHEN** slide config contains `"reference_image": "./source.png"`
- **THEN** `load_config()` accepts it without error
- **AND** the path is passed to `generate_slide()` for model dispatch

#### Scenario: Config without reference_image is unchanged

- **WHEN** slide config has no `reference_image` field
- **THEN** behavior is identical to current (no breaking change)

---

### Requirement: Model-based routing in generate_slide

`generate_images.py` SHALL dispatch API calls based on the model name:

- `gpt-image-2` without `reference_image` → `client.images.generate()`
- `gpt-image-2` with `reference_image` → `client.images.edit()`
- Any other model → existing `client.chat.completions.create()` path (unchanged)

**ID:** `unified-generation-008`
**Priority:** High

#### Scenario: Gemini model unchanged

- **WHEN** `IMAGE_GEN_MODEL=gemini-3-pro-image`
- **THEN** script uses `client.chat.completions.create()` exactly as before
- **AND** no new code paths are entered

#### Scenario: Mixed-model batch routes each slide correctly

- **WHEN** batch config has Gemini slides and gpt-image-2 slides
- **THEN** each slide is dispatched to its correct API path independently
- **AND** results are collected in the same output format regardless of model

## MODIFIED Requirements

### Requirement: JSON Config Pattern

All image generation SHALL use JSON configuration files with minimal required fields.

**ID:** `unified-generation-004`
**Priority:** High

**Updated:** Config schema gains optional `reference_image` per slide for gpt-image-2 editing.

#### Scenario: Claude creates minimal config

- **WHEN** user requests images with basic requirements
- **THEN** config contains only `slides` and `output_dir`
- **AND** no optional fields unless needed

#### Scenario: Claude creates config with reference image for editing

- **WHEN** user requests gpt-image-2 image editing
- **THEN** config includes `reference_image` on the relevant slide

Updated example:

```json
{
  "slides": [
    {"number": 1, "prompt": "Add a blue border to this image", "reference_image": "./source.png"},
    {"number": 2, "prompt": "A futuristic cityscape", "style": "professional"}
  ],
  "output_dir": "./001-edits/"
}
```
