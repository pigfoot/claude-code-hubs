# gpt-image2-editing Specification

## Purpose

TBD - created by syncing change nano-banana-gpt-image2. Update Purpose after archive.

## Requirements

### Requirement: gpt-image-2 image editing via images/edits

When `IMAGE_GEN_MODEL=gpt-image-2` and a slide specifies `reference_image`,
`generate_images.py` SHALL call `client.images.edit()` (OpenAI `/images/edits` endpoint)
using multipart form data.

**ID:** `gpt-image2-editing-001`
**Priority:** High

#### Scenario: Image editing with reference image succeeds

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2` and slide has `"reference_image": "./source.png"`
- **THEN** script reads the reference image file as bytes
- **AND** calls `client.images.edit(model="gpt-image-2", image=<bytes>, prompt=..., quality="low", size="1024x1024")`
- **AND** response image is extracted from `response.data[0].b64_json`
- **AND** image is saved to `output_dir/slide-NN.<format>`

#### Scenario: Missing reference image file is an error

- **WHEN** slide specifies `"reference_image": "./missing.png"` but file does not exist
- **THEN** script marks that slide as failed
- **AND** error message includes: `reference_image not found: ./missing.png`
- **AND** batch continues with remaining slides

---

### Requirement: reference_image path resolves relative to working directory

`reference_image` paths SHALL be resolved relative to the process working directory
(same convention as `output_dir`), NOT relative to the config file location.

**ID:** `gpt-image2-editing-002`
**Priority:** High

#### Scenario: Relative reference_image resolves from cwd

- **WHEN** slide has `"reference_image": "./assets/photo.png"` and cwd is `/home/user/project`
- **THEN** script reads `/home/user/project/assets/photo.png`

#### Scenario: Absolute reference_image path is rejected

- **WHEN** slide has `"reference_image": "/absolute/path/photo.png"`
- **THEN** script marks that slide as failed
- **AND** error message: `reference_image must be a relative path`

---

### Requirement: gpt-image-2 editing quality is hardcoded to low

`generate_images.py` SHALL always pass `quality="low"` to `client.images.edit()` for gpt-image-2.

**ID:** `gpt-image2-editing-003`
**Priority:** High

#### Scenario: API quality is always low for gpt-image-2 edits

- **WHEN** `IMAGE_GEN_MODEL=gpt-image-2` with a `reference_image`
- **THEN** API call uses `quality="low"`
- **AND** this is independent of the config `quality` field (file compression)

---

### Requirement: gpt-image-2 editing does not support seed or temperature

`generate_images.py` SHALL NOT pass `seed` or `temperature` to `client.images.edit()`.

**ID:** `gpt-image2-editing-004`
**Priority:** Medium

#### Scenario: Seed and temperature ignored for gpt-image-2 edit slides

- **WHEN** slide config specifies `seed` or `temperature` with a `reference_image` and `IMAGE_GEN_MODEL=gpt-image-2`
- **THEN** API call does NOT include those parameters
- **AND** script prints a warning for each ignored parameter
