# unified-generation Specification

## Purpose

Define a unified image generation workflow that eliminates AI hallucinations by replacing dynamic code generation (heredocs) with a fixed Python script + JSON config pattern.

## ADDED Requirements

### Requirement: Single Workflow for All Image Counts

The system SHALL use the same fixed Python script (`generate_images.py`) for all image generation tasks, regardless of the number of images (1-100).

**ID:** `unified-generation-001`
**Priority:** High

#### Scenario: Single image generation

**Given:** User requests 1 image
**When:** Claude prepares generation
**Then:**
- Claude creates JSON config with 1 slide
- Calls `uv run generate_images.py --config <path>`
- Same script as batch mode
- No heredoc generation

#### Scenario: Small batch (3 images)

**Given:** User requests 3 images
**When:** Claude prepares generation
**Then:**
- Claude creates JSON config with 3 slides
- Calls `uv run generate_images.py --config <path>`
- Same script as single/large batch
- No mode switching logic

#### Scenario: Large batch (50 images)

**Given:** User requests 50 images
**When:** Claude prepares generation
**Then:**
- Claude creates JSON config with 50 slides
- Calls `uv run generate_images.py --config <path>`
- Same script behavior, scales naturally
- Progress tracking handles large counts

**Rationale:** Eliminates complexity of mode switching and ensures consistent, hallucination-free behavior across all use cases.

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

**Rationale:** Minimal config reduces what Claude needs to generate, lowering hallucination risk. Cross-platform paths avoid Windows errors.

---

### Requirement: Consistent Execution Pattern

Image generation SHALL always follow the same execution pattern: config creation → script execution → progress monitoring → result collection.

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
