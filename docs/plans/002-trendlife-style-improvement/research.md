# Research: TrendLife Style Implementation

## Executive Summary

This document contains research findings for implementing TrendLife brand style in the nano-banana plugin, including industry best practices for AI-generated branded presentations and detailed analysis of the TrendLife PowerPoint template.

**Key Finding:** Google's hybrid approach (Imagen 3 + Pillow overlay) is the industry-recommended method for generating branded slides with perfect logo preservation.

---

## Industry Best Practices (2026)

### AI Image Generation with Brand Logos

#### Microsoft Copilot Approach

**Key Features:**
- Integrates DALL·E 3 directly in PowerPoint
- Automatically applies company PowerPoint templates including logos, fonts, and color schemes
- Supports company digital asset managers (DAM) and Microsoft organizational asset libraries (OALs)
- Available to general public since June 2025

**Best Practices:**
- Customize templates in Slide Master view
- Add logos, colors, and fonts so they are inherited by all layouts
- Use Copilot PowerPoint starter template optimized for AI generation
- Keep template layout names as-is for optimal Copilot performance

**Source:** [Keep your presentation on-brand with Copilot - Microsoft Support](https://support.microsoft.com/en-us/topic/keep-your-presentation-on-brand-with-copilot-046c23d5-012e-49e0-8579-fe49302959fc)

#### Google Imagen 3 + Gemini Approach ⭐ **Recommended**

**Key Features:**
- Imagen 3 generates high-quality brand-styled images
- Gemini selects and refines generated images
- Pillow library adds logos with optimal placement and size
- Ensures maximum logo accuracy without distortion

**Workflow:**
1. Imagen 3 generates initial images with brand colors
2. Gemini refines and selects best results
3. Pillow performs precise logo integration and manipulation

**Logo Overlay Process:**
- Multi-image to image composition for product mockups
- Realistic composite visual input that feels branded and intentional
- Keeps logos accurately intact without distortions
- Available through Vertex AI, Figma integration, and Google Workspace

**Source:** [Build a brand logo with Imagen 3 and Gemini | Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/build-a-brand-logo-with-imagen-3-and-gemini)

#### Other AI Tools (2026)

**Beautiful.ai:**
- AI image generation matching brand identity
- Automatic brand asset application

**Plus AI:**
- Brand asset integration (colors, fonts, logos)
- Custom branded presentations

**Source:** [Custom branded presentations | Plus AI](https://plusai.com/features/custom-branded-presentations)

### Key Takeaways

1. **Logo overlay is preferred over prompt-based logo generation** - prevents distortion
2. **Template-based approach** - use Slide Master for consistent brand elements
3. **Separation of concerns** - generate content separately, composite with branding
4. **Precision tools** - use libraries like Pillow for exact logo placement

---

## TrendLife PowerPoint Template Analysis

### Template Structure

**File:** `plugins/nano-banana/skills/nano-banana/assets/templates/1201_TrendLife PowerPoint Deck.pptx`

**Basic Information:**
- **Slide count:** 29 sample slides
- **Dimensions:** 13.33" × 7.5" (33.87cm × 19.05cm)
- **Aspect ratio:** 16:9 (standard presentation format)
- **Slide masters:** 1 master with 20 layouts

### Slide Layouts

The template provides 20 different layouts categorized as:

**Title Slides (7 layouts):**
- Title slide - Life #1
- Title slide - Life #2
- Title slide - Tokyo
- 1_Title slide - Tokyo
- 2_Title slide - Tokyo
- Title slide - Family
- Title slide - T Symbol

**Divider Slides (6 layouts):**
- Divider slide #1
- 1_Divider slide #1
- Divider slide #2
- Divider slide #3
- Divider slide #4
- Divider slide #5
- Divider slide #6

**Content Slides (4 layouts):**
- White with Title + Body
- White with Title
- White Blank
- Highlights slide

**Closing Slide (1 layout):**
- End slide

### Color Scheme

**Theme Name:** "TrendMicro-LightTheme" / "Trend"

**Primary Colors:**
| Element | Hex Code | Usage |
|---------|----------|-------|
| **Trend Red** | `#D71920` | Primary brand color (accent1) |
| **Guardian Red** | `#6F0000` | Supporting brand color (accent2, dk2) |
| **Trend Red 80%** | `#DE543B` | Tinted variation (accent3) |
| **Trend Red 40%** | `#EDA389` | Light tinted variation (accent4) |

**Neutral Colors:**
| Element | Hex Code | Usage |
|---------|----------|-------|
| Black | `#000000` | Dark primary (dk1) |
| White | `#FFFFFF` | Light primary (lt1) |
| Light Gray | `#E7E6E6` | Light secondary (lt2) |
| Dark Gray | `#57585B` | Accent 5 |
| Medium Gray | `#808285` | Accent 6 |

**System Colors:**
| Element | Hex Code | Usage |
|---------|----------|-------|
| Hyperlink | `#BCBEC0` | Link color |
| Followed Link | `#E6E7E8` | Visited link color |

### Typography

**Major Font (Headers):**
- Latin: Calibri Light
- Japanese: 游ゴシック Light (Yu Gothic Light)
- Chinese Simplified: 等线 Light
- Chinese Traditional: 新細明體
- Korean: 맑은 고딕

**Minor Font (Body):**
- Latin: Calibri
- Japanese: 游ゴシック (Yu Gothic)
- Chinese Simplified: 等线
- Chinese Traditional: 新細明體
- Korean: 맑은 고딕

### Logo Assets

**TrendLife Logo (Primary):** ✅ Found and extracted
- **Original file:** `ppt/media/image3.png` (306 KB)
- **Components:**
  - Red circular icon with "t" symbol
  - "TRENDLIFE" text (black "TREND" + red "LIFE")
  - Tagline: "Where Intelligence Meets Care" (cropped out for overlay)
- **Format:** PNG with transparency (RGBA)
- **Original dimensions:** 12532 × 1490 pixels
- **Cropped dimensions:** 7769 × 1490 pixels (aspect ratio 5.2:1)
- **Final asset:** `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png` (166 KB)
- **Colors:** Trend Red (#D71920) for icon and "LIFE", black for "TREND"

**Trend Micro Logo (Alternative):**
- **File:** `image1.png` (8.2 KB)
- **Components:** Red circular icon + "TREND MICRO" text
- **Format:** PNG with transparency
- **Note:** This is the corporate Trend Micro logo, different from TrendLife product logo

**Additional Brand Assets:**
- Multiple decorative images (image2-image35)
- Various sizes from 5.7 KB to 2.6 MB
- Mix of PNG and JPEG formats
- Color palette reference (image21.png)

### Logo Placement Analysis

**Confirmed from PowerPoint template inspection:**

**Position:** Bottom-right corner of slides
- **Standard placement:** Right-aligned, near bottom edge
- **Typical size:** 10-15% of slide width
- **Clear space:** Minimum 30-40px padding from edges

**Layout-specific positioning:**
- **Title slides:** Bottom-right corner with standard padding
- **Content slides:** Bottom-right corner, consistent with title slides
- **Divider slides:** Bottom-right corner maintained across layouts
- **Master slides:** Logo appears in Slide Master, inherited by all layouts

**Implementation note:** Logo overlay should target bottom-right corner with 40px horizontal and 30px vertical padding from slide edges, sized at 12-15% of slide width depending on layout type.

---

## Technical Investigation

### Existing nano-banana Implementation

**Current "Trend" Style:**
- Located in `references/brand-styles.md`
- Uses prompt-based color specification
- No logo overlay mechanism
- Colors specified in prompts sent to Gemini/Imagen

**Limitations:**
- Logo distortion when AI generates it
- No separation between content and branding
- Single "Trend" style for all Trend Micro presentations

### Proposed Technical Stack

**Image Generation:**
- Gemini Image API or Imagen API (existing)
- Prompt-based with TrendLife color palette

**Logo Overlay:**
- **Pillow (PIL)** - Python imaging library
- Already in dependencies: `["google-genai", "pillow"]`
- Capabilities:
  - Image composition
  - Precise positioning
  - Alpha channel handling (transparency)
  - No quality loss

**Output Format:**
- Lossless WebP (existing for slides)
- Maintains both image quality and logo precision

---

## Comparison of Approaches

### Approach A: Google Hybrid Method (Recommended) ⭐

**Description:** Imagen/Gemini generates background + Pillow overlays logo

**Pros:**
- ✅ Perfect logo accuracy (no AI distortion)
- ✅ Controllable image quality
- ✅ Industry best practice (Google recommended)
- ✅ All work done within nano-banana skill
- ✅ Uses existing dependencies (Pillow already included)

**Cons:**
- ⚠️ Need to define logo positions per layout type
- ⚠️ Adds one Pillow overlay step

**Implementation Complexity:** Medium

---

### Approach B: Template-First Method

**Description:** Generate images only, use ppt skill to insert into template

**Pros:**
- ✅ Logo positions managed by template (most accurate)
- ✅ Supports all 20 layouts automatically
- ✅ nano-banana focuses only on image generation

**Cons:**
- ❌ Not within nano-banana skill scope (more of a ppt skill feature)
- ❌ Requires ppt skill to have template integration capability
- ❌ Breaks single-skill workflow

**Implementation Complexity:** High (requires ppt skill changes)

---

### Approach C: Prompt-Based Logo (Not Recommended) ❌

**Description:** AI generates logo directly in image

**Pros:**
- ✅ Simple implementation

**Cons:**
- ❌ Logo distortion (user reported issue)
- ❌ Poor results (confirmed by user feedback)
- ❌ Not industry best practice

**Implementation Complexity:** Low (but poor results)

---

## Recommendation

**Selected Approach: A - Google Hybrid Method**

**Rationale:**
1. Balances image quality and logo precision (user requirement)
2. Follows industry best practice (Google 2026 approach)
3. Fully implementable within nano-banana skill scope
4. Highest logo accuracy with controllable image quality
5. Uses existing dependencies (no new libraries needed)

**Next Steps:**
1. Define standard logo positions for each layout category
2. Design TrendLife style configuration
3. Implement Pillow logo overlay workflow
4. Update brand-styles.md with TrendLife specs

---

## References

### Industry Sources

- [Build a brand logo with Imagen 3 and Gemini | Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/build-a-brand-logo-with-imagen-3-and-gemini)
- [Keep your presentation on-brand with Copilot - Microsoft Support](https://support.microsoft.com/en-us/topic/keep-your-presentation-on-brand-with-copilot-046c23d5-012e-49e0-8579-fe49302959fc)
- [Custom branded presentations | Plus AI](https://plusai.com/features/custom-branded-presentations)

### Template Analysis Tools

- python-pptx library for PowerPoint parsing
- Manual extraction of template colors and structure
- Logo assets extracted from ppt/media folder

---

## Appendix: Raw Data

### Template Color XML (theme1.xml)

```xml
<a:clrScheme name="Trend">
  <a:dk1><a:srgbClr val="000000"/></a:dk1>
  <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
  <a:dk2><a:srgbClr val="6E0000"/></a:dk2>
  <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
  <a:accent1><a:srgbClr val="D71920"/></a:accent1>
  <a:accent2><a:srgbClr val="6F0000"/></a:accent2>
  <a:accent3><a:srgbClr val="DE543B"/></a:accent3>
  <a:accent4><a:srgbClr val="EDA389"/></a:accent4>
  <a:accent5><a:srgbClr val="57585B"/></a:accent5>
  <a:accent6><a:srgbClr val="808285"/></a:accent6>
  <a:hlink><a:srgbClr val="BCBEC0"/></a:hlink>
  <a:folHlink><a:srgbClr val="E6E7E8"/></a:folHlink>
</a:clrScheme>
```

### Logo File Details

**TrendLife Logo (Primary - CONFIRMED):**
- **Source:** `ppt/media/image3.png` - 306 KB - TrendLife complete logo
- **Components:** Icon + "TRENDLIFE" + Tagline "Where Intelligence Meets Care"
- **Processing:** Cropped to 62% width to remove tagline
- **Final asset:** `plugins/nano-banana/skills/nano-banana/assets/logos/trendlife-logo.png` - 166 KB
- **Dimensions:** 7769 × 1490 pixels (cropped from 12532 × 1490)
- **Status:** ✅ Ready for implementation

**Alternative Logos Extracted:**
- `image1.png` - 8.2 KB - Trend Micro corporate logo (not used for TrendLife)
- `image21.png` - 39 KB - Color palette reference (not a logo)
- `image22.png` - 9.2 KB - UI element (not logo)
- `image23.png` - 23 KB - UI element (not logo)
- `image24.png` - 5.7 KB - UI element (not logo)

**Logo Selection Process:**
1. Initial assumption: `image1.png` (Trend Micro logo)
2. User screenshot revealed "TRENDLIFE" text in slide corner
3. Searched all small PNG files in template
4. Found `image3.png` containing full TrendLife logo with tagline
5. Cropped to remove tagline per user preference
6. Final logo confirmed and saved to assets directory
