# gpt-image2-generation Specification

## Purpose

TBD - created by syncing change nano-banana-gpt-image2. Update Purpose after archive.

## Requirements

### Requirement: gpt-image-2 text-to-image via images/generations

When `IMAGE_GEN_MODEL=gpt-image-2` and no `reference_image` is specified in a slide,
`generate_images.py` SHALL call `client.images.generate()` (OpenAI `/images/generations` endpoint)
instead of `chat.completions`.

**ID:** `gpt-image2-generation-001`
**Priority:** High

#### Scenario: Text-to-image with gpt-image-2 succeeds

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2` and slide has no `reference_image`
- **THEN** script calls `client.images.generate(model="gpt-image-2", prompt=..., quality="low", size="1024x1024")`
- **AND** response image is extracted from `response.data[0].b64_json`
- **AND** image is saved to `output_dir/slide-NN.<format>`

#### Scenario: gpt-image-2 does not use chat.completions

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2`
- **THEN** script SHALL NOT call `client.chat.completions.create()` for that slide
- **AND** `extra_body={"response_modalities": ["IMAGE"]}` is NOT sent

---

### Requirement: gpt-image-2 generation quality is hardcoded to low

`generate_images.py` SHALL always pass `quality="low"` to `client.images.generate()` for gpt-image-2,
regardless of any config `quality` field (which controls output file compression, not API quality).

**ID:** `gpt-image2-generation-002`
**Priority:** High

#### Scenario: API quality is always low for gpt-image-2 generations

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2` and slide config has `"quality": 90` (file compression)
- **THEN** API call uses `quality="low"` (API param)
- **AND** output file is saved with compression quality 90 (config param, unchanged)

---

### Requirement: gpt-image-2 generation does not support seed or temperature

`generate_images.py` SHALL NOT pass `seed` or `temperature` to `client.images.generate()`.
If a slide config specifies `seed` or `temperature` and the model is gpt-image-2,
the script SHALL emit a warning and continue without those parameters.

**ID:** `gpt-image2-generation-003`
**Priority:** Medium

#### Scenario: Seed ignored for gpt-image-2 slides

- **WHEN** slide config has `"seed": 42` and `IMAGE_GEN_MODEL=gpt-image-2`
- **THEN** API call does NOT include `seed`
- **AND** script prints a warning: `Warning: seed is not supported for gpt-image-2, ignoring`
- **AND** results JSON omits `seed` for that slide

#### Scenario: Temperature ignored for gpt-image-2 slides

- **WHEN** slide config has `"temperature": 0.8` and `IMAGE_GEN_MODEL=gpt-image-2`
- **THEN** API call does NOT include `temperature`
- **AND** script prints a warning: `Warning: temperature is not supported for gpt-image-2, ignoring`

---

### Requirement: gpt-image-2 generation size defaults to 1024x1024

`generate_images.py` SHALL use `size="1024x1024"` for gpt-image-2 `/images/generations` calls.

**ID:** `gpt-image2-generation-004`
**Priority:** Low

#### Scenario: Default size used for gpt-image-2 generation

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2` and no size override exists
- **THEN** API call uses `size="1024x1024"`
