# unified-generation Specification

## Purpose

TBD - created by archiving change eliminate-heredoc-hallucinations. Update Purpose after archive.

## Requirements

### Requirement: Single Workflow for All Image Counts

The system SHALL use the same fixed Python script (`generate_images.py`) for all image generation tasks, regardless of
the number of images (1-100).

**ID:** `unified-generation-001`
**Priority:** High

#### Scenario: Single image generation

- **WHEN** user requests 1 image
- **THEN** Claude creates JSON config with 1 slide
- **AND** calls `uv run generate_images.py --config <path>`
- **AND** generation uses the OpenAI-compatible client (`openai` library), not `google-genai`

#### Scenario: Small batch (3 images)

- **WHEN** user requests 3 images
- **THEN** Claude creates JSON config with 3 slides
- **AND** calls `uv run generate_images.py --config <path>`
- **AND** the same script is used as for single or large batch

#### Scenario: Large batch (50 images)

- **WHEN** user requests 50 images
- **THEN** Claude creates JSON config with 50 slides
- **AND** calls `uv run generate_images.py --config <path>`
- **AND** script behavior scales naturally with no mode switching

**Rationale:** Eliminates complexity of mode switching and ensures consistent, hallucination-free behavior across all
use cases.

---

### Requirement: OpenAI Library Dependency

The system SHALL declare `openai` (not `google-genai`) as the image generation dependency in the script header.

**ID:** `unified-generation-009`
**Priority:** High

#### Scenario: Script header specifies openai

- **WHEN** `generate_images.py` is inspected
- **THEN** the `# dependencies` line in the uv inline script header contains `"openai"` and `"pillow"`
- **AND** does NOT contain `"google-genai"`

#### Scenario: uv resolves openai at runtime

- **WHEN** `uv run generate_images.py --config <path>` is executed
- **THEN** `uv` installs `openai` and `pillow` if not cached
- **AND** the script runs without any manual `pip install`

---

### Requirement: Fixed Script Name

The image generation script SHALL be named `generate_images.py` to reflect its unified purpose.

**ID:** `unified-generation-002`
**Priority:** Medium

#### Scenario: Script naming convention

**Given:** Script handles all image generation tasks
**When:** User or documentation references the script
**Then:**

- Script is named `generate_images.py`
- Name reflects general-purpose usage
- Not limited to "batch" semantics

**Rationale:** Semantic clarity - "images" (general) vs "batch" (implies threshold).

---

### Requirement: No Heredoc Code Generation

Claude SHALL NOT generate Python code via heredocs for image generation tasks.

**ID:** `unified-generation-003`
**Priority:** Critical

#### Scenario: Claude avoids heredoc generation

**Given:** User requests any number of images
**When:** Claude prepares generation workflow
**Then:**

- Claude creates JSON config data only
- No Python code generation
- No `uv run - << 'EOF'` patterns
- No inline API calls in heredocs

#### Scenario: Existing heredoc patterns removed

**Given:** Documentation contains heredoc examples
**When:** Documentation is updated
**Then:**

- All heredoc examples are removed
- Only config-based examples remain
- No code generation patterns documented

**Rationale:** Heredoc generation has 30-40% hallucination rate; JSON config has ~0% hallucination rate.

---

### Requirement: JSON Config Pattern

All image generation SHALL use JSON configuration files with minimal required fields.

**ID:** `unified-generation-004`
**Priority:** High

#### Scenario: Claude creates minimal config

**Given:** User requests images with basic requirements
**When:** Claude creates config file
**Then:**

- Config contains only `slides` and `output_dir`
- No optional fields included unless needed
- JSON is valid and minimal

Example:

```json
{
  "slides": [
    {"number": 1, "prompt": "AI safety slide", "style": "trendlife"}
  ],
  "output_dir": "./001-slides/"
}
```

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

#### Scenario: Claude uses cross-platform temp path

**Given:** Claude needs to create config file
**When:** Determining config file path
**Then:**

- Uses `Path(tempfile.gettempdir())` for path
- Path works on Windows/Linux/macOS
- No hardcoded `/tmp/` paths

Example (Python):

```python
config_path = Path(tempfile.gettempdir()) / "nano-banana-config.json"
```

**Rationale:** Minimal config reduces what Claude needs to generate, lowering hallucination risk. Cross-platform paths
avoid Windows errors.

---

### Requirement: Consistent Execution Pattern

Image generation SHALL always follow the same execution pattern: config creation → script execution → progress
monitoring → result collection.

**ID:** `unified-generation-005`
**Priority:** Medium

#### Scenario: Execution workflow consistency

**Given:** Any image generation request (1-100 images)
**When:** Claude executes the workflow
**Then:**

- Step 1: Create JSON config file
- Step 2: Execute `uv run generate_images.py --config <path>`
- Step 3: Monitor progress file (if background)
- Step 4: Read results file when complete
- Same steps regardless of image count

**Rationale:** Consistent workflow is easier to understand, debug, and maintain.

---

### Requirement: Zero AI Hallucination Target

The unified generation workflow SHALL achieve zero AI-caused hallucinations in image generation.

**ID:** `unified-generation-006`
**Priority:** Critical

#### Scenario: No API parameter hallucinations

**Given:** Claude generates config for image generation
**When:** Config is executed by fixed script
**Then:**

- No non-existent API parameters (e.g., `api_version`)
- No incorrect model names
- No mixed API patterns
- Script handles all API details correctly

#### Scenario: Success rate measurement

**Given:** 100 image generation requests
**When:** Using unified generation workflow
**Then:**

- 0 failures due to AI hallucinations
- Any failures are user error (invalid config) or system error (API down)
- Success rate for AI-generated parts: 100%

**Rationale:** This is the primary goal - eliminate the 30-40% hallucination rate of heredoc approach.

---

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
