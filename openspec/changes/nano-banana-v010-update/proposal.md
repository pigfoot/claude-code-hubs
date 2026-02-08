## Why

Users frequently encounter errors when using the nano-banana plugin after downloading via Claude Code, primarily
due to Git LFS pointer files instead of actual logo images. Additionally, the current TrendLife logo needs
updating to the 2026 version, and cover pages require special handling to incorporate the logo professionally
rather than as a small corner overlay. Python version compatibility issues also affect users who bypass uv
and run scripts directly.

## What Changes

- **Logo Update**: Replace `trendlife-logo.png` with `trendlife-2026-logo-light.png` (2026 brand refresh) across
  all code and documentation
- **Smart Cover Pages**: TrendLife slide deck cover pages now use logo as reference image (Gemini API) for
  professional AI-generated branding, instead of simple corner overlay
- **Git LFS Error Detection**: Add automatic detection of Git LFS pointer files with clear installation
  instructions when logo loading fails
- **Python Compatibility**: Add fallback support for Python 3.9+ using `timezone.utc` when `datetime.UTC`
  (Python 3.11+) is unavailable, while maintaining `requires-python = ">=3.14"` for uv-managed execution
- **Environment Checks**: Add pre-flight Python version checks (error <3.9, warning <3.14) with helpful hints
- **Improved Documentation**: Update README and SKILL.md with Git LFS prerequisites, uv requirements, and
  common error solutions
- **Version Bump**: 0.0.9 → 0.1.0 (minor version) across all metadata files

## Capabilities

### New Capabilities

- `python-compatibility`: Python version compatibility layer with dynamic UTC import fallback and environment validation

### Modified Capabilities

- `error-handling`: Add Git LFS pointer file detection as a new error type with actionable installation
  instructions
- `logo-overlay`: Update to skip logo overlay for title/cover slides (logo already in generated image) and
  change logo file path to new 2026 version
- `brand-styling`: Enhance TrendLife style to use logo as reference image for Gemini API when generating
  cover pages, ensuring professional brand integration

## Impact

**Code:**

- `plugins/nano-banana/skills/nano-banana/scripts/generate_images.py`: Major modifications in 5 locations
  (UTC import, generate_slide_gemini function, logo overlay logic, environment checks)
- `plugins/nano-banana/skills/nano-banana/logo_overlay.py`: Logo path updates

**Documentation:**

- `plugins/nano-banana/README.md`: Prerequisites section expansion, Recent Improvements section addition
- `plugins/nano-banana/skills/nano-banana/SKILL.md`: Common Errors section addition, metadata version update, logo
  path references
- `plugins/nano-banana/skills/nano-banana/references/brand-styles.md`: Logo path updates
- `plugins/nano-banana/skills/nano-banana/assets/logos/README.md`: Logo specifications update
- `plugins/nano-banana/skills/nano-banana/assets/README.md`: Asset references update
- Root `README.md`: Marketplace version table update

**Assets:**

- Delete: `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png` (old logo)
- Use: `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-2026-logo-light.png` (already uploaded)

**Metadata:**

- `plugins/nano-banana/.claude-plugin/plugin.json`: Version field update

**Dependencies:**

- No new dependencies (uses existing Pillow, google-genai)
- uv version requirement clarified as 0.4.0+ in documentation

**User Impact:**

- Resolves most common user installation issue (Git LFS pointer files)
- Improves cover page visual quality (reference image vs. simple overlay)
- Better error messages guide users to solutions
- Backward compatible for Python 3.9+ users (with warnings)
