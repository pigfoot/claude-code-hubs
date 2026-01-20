# config-simplification Specification

## Purpose
TBD - created by archiving change eliminate-heredoc-hallucinations. Update Purpose after archive.
## Requirements
### Requirement: Remove Model Field from Config

The configuration file SHALL NOT include a `model` field. Model selection SHALL be controlled exclusively by the `NANO_BANANA_MODEL` environment variable.

**ID:** `config-simplification-001`
**Priority:** High

#### Scenario: Config without model field

**Given:** Claude creates config for image generation
**When:** Building the JSON config
**Then:**
- Config does NOT contain `"model"` field
- Model is determined by environment variable only
- Claude never specifies model in config

Example config:
```json
{
  "slides": [...],
  "output_dir": "./001-slides/"
  // NO "model" field
}
```

#### Scenario: Model selection priority

**Given:** Script executes with config
**When:** Determining which model to use
**Then:**
- Priority 1: `NANO_BANANA_MODEL` environment variable
- Priority 2: Default (`"gemini-3-pro-image-preview"`)
- Config file is never checked for model

Script logic:
```python
model = os.environ.get("NANO_BANANA_MODEL") or "gemini-3-pro-image-preview"
# Note: config.get('model') is NOT used
```

**Rationale:** Prevents Claude from hallucinating incorrect model names (e.g., missing `-preview` suffix). User environment variable takes precedence.

---

### Requirement: Minimal Required Fields

The configuration file SHALL require only two fields: `slides` and `output_dir`.

**ID:** `config-simplification-002`
**Priority:** High

#### Scenario: Minimal valid config

**Given:** Claude needs to generate config
**When:** Creating the most basic valid config
**Then:**
- Config contains `slides` array (required)
- Config contains `output_dir` string (required)
- No other fields are required
- Config is valid and accepted by script

Minimal example:
```json
{
  "slides": [
    {"number": 1, "prompt": "AI safety overview"}
  ],
  "output_dir": "./001-ai-safety/"
}
```

#### Scenario: Optional fields

**Given:** User needs customization
**When:** Advanced config is needed
**Then:**
- Optional fields may be added: `format`, `quality`
- Claude should NOT add these unless user explicitly requests
- Defaults are used when optional fields absent

Example with optional fields:
```json
{
  "slides": [...],
  "output_dir": "./001-slides/",
  "format": "png",        // Optional, default: "webp"
  "quality": 95           // Optional, default: 90
}
```

**Rationale:** Less for Claude to generate = less chance of error. Optional fields only when needed.

---

### Requirement: Relative Path Enforcement

The `output_dir` field SHALL only accept relative paths. Absolute paths SHALL be rejected with a clear error message.

**ID:** `config-simplification-003`
**Priority:** High

#### Scenario: Relative path accepted

**Given:** Config with relative `output_dir`
**When:** Script validates config
**Then:**
- Path is accepted
- Script creates directory relative to execution location

Valid examples:
- `"./001-slides/"`
- `"../output/slides/"`
- `"slides/"`

#### Scenario: Absolute path rejected (Unix-style)

**Given:** Config with absolute Unix path
**When:** Script validates config
**Then:**
- Validation fails with error
- Error message: "output_dir must be relative path, got: /home/user/slides/"
- Suggests: "Use './dirname/' instead for cross-platform compatibility"
- Script exits with code 1

Rejected example:
```json
{
  "output_dir": "/home/user/slides/"  // ❌ Absolute path
}
```

#### Scenario: Absolute path rejected (Windows-style)

**Given:** Config with Windows absolute path
**When:** Script validates config
**Then:**
- Validation fails with error
- Error message includes the rejected path
- Same clear guidance as Unix case

Rejected examples:
- `"C:\\Users\\slides\\"`
- `"/c/Users/slides/"` (Git Bash style)

#### Scenario: Validation error is actionable

**Given:** User receives absolute path error
**When:** Reading error message
**Then:**
- Message clearly states the problem
- Message shows the rejected path
- Message suggests correct format
- User can fix without further research

Error format:
```
Error: output_dir must be relative path, got: /home/user/slides/
Use './dirname/' instead for cross-platform compatibility.
```

**Rationale:** Relative paths avoid Git Bash `/c/Users` vs Windows `C:\Users` conflicts and improve portability.

---

### Requirement: Cross-Platform Temp File Paths

Progress and results files SHALL use platform-appropriate temporary directories via `tempfile.gettempdir()`.

**ID:** `config-simplification-004`
**Priority:** High

#### Scenario: Temp files on Linux/macOS

**Given:** Script runs on Linux or macOS
**When:** Creating progress/results files
**Then:**
- Files created in `/tmp/`
- Paths: `/tmp/nano-banana-progress.json`, `/tmp/nano-banana-results.json`

#### Scenario: Temp files on Windows

**Given:** Script runs on Windows
**When:** Creating progress/results files
**Then:**
- Files created in Windows temp directory
- Path: `C:\Users\<user>\AppData\Local\Temp\nano-banana-progress.json`
- No `/tmp/` errors

#### Scenario: No hardcoded paths

**Given:** Script source code
**When:** Reviewing temp file path logic
**Then:**
- No hardcoded `/tmp/` strings
- Uses `Path(tempfile.gettempdir())`
- Works on all platforms automatically

Implementation:
```python
import tempfile
from pathlib import Path

TEMP_DIR = Path(tempfile.gettempdir())
PROGRESS_FILE = TEMP_DIR / "nano-banana-progress.json"
RESULTS_FILE = TEMP_DIR / "nano-banana-results.json"
```

**Rationale:** Hardcoded `/tmp/` causes `FileNotFoundError` on Windows. `tempfile.gettempdir()` is cross-platform standard.

---

### Requirement: Config Field Documentation

Configuration field requirements and examples SHALL be clearly documented in SKILL.md.

**ID:** `config-simplification-005`
**Priority:** Medium

#### Scenario: Config documentation in SKILL.md

**Given:** Claude needs to know config format
**When:** Reading SKILL.md
**Then:**
- Required fields clearly marked
- Optional fields clearly marked
- Examples show minimal config
- Path requirements explained
- Model field explicitly noted as removed

Documentation includes:
```markdown
### Config Requirements

**Minimal Config (recommended):**
```json
{
  "slides": [{"number": 1, "prompt": "...", "style": "trendlife"}],
  "output_dir": "./001-slides/"  // Must be relative path
}
```

**Field Rules:**
- ✅ `output_dir` MUST be relative path
- ❌ NO absolute paths (breaks cross-platform)
- ❌ NO `model` field (use NANO_BANANA_MODEL env var)
```

**Rationale:** Clear documentation prevents Claude from adding unnecessary or incorrect fields.

