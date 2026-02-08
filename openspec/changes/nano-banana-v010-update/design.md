## Context

The nano-banana plugin generates AI-powered presentation slides using Gemini and Imagen APIs. It currently
supports brand styling (TrendLife) with automatic logo overlay using Pillow. The plugin is distributed via
Claude Code, where users clone the repository and run scripts using `uv --managed-python`.

**Current State:**

- Logo files: Managed by Git LFS (`trendlife-logo.png` at 7693×1360, 166 KB)
- Logo overlay: Post-processing step using Pillow, applied to all TrendLife slides uniformly
- Python requirement: `requires-python = ">=3.14"` with `datetime.UTC` import (Python 3.11+ only)
- Error handling: Basic PIL exceptions, no Git LFS awareness
- Documentation: Minimal prerequisites, assumes Git LFS and uv are properly configured

**Problem:**

1. **Git LFS issue (primary)**: Users without Git LFS get pointer files (plain text), causing PIL to fail
   with cryptic "cannot identify image file" errors
2. **Cover page aesthetics**: Logo appears as small corner overlay on title slides instead of being
   professionally integrated into the design
3. **Python compatibility**: Users bypassing uv with Python 3.9-3.13 hit ImportError on `datetime.UTC`
4. **Poor error messages**: No guidance when environment setup is incorrect

**Constraints:**

- Must maintain backward compatibility with existing slide generation workflows
- Cannot modify logo image itself (TrendLife trademark)
- uv remains the supported execution method (`requires-python = ">=3.14"` unchanged)
- No new external dependencies (use existing Pillow, google-genai)

**Stakeholders:**

- End users: Need clear error messages and smooth installation
- Plugin maintainers: Need consistent brand compliance
- Claude Code users: Downloading and using plugin via git clone

## Goals / Non-Goals

**Goals:**

- Resolve #1 user issue: Git LFS pointer files causing PIL failures
- Improve TrendLife cover page visual quality through AI-generated branding
- Enable Python 3.9+ fallback for edge cases while maintaining 3.14+ as standard
- Provide actionable error messages for common setup issues
- Update to 2026 TrendLife logo across all assets
- Document prerequisites clearly (Git LFS, uv 0.4.0+, Python versions)

**Non-Goals:**

- Auto-installing Git LFS or uv (users must install these themselves)
- Supporting Python <3.9 (too old, incompatible with timezone.utc approach)
- Migrating away from Git LFS for logo storage (current solution works when properly configured)
- Adding logo customization or positioning controls (keep automatic behavior)
- Supporting reference images in Imagen API (API limitation, Gemini only)
- Refactoring entire codebase or changing architecture

## Decisions

### Decision 1: Gemini API Reference Image for Cover Pages

**Choice:** Use Gemini API's multi-modal content array (`contents = [prompt, logo_image]`) to pass logo as
reference image for title/cover slides, allowing AI to generate professional cover designs that incorporate
the logo.

**Rationale:**

- Gemini API supports PIL Image objects as content (documented feature)
- AI can integrate logo naturally into cover design (better than corner overlay)
- Logo remains unmodified (trademark compliance) but positioned by AI
- Only applies to title slides; content slides continue using post-processing overlay

**Alternatives considered:**

- **Keep corner overlay for all slides**: Rejected - cover pages look unprofessional with small corner logo
- **Use image-to-image generation**: Rejected - requires additional API calls and complexity
- **Manual logo positioning parameters**: Rejected - adds complexity, auto-detection is simpler

**Implementation approach:**

1. Detect layout type using existing `detect_layout_type()` function
2. If TrendLife + title slide: Load logo as PIL Image, pass in `contents` array with prompt
3. Enhance prompt with brand colors + instruction: "Use exact logo from reference image - DO NOT modify"
4. Skip post-processing overlay for title slides (logo already in generated image)
5. For Imagen API (no reference image support): Log warning, generate with prompt only, apply corner overlay

**Trade-off:** Gemini-only feature (Imagen cannot use reference images), but Imagen usage is rare for branded slides.

---

### Decision 2: Git LFS Pointer Detection via File Content Check

**Choice:** When logo loading fails, read file as text and check if first line contains
`version https://git-lfs.github.com/spec/v1` to identify Git LFS pointers. Provide clear installation
instructions.

**Rationale:**

- Git LFS pointers are plain text files with predictable format (version line at top)
- Simple text read operation is cheap and reliable
- Can distinguish LFS issue from other PIL errors (corrupted file, wrong format)
- Provides actionable solution: install Git LFS + run `git lfs pull`

