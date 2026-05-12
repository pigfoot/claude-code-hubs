## MODIFIED Requirements

### Requirement: Configuration File Creation
The system SHALL create a JSON configuration file containing slide specifications without the `model` field.

**ID:** `batch-generation-002`
**Priority:** High

#### Scenario: Creating config for mixed-style presentation
- **WHEN** user requests slides with different visual styles
- **THEN** a config JSON is created containing a slides array with number, prompt, and style fields
- **AND** includes `output_dir` as a relative path
- **AND** does NOT include a `model` field
- **AND** uses `IMAGE_GEN_MODEL` environment variable for model selection (not `NANO_BANANA_MODEL`)

Example:
```json
{
  "slides": [
    {"number": 1, "prompt": "Pipeline overview", "style": "professional"},
    {"number": 2, "prompt": "Build stage", "style": "data-viz"}
  ],
  "output_dir": "./ci-cd-deck/",
  "format": "webp",
  "quality": 90
}
```

---

## ADDED Requirements

### Requirement: Renamed Environment Variables
The system SHALL read the model name from `IMAGE_GEN_MODEL`, API credentials from `RDSEC_API_KEY`, and the endpoint URL from `IMAGE_GEN_BASE_URL`.

#### Scenario: Read model from IMAGE_GEN_MODEL
- **WHEN** the environment variable `IMAGE_GEN_MODEL` is set to `gemini-3-pro-image`
- **THEN** the script uses `gemini-3-pro-image` as the model for all API calls
- **AND** `NANO_BANANA_MODEL` is NOT read

#### Scenario: IMAGE_GEN_MODEL not set uses default
- **WHEN** `IMAGE_GEN_MODEL` is not set
- **THEN** the script uses `gemini-3-pro-image` as the default model

#### Scenario: Read credentials from RDSEC_API_KEY
- **WHEN** `RDSEC_API_KEY` is set
- **THEN** it is used as the API key for the OpenAI client
- **AND** `GEMINI_API_KEY` and `GOOGLE_API_KEY` are NOT read

#### Scenario: Read endpoint from IMAGE_GEN_BASE_URL
- **WHEN** `IMAGE_GEN_BASE_URL` is set to `https://api.rdsec.trendmicro.com/prod/aiendpoint/v1`
- **THEN** the OpenAI client uses this value as `base_url`
- **AND** `GOOGLE_GEMINI_BASE_URL` is NOT read

---

## REMOVED Requirements

### Requirement: GEMINI_API_KEY / GOOGLE_API_KEY Support
**Reason**: Replaced by `RDSEC_API_KEY` to reflect the actual credential provider (RDSEC ONE portal) and remove Google-specific naming.
**Migration**: Set `RDSEC_API_KEY` in `.env` or shell with the same JWT token value previously used for `GEMINI_API_KEY`.

### Requirement: NANO_BANANA_MODEL Support
**Reason**: Renamed to `IMAGE_GEN_MODEL` for provider-agnostic naming.
**Migration**: Rename `NANO_BANANA_MODEL` to `IMAGE_GEN_MODEL` in `.env` or shell.

### Requirement: GOOGLE_GEMINI_BASE_URL Support
**Reason**: Renamed to `IMAGE_GEN_BASE_URL` for provider-agnostic naming. The URL must include the `/v1` suffix for OpenAI-compatible routing.
**Migration**: Set `IMAGE_GEN_BASE_URL=https://api.rdsec.trendmicro.com/prod/aiendpoint/v1` (append `/v1` to the existing URL).
