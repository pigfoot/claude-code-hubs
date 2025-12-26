# Brand Styles Reference

This file contains brand color palettes and style guidelines for generating on-brand imagery.

---

## Trend Micro

Corporate brand identity for Trend Micro, a global leader in cybersecurity solutions.

### Color Palette

**Primary Palette (Always First Choice)**

The primary palette should always be your first choice. Trend Red is the "hero" color and should be the first order of attention in any design.

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Trend Red** | `#d71920` | Hero/accent color - primary brand identifier |
| Trend Red 80% | `#de543b` | Tinted variations |
| Trend Red 60% | `#e67c60` | Tinted variations |
| Trend Red 40% | `#eda389` | Tinted variations |
| **Guardian Red** | `#6f0000` | Intensity and supporting elements |
| Black | `#000000` | Strong contrast |
| White | `#ffffff` | Clean backgrounds, text |

**Grays (K10-K90)**

Use for backgrounds, neutrals, and sophistication:

| Gray Level | Hex Code |
|------------|----------|
| K10 (lightest) | `#e6e7e8` |
| K20 | `#d1d3d4` |
| K30 | `#bcbec0` |
| K40 | `#a7a9ac` |
| K50 | `#939598` |
| K60 | `#808285` |
| K70 | `#6d6e71` |
| K80 | `#58595b` |
| K90 (darkest) | `#414042` |

**Secondary Palette (Use Sparingly)**

Only use for complex visuals (data visualization, diagrams). Maximum 2 secondary colors per design.

| Color Name | Hex Code | When to Use |
|------------|----------|-------------|
| Orange | `#f9a25e` | Warmth, alerts |
| Yellow | `#ffde6c` | Attention, highlights |
| Sage | `#c3d7a4` | Calm, growth |
| Green | `#73c167` | Success, security |
| Purple | `#9a4e9e` | Innovation |
| **Dark Blue** | `#005295` | Professionalism, trust |
| Light Blue | `#56a0d3` | Information |
| **Teal** | `#2cafa4` | Technology, modern |

**Recommended Secondary Colors:** Dark Blue and Teal are preferred when additional colors are needed beyond the primary palette.

### Style Guidelines

**When generating images with Trend Micro brand style:**

1. **Color Hierarchy:**
   - Trend Red (#d71920) must be the primary focus color
   - Guardian Red (#6f0000) for supporting elements and depth
   - Grays (#58595b to #e6e7e8) for backgrounds and neutrals
   - Black and white for strong contrast and clean visual identity

2. **Color Restrictions:**
   - Limit to primary palette whenever possible
   - If additional colors needed: use **only** Dark Blue (#005295) or Teal (#2cafa4)
   - Maximum 2 secondary colors in any design
   - Never mix more than 4-5 colors total

3. **Design Principles:**
   - Clean and professional aesthetic
   - Clear intent in color usage - every color should have a purpose
   - Strong hierarchy with Trend Red as the focal point
   - Use grays to create sophistication and balance

4. **Typical Use Cases:**
   - Product images: Trend Red as primary accent
   - Infographics: Trend Red for key metrics, grays for structure, Dark Blue/Teal for data categories
   - UI mockups: Trend Red for CTAs, Guardian Red for errors/warnings, grays for interface
   - Presentations: Trend Red headers, K80 gray body text, white backgrounds

### Prompt Template

When `style: "trend"` is detected, append this to the user's prompt:

```
Use Trend Micro brand colors:
- Primary: Trend Red (#d71920) as the hero/accent color - make it the first order of attention
- Guardian Red (#6f0000) for intensity and supporting elements
- Grays (#58595b to #e6e7e8) for backgrounds, neutrals, and sophistication
- Black and white for strong contrast and visual identity
- If additional colors needed: Dark Blue (#005295) or Teal (#2cafa4) only
Keep the design clean and professional with clear intent in color usage.
```

### Examples

**Good Usage:**
- Dashboard with Trend Red header, K80 gray sidebar, white content area, Dark Blue accent for data
- Product shot with Trend Red packaging, gray background, white highlights
- Infographic with Trend Red title, gray structure, Teal for primary data, Dark Blue for secondary data

**Poor Usage:**
- Using orange, yellow, and green together (too many secondary colors)
- Trend Red as a minor element instead of hero color
- Mixing all secondary colors in one design
- Using secondary colors without primary palette

---

## Adding New Brand Styles

To add new brands, follow this structure:

```markdown
## [Brand Name]

### Color Palette
[Primary, secondary, accent colors with hex codes]

### Style Guidelines
[Design principles, usage rules]

### Prompt Template
[Text to append when style is detected]
```