**Alternatives considered:**

- **Check file size**: Rejected - unreliable, pointers and small images can both be <1KB
- **Pre-flight Git LFS check**: Rejected - requires shelling out to git commands, adds complexity
- **Bundle logos in repo without LFS**: Rejected - increases repo size, doesn't solve existing clones
- **Download logos from URL at runtime**: Rejected - requires internet, complicates offline use

**Implementation approach:**

```python
try:
    logo_image = PILImage.open(logo_path)
except Exception as e:
    try:
        with open(logo_path, 'r', encoding='utf-8') as f:
            if 'version https://git-lfs.github.com' in f.readline():
                print("Error: Logo file is Git LFS pointer", file=sys.stderr)
                print("Solution: git lfs install && git lfs pull", file=sys.stderr)
                return error_result
    except:
        pass  # Not LFS issue
    # Re-raise original PIL error
    raise
```

**Trade-off:** Adds try-except nesting, but dramatically improves user experience for the #1 reported issue.

---

### Decision 3: Dynamic UTC Import with Fallback

**Choice:** Use try-except to import `datetime.UTC` (Python 3.11+), fallback to `timezone.utc` (Python 3.2+)
if ImportError. Keep `requires-python = ">=3.14"` in metadata unchanged.

**Rationale:**

- `requires-python` is enforced by uv (standard path), ensures Python 3.14+ for managed execution
- Fallback enables Python 3.9-3.13 for users who bypass uv (edge case, but possible)
- `timezone.utc` is functionally identical to `UTC` (same underlying tzinfo)
- No code changes needed beyond import statement - all `datetime.now(UTC)` calls work as-is

**Alternatives considered:**

- **Hard require Python 3.14+**: Rejected - breaks edge cases, no technical benefit
- **Lower requires-python to 3.9**: Rejected - signals old Python is supported, contradicts uv philosophy
- **Use only timezone.utc**: Rejected - unnecessarily avoids modern Python APIs
- **Detect version and branch logic**: Rejected - unnecessary complexity when import fallback is sufficient

**Implementation approach:**

```python
# At top of file (line ~57)
try:
    from datetime import datetime, UTC
except ImportError:
    # Fallback for Python < 3.11
    from datetime import datetime, timezone
    UTC = timezone.utc

# All existing code using datetime.now(UTC) remains unchanged
```

**Trade-off:** Supports "unsupported" Python versions (with warning), but increases robustness for users in
non-standard environments.

---

### Decision 4: Python Version Check (No Dependency Check)

**Choice:** Add `check_environment()` function that validates Python version only (error <3.9, warning <3.14).
Do NOT check for Pillow, google-genai, or other dependencies.

**Rationale:**

- uv automatically installs dependencies from PEP 723 metadata (script header)
- Dependency ImportErrors from Python are clear and actionable ("ModuleNotFoundError: No module named 'PIL'")
- Pre-flight dependency checks add complexity without value
- Python version check catches the main environment issue (too old = incompatible)

**Alternatives considered:**

- **Check all dependencies**: Rejected - unnecessary, uv handles this, adds maintenance burden
- **No environment check at all**: Rejected - misses opportunity for helpful warnings
- **Check uv availability**: Rejected - script runs via `uv run`, so uv is always present

**Implementation approach:**

```python
def check_environment():
    import sys
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ required", file=sys.stderr)
        sys.exit(1)
    elif sys.version_info < (3, 14):
        print("Warning: Python 3.14+ recommended", file=sys.stderr)

# Call at start of main()
def main():
    check_environment()
    # ... existing code
```

**Trade-off:** Only checks Python version, but this is the appropriate scope given uv's dependency management.

---

### Decision 5: Logo Path Update Strategy

**Choice:** Simple string replacement across all files: `trendlife-logo.png` → `trendlife-2026-logo-light.png`.
No changes to positioning logic (percentage-based sizing auto-adjusts).

**Rationale:**

- New logo dimensions (2780×511) differ from old (7693×1360), but positioning uses percentage of slide width
- Existing `logo_width = slide_width * 0.1534` automatically scales to new size
- Pillow LANCZOS resampling maintains quality
- No layout changes needed - just asset replacement

**Alternatives considered:**

- **Keep both logos**: Rejected - confuses users, no use case for old logo
- **Adjust positioning constants**: Rejected - unnecessary, percentage-based positioning handles size changes
- **Version logos in separate directories**: Rejected - over-engineering for single logo update

