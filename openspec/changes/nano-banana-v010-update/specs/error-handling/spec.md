# error-handling Specification (Delta)

## ADDED Requirements

### Requirement: Git LFS Pointer File Detection

The system SHALL detect when logo files are Git LFS pointers (text files) instead of actual images and
provide clear installation instructions.

**ID:** `error-handling-006`
**Priority:** Critical

#### Scenario: Git LFS pointer detected when loading logo

**WHEN** logo loading fails and file is a Git LFS pointer
**THEN**:

- File is read as text
- First line checked for `version https://git-lfs.github.com/spec/v1`
- Error message printed to stderr: "Error: Logo file is a Git LFS pointer, not the actual image."
- Solution printed to stderr: "Please install Git LFS and run: git lfs pull"
- Installation link printed: "Git LFS install: <https://git-lfs.com/>"
- Function returns error with message: "Logo file is Git LFS pointer - run git lfs pull"
- Slide generation fails gracefully (no crash)

#### Scenario: Legitimate PIL error not mistaken for LFS issue

**WHEN** logo loading fails but file is NOT a Git LFS pointer
**THEN**:

- File content check is attempted
- Check fails or doesn't match LFS pointer format
- Original PIL exception is re-raised
- Standard error handling proceeds
- No false positive LFS error message

#### Scenario: Git LFS detection in generate_slide_gemini

**WHEN** loading logo as reference image in Gemini API and file is LFS pointer
**THEN**:

- LFS detection runs inside logo loading exception handler
- Specific error message for Gemini context
- Function returns error tuple: `(False, None, "Logo file is Git LFS pointer - run git lfs pull", None, None)`
- Slide generation stops for this slide
- Error is logged in results

#### Scenario: Git LFS detection in logo overlay

**WHEN** loading logo for post-processing overlay and file is LFS pointer
**THEN**:

- LFS detection runs inside overlay exception handler
- Specific error message for overlay context
- Warning message logged: "Warning: Logo overlay failed for slide N: ..."
- Function returns error tuple: `(False, None, "Logo file is Git LFS pointer - run git lfs pull", None, None)`
- Slide generation may continue without logo (depending on handling)

**Rationale:** Git LFS pointer files are the #1 reported user issue. Without Git LFS installed, users get
cryptic "cannot identify image file" errors. Clear detection and installation instructions dramatically
improve user experience.

**Detection Logic:**

```python
try:
    logo_image = PILImage.open(logo_path)
except Exception as e:
    # Check if file is a Git LFS pointer (common issue)
    try:
        with open(logo_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if 'version https://git-lfs.github.com' in first_line:
                print("Error: Logo file is a Git LFS pointer, not the actual image.", file=sys.stderr)
                print("Please install Git LFS and run: git lfs pull", file=sys.stderr)
                print("Git LFS install: https://git-lfs.com/", file=sys.stderr)
                return error_result
    except:
        pass  # Not LFS issue, re-raise original PIL error
    raise  # Re-raise original exception if not LFS
```

---

### Requirement: Documentation of Common Errors

The SKILL.md SHALL document common error scenarios with solutions, prioritizing Git LFS issues.

**ID:** `error-handling-007`
**Priority:** High

#### Scenario: Git LFS error listed as most common issue

**WHEN** Claude reads SKILL.md error handling section
**THEN**:

- "Common Errors and Solutions" section exists
- Git LFS pointer error is listed as issue #1
- Section includes detection phrases: "Logo file is Git LFS pointer" OR "cannot identify image file"
- Solution includes step-by-step installation: `git lfs install` then `git lfs pull`
- Link to Git LFS website provided

#### Scenario: Error handling section covers uv and Python issues

**WHEN** Claude reads SKILL.md error handling section
**THEN**:

- "command not found: uv" error documented with installation instructions
- "Python 3.14+ recommended" warning explained with uv usage hint
- Permission and download errors covered with diagnostic steps
- Missing dependencies error explained (should use uv run)

#### Scenario: Claude uses error documentation proactively

**WHEN** script execution fails with known error pattern
**THEN**:

- Claude checks SKILL.md "Common Errors and Solutions"
- Claude matches error message to documented pattern
- Claude provides solution from documentation
- Claude explains root cause and prevention

**Rationale:** Documenting common errors in SKILL.md enables Claude to provide accurate solutions without
guessing, improving user experience and reducing support burden.
