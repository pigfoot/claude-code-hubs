## ADDED Requirements

### Requirement: OpenAI-Compatible Client Initialization
The system SHALL initialize an OpenAI client using `IMAGE_GEN_BASE_URL` and `RDSEC_API_KEY`, and SHALL use this client for all image generation.

#### Scenario: Client initialized with required env vars
- **WHEN** `IMAGE_GEN_BASE_URL` and `RDSEC_API_KEY` are set
- **THEN** `openai.OpenAI(api_key=RDSEC_API_KEY, base_url=IMAGE_GEN_BASE_URL)` is created successfully
- **AND** all subsequent API calls use this client

#### Scenario: Missing RDSEC_API_KEY
- **WHEN** `RDSEC_API_KEY` is not set
- **THEN** the script exits with error: "RDSEC_API_KEY environment variable not set"

#### Scenario: Missing IMAGE_GEN_BASE_URL
- **WHEN** `IMAGE_GEN_BASE_URL` is not set
- **THEN** the script exits with error: "IMAGE_GEN_BASE_URL environment variable not set"

---

### Requirement: Image Generation via chat.completions
The system SHALL use `client.chat.completions.create()` with `extra_body={"response_modalities": ["IMAGE"]}` for all image generation, including both standard slides and reference-image slides.

#### Scenario: Standard slide generation
- **WHEN** a slide with no reference image is generated
- **THEN** `chat.completions.create()` is called with `messages=[{"role": "user", "content": prompt}]`
- **AND** `extra_body={"response_modalities": ["IMAGE"]}` is included

#### Scenario: Reference image slide generation (TrendLife featured)
- **WHEN** a TrendLife featured slide requires a logo reference image
- **THEN** `chat.completions.create()` is called with a multi-part message containing the logo image as `image_url` with base64 data URI, followed by the text prompt
- **AND** `extra_body={"response_modalities": ["IMAGE"]}` is included

---

### Requirement: Seed and Temperature as Standard Parameters
The system SHALL pass `seed` and `temperature` as top-level parameters to `chat.completions.create()`, not via `extra_body`.

#### Scenario: Seed passed as standard parameter
- **WHEN** a slide specifies `seed=42`
- **THEN** `chat.completions.create(seed=42, ...)` is called
- **AND** repeated calls with the same seed and prompt produce identical images

#### Scenario: Temperature passed as standard parameter
- **WHEN** a slide specifies `temperature=0.5`
- **THEN** `chat.completions.create(temperature=0.5, ...)` is called

#### Scenario: Auto-generated seed when not specified
- **WHEN** no seed is specified in slide or global config
- **THEN** a unique integer seed is auto-generated per slide using timestamp
- **AND** the actual seed used is recorded in generation results

---

### Requirement: Image Extraction from message.images
The system SHALL extract generated image bytes from `message.images[0].image_url.url` (accessed via `model_dump()`), with fallback to the `content` list.

#### Scenario: Image found in message.images
- **WHEN** the chat.completions response contains `message.images` with a data URI
- **THEN** image bytes are decoded from `message.images[0].image_url.url` after stripping the `data:image/...;base64,` prefix

#### Scenario: No image in response
- **WHEN** `message.images` is empty or absent
- **AND** `message.content` contains no image parts
- **THEN** generation fails for that slide with error "No image data in response"
- **AND** the batch continues with remaining slides