**Implementation approach:**

1. Find/replace `trendlife-logo.png` → `trendlife-2026-logo-light.png` in:
   - Python code (2 locations in generate_images.py)
   - Documentation (5 locations across SKILL.md, brand-styles.md, assets/README.md, logos/README.md)
2. Delete old logo file
3. Verify new logo file exists and is not LFS pointer

**Trade-off:** Requires updating multiple files, but straightforward and low-risk.

## Risks / Trade-offs

### Risk 1: Reference Image Quality Depends on AI Interpretation

**Risk:** Gemini may position logo poorly or ignore brand color instructions on cover pages.

**Mitigation:**

- Prompt explicitly instructs: "Use exact logo from reference image - DO NOT modify"
- Brand colors specified in detail with hex codes
- Layout type detection tested to ensure only true title slides use this feature
- If quality is poor, users can regenerate with different prompt or use Imagen (corner overlay)

---

### Risk 2: Git LFS Pointer Detection False Positives/Negatives

**Risk:** File content check could misidentify non-LFS files or miss LFS pointers with different formats.

**Mitigation:**

- Check is inside exception handler (only runs when PIL fails)
- Uses standard LFS pointer format (`version https://git-lfs.github.com/spec/v1`)
- If detection fails, original PIL error is shown (existing behavior)
- False positive unlikely (legitimate images don't contain that string)

---

### Risk 3: Python 3.9-3.13 Users May Miss Warnings

**Risk:** Warning printed to stderr may be overlooked if users redirect output.

**Mitigation:**

- Warning is printed before any processing starts (visible immediately)
- Script still runs successfully (non-blocking warning)
- Documentation emphasizes Python 3.14+ via uv as standard approach
- Fallback is safety net, not primary support path

---

### Risk 4: Imagen API Users Lose Reference Image Feature

**Risk:** Users generating TrendLife covers with Imagen API get corner overlay instead of integrated logo.

**Mitigation:**

- Imagen usage is rare for branded slides (Gemini is default)
- Warning logged when Imagen + title slide detected
- Corner overlay is current behavior anyway (not a regression)
- Documentation clarifies reference image is Gemini-only

---

### Risk 5: Version Bump Communication

**Risk:** Users may not notice breaking/non-breaking nature of 0.0.9 → 0.1.0 bump.

**Mitigation:**

- Minor version bump (0.1.0) signals new features, backward compatible
- "Recent Improvements" section in README highlights changes
- No breaking API changes (all changes are additive or internal)
- Existing workflows continue working without modification

## Migration Plan

**Pre-deployment:**

1. Test Git LFS detection with actual pointer file (create test case)
2. Visual verification: Generate TrendLife deck (title + content slides) and confirm:
   - Title slide: Logo integrated in cover design (not corner)
   - Content slides: Logo in bottom-right corner (existing behavior)
3. Python version testing:
   - Python 3.14: No warnings
   - Python 3.11-3.13: Warning shown, script runs
   - Python 3.9-3.10: Warning shown, script runs
   - Python 3.8: Error and exit

**Deployment:**

- Changes are client-side only (no server/API changes)
- Users pull latest code via git
- New logo file already in repo (uploaded)
- No database migrations or service restarts needed

**Rollback:**

- If issues discovered: Revert commit, users pull previous version
- Old logo file preserved in git history (can restore if needed)
- No data migration required

**Verification:**

1. Logo search: `grep -r "trendlife-logo.png" plugins/nano-banana/` returns empty
2. LFS check: `head -1 plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-2026-logo-light.png`
   shows binary data (PNG header), not LFS pointer
3. Version check: `grep "0\.0\.9" plugins/nano-banana/ README.md` returns empty

## Open Questions

1. **Gemini prompt tuning**: Current prompt instructs "use exact logo - DO NOT modify" but relies on AI
   interpretation. May need iteration based on user feedback.

2. **Logo position on covers**: Should we add layout hints like "center" or "upper area" to prompt, or let AI
   decide naturally?
   - **Decision**: Include "typically center or upper area" as hint, but allow AI flexibility

3. **Backward compatibility window**: How long should we keep old logo file in git history before cleaning LFS storage?
   - **Decision**: Not urgent, LFS storage is cheap, keep indefinitely

4. **Error message localization**: Should Git LFS error messages support multiple languages?
   - **Decision**: English only for now (matches rest of error messages)
