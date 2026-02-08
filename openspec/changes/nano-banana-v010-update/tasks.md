## 1. Logo File Replacement

- [x] 1.1 Update logo path in generate_images.py line 408 to `trendlife-2026-logo-light.png`
- [x] 1.2 Update logo path in generate_images.py line 526 to `trendlife-2026-logo-light.png`
- [x] 1.3 Update logo path reference in SKILL.md (around line 226 example code)
- [x] 1.4 Update logo path description in references/brand-styles.md (around line 51)
- [x] 1.5 Update logo specifications in assets/logos/README.md (around line 11, dimensions updated to 2780×511)
- [x] 1.6 Update first asset reference in assets/README.md (around line 10)
- [x] 1.7 Update second asset reference in assets/README.md (around line 26)
- [x] 1.8 Update third asset reference in assets/README.md (around line 65)
- [x] 1.9 Delete old logo file `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png`

## 2. Cover Page Reference Image Handling

- [x] 2.1 Add cover page detection logic in generate_slide_gemini() function
  (check layout_type == "title" and style == "trendlife")
- [x] 2.2 Create special prompt enhancement for cover pages (including logo integration and trademark protection instructions)
- [x] 2.3 Load logo as PIL Image for cover pages and add to contents array (including Git LFS pointer error detection)
- [x] 2.4 Modify logo overlay logic to skip overlay for cover pages (layout_type == "title")
- [x] 2.5 Add Git LFS pointer detection and clear error messages when logo overlay fails
- [x] 2.6 Add warning message in generate_slide_imagen() function for TrendLife
  cover pages (Imagen API does not support reference images)

## 3. Python Version Compatibility

- [x] 3.1 Add UTC import fallback logic at line 57 in generate_images.py (try-except, fallback to timezone.utc)

## 4. Environment Checks and Documentation Improvements

- [x] 4.1 Add check_environment() function in generate_images.py (check Python 3.9+, warn <3.14, error <3.9)
- [x] 4.2 Call check_environment() at the start of main() function
- [x] 4.3 Update Prerequisites section in plugins/nano-banana/README.md (add Git LFS explanation and detailed uv explanation)
- [x] 4.4 Add "Common Errors and Solutions" section in SKILL.md (Git LFS listed as first item, including 5 common errors)

## 5. Version Number Update

- [x] 5.1 Update version number in `plugins/nano-banana/.claude-plugin/plugin.json` from 0.0.9 to 0.1.0
- [x] 5.2 Add "Recent Improvements (v0.1.0)" section at the top of `plugins/nano-banana/README.md`
- [x] 5.3 Update metadata version number in `plugins/nano-banana/skills/nano-banana/SKILL.md` from 0.0.9 to 0.1.0
- [x] 5.4 Update nano-banana version number in Available Plugins table in root `README.md` (around line 705)
