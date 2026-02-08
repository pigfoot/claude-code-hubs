# python-compatibility Specification

## Purpose

Provide Python version compatibility layer that enables the nano-banana plugin to run on Python 3.9+ through
dynamic import fallbacks, while maintaining Python 3.14+ as the recommended version via uv-managed execution.

## ADDED Requirements

### Requirement: Dynamic UTC Import Fallback

The script SHALL attempt to import `datetime.UTC` (Python 3.11+) and fallback to `timezone.utc` (Python 3.2+)
if unavailable, ensuring compatibility across Python 3.9-3.14+.

**ID:** `python-compatibility-001`
**Priority:** High

#### Scenario: Python 3.14 uses datetime.UTC

**WHEN** script runs on Python 3.14+
**THEN**:

- `datetime.UTC` import succeeds
- No fallback logic triggered
- All `datetime.now(UTC)` calls use Python 3.11+ native UTC constant

#### Scenario: Python 3.9-3.10 falls back to timezone.utc

**WHEN** script runs on Python 3.9 or 3.10
**THEN**:

- `datetime.UTC` import fails with ImportError
- Fallback imports `timezone.utc`
- UTC variable is aliased to `timezone.utc`
- All `datetime.now(UTC)` calls work identically (same underlying tzinfo)

#### Scenario: Python 3.11-3.13 uses datetime.UTC

**WHEN** script runs on Python 3.11, 3.12, or 3.13
**THEN**:

- `datetime.UTC` import succeeds
- No fallback logic triggered
- Behavior identical to Python 3.14

**Rationale:** `timezone.utc` has been available since Python 3.2 and is functionally identical to
`datetime.UTC`. Dynamic fallback enables edge cases where users bypass uv and run with older Python versions.

---

### Requirement: Python Version Validation

The script SHALL validate the Python version at startup and provide clear error or warning messages based on
version compatibility.

**ID:** `python-compatibility-002`
**Priority:** High

#### Scenario: Python 3.8 or older fails immediately

**WHEN** script is executed with Python 3.8 or older
**THEN**:

- Error message printed to stderr: "Error: Python 3.9+ required for fallback support, but running X.Y"
- Hint printed to stderr: "This script should be run with 'uv run --managed-python' to automatically use Python 3.14+"
- Script exits with code 1 (failure)
- No processing attempted

#### Scenario: Python 3.9-3.13 shows warning but continues

**WHEN** script is executed with Python 3.9, 3.10, 3.11, 3.12, or 3.13
**THEN**:

- Warning message printed to stderr: "Warning: Python X.Y detected. Python 3.14+ is recommended."
- Hint printed to stderr: "Use 'uv run --managed-python' for optimal compatibility"
- Script continues execution normally
- Warning displayed before any processing starts

#### Scenario: Python 3.14+ runs without warnings

**WHEN** script is executed with Python 3.14 or newer
**THEN**:

- No version messages printed
- Script proceeds directly to processing
- Optimal execution path

**Rationale:** Python 3.9 is the minimum version supporting timezone.utc fallback. Versions 3.9-3.13 work but
receive warnings to guide users toward the supported path (Python 3.14+ via uv).

---

### Requirement: No Dependency Pre-flight Checks

The script SHALL NOT check for the presence of dependencies (Pillow, google-genai) at startup, relying on uv's
automatic dependency installation and Python's native ImportError messages.

**ID:** `python-compatibility-003`
**Priority:** Medium

#### Scenario: Dependencies missing when using uv

**WHEN** script is executed via `uv run --managed-python` and dependencies are not installed
**THEN**:

- uv automatically installs dependencies from PEP 723 script metadata
- Script runs successfully after installation
- No manual dependency checks needed

#### Scenario: Dependencies missing when bypassing uv

**WHEN** script is executed directly with python command and dependencies are missing
**THEN**:

- Python raises ImportError: "ModuleNotFoundError: No module named 'PIL'"
- Error message is clear and actionable (standard Python behavior)
- No custom dependency checking logic needed

#### Scenario: Environment check function only validates Python version

**WHEN** `check_environment()` function is called
**THEN**:

- Only Python version is checked (sys.version_info)
- No attempts to import Pillow, google-genai, or other dependencies
- Function completes quickly (no I/O operations)

**Rationale:** uv handles dependency installation automatically via PEP 723 metadata. Adding custom dependency
checks would duplicate functionality, add maintenance burden, and provide no user benefit (Python's ImportError
is already clear).

---

### Requirement: Preserve PEP 723 Metadata

The script SHALL maintain `requires-python = ">=3.14"` in PEP 723 metadata header, ensuring uv enforces
Python 3.14+ for managed execution.

**ID:** `python-compatibility-004`
**Priority:** High

#### Scenario: PEP 723 metadata specifies Python 3.14+

**WHEN** script metadata header is inspected
**THEN**:

- Header contains: `# /// script`
- Header contains: `requires-python = ">=3.14"`
- Header defines dependencies: `google-genai`, `pillow`

#### Scenario: uv enforces Python 3.14 requirement

**WHEN** script is executed via `uv run --managed-python`
**THEN**:

- uv reads PEP 723 metadata
- uv ensures Python 3.14+ is used (downloads if needed)
- Script never runs on Python <3.14 via standard path

#### Scenario: Fallback logic activates only when bypassing uv

**WHEN** user directly runs script with `python generate_images.py`
**THEN**:

- PEP 723 metadata is ignored (plain Python execution)
- Fallback logic in script code activates if Python <3.14
- Warning messages guide user toward uv execution

**Rationale:** Maintaining `requires-python = ">=3.14"` in metadata preserves the official support policy while
runtime fallback handles edge cases gracefully.
