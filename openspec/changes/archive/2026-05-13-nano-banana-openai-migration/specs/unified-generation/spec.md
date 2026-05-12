## MODIFIED Requirements

### Requirement: Single Workflow for All Image Counts
The system SHALL use the same fixed Python script (`generate_images.py`) for all image generation tasks, regardless of the number of images (1-100).

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

---

## ADDED Requirements

### Requirement: OpenAI Library Dependency
The system SHALL declare `openai` (not `google-genai`) as the image generation dependency in the script header.

#### Scenario: Script header specifies openai
- **WHEN** `generate_images.py` is inspected
- **THEN** the `# dependencies` line in the uv inline script header contains `"openai"` and `"pillow"`
- **AND** does NOT contain `"google-genai"`

#### Scenario: uv resolves openai at runtime
- **WHEN** `uv run generate_images.py --config <path>` is executed
- **THEN** `uv` installs `openai` and `pillow` if not cached
- **AND** the script runs without any manual `pip install`

---

## REMOVED Requirements

### Requirement: Imagen API Path
**Reason**: The Imagen API (`client.models.generate_images()`) is a `google-genai`-specific method with no OpenAI-compatible equivalent. After switching to the `openai` library, all generation goes through `chat.completions`.
**Migration**: Use `IMAGE_GEN_MODEL` with a Gemini image model (e.g., `gemini-3-pro-image`). Model names containing "imagen" are no longer supported.

### Requirement: API Type Detection
**Reason**: `detect_api_type()` existed to route between Gemini and Imagen paths. With a single `chat.completions` path, routing is no longer needed.
**Migration**: No action required. All models use the same API path.
