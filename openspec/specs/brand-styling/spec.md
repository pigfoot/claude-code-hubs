# brand-styling Specification

## Purpose
TBD - created by archiving change 002-trendlife-style-improvement. Update Purpose after archive.
## Requirements
### Requirement: TrendLife Brand Style

The system SHALL support TrendLife brand style for AI-generated presentation slides with official brand colors and visual guidelines.

**ID:** `brand-styling-001`
**Priority:** High

#### Scenario: User requests TrendLife style explicitly

**Given:** User asks "Generate a title slide using TrendLife style"
**When:** Style detection processes the request
**Then:**
- TrendLife style is activated
- Brand color palette is injected into generation prompt
- TrendLife logo overlay is triggered
- Output follows TrendLife brand guidelines

#### Scenario: User requests TrendLife style via config

**Given:** User provides config with `{"style": "trendlife"}`
**When:** Batch generation processes the config
**Then:**
- Each slide with `style: "trendlife"` uses TrendLife brand
- Logo overlay is automatically applied
- Colors match TrendLife specification

#### Scenario: Natural language style detection

**Given:** User asks "Create slides for TrendLife presentation"
**When:** Style detection analyzes the prompt
**Then:**
- TrendLife style is inferred from context
- Brand styling is automatically applied
- User is notified: "Using TrendLife brand style"

**Rationale:** TrendLife is a distinct product line requiring specific brand identity separate from generic Trend Micro branding.

---

### Requirement: TrendLife Color Palette

The system SHALL inject TrendLife brand colors into image generation prompts when TrendLife style is detected.

**ID:** `brand-styling-002`
**Priority:** High

#### Scenario: Prompt enhancement with brand colors

**Given:** User prompt is "Create a data visualization slide"
**When:** TrendLife style is active
**Then:**
- Original prompt is enhanced with color guidance:
  ```
  Use TrendLife brand colors for Trend Micro presentations:
  - Primary: Trend Red (#D71920) for key elements and accents
  - Guardian Red (#6F0000) for supporting elements and depth
  - Neutral palette: Dark gray (#57585B), medium gray (#808285), light gray (#E7E6E6)
  - Black (#000000) and white (#FFFFFF) for contrast
  Keep the design clean, professional, and suitable for corporate presentations.
  DO NOT include any logos or brand text - these will be added separately.
  ```
- AI model receives enhanced prompt
- Generated image uses specified colors

**Color Specification:**

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Trend Red | #D71920 | Primary brand color, accents |
| Guardian Red | #6F0000 | Supporting elements, intensity |
| Trend Red 80% | #DE543B | Tinted variations |
| Trend Red 40% | #EDA389 | Light tinted variations |
| Dark Gray | #57585B | Text, structure |
| Medium Gray | #808285 | Secondary elements |
| Light Gray | #E7E6E6 | Backgrounds |
| Black | #000000 | High contrast |
| White | #FFFFFF | Clean backgrounds |

**Rationale:** Consistent color usage ensures brand recognition and professional appearance across all generated slides.

---

### Requirement: Style Trigger Keywords

The system SHALL recognize multiple trigger patterns for activating TrendLife style.

**ID:** `brand-styling-003`
**Priority:** Medium

#### Scenario: Explicit style parameter

**Given:** Config contains `"style": "trendlife"`
**When:** Generation processes the config
**Then:**
- TrendLife style is activated
- No ambiguity in style selection

#### Scenario: Natural language triggers

**Given:** User prompt contains any of:
- "trendlife style"
- "use trendlife"
- "trendlife brand"
- "trendlife presentation"

**When:** Style detection analyzes the prompt
**Then:**
- TrendLife style is activated
- Case-insensitive matching applied
- User is notified of style selection

#### Scenario: Default to no style

**Given:** User prompt contains no style keywords
**When:** Style detection runs
**Then:**
- No brand style is applied
- Generic professional style is used
- No logo overlay occurs

**Rationale:** Multiple trigger patterns improve user experience and reduce need for exact syntax.

---

### Requirement: Brand Style Documentation

The system SHALL maintain TrendLife brand guidelines in `references/brand-styles.md` for consistent style application.

**ID:** `brand-styling-004`
**Priority:** Medium

#### Scenario: Accessing brand guidelines

**Given:** Agent needs to apply TrendLife style
**When:** Agent reads `references/brand-styles.md`
**Then:**
- Complete color palette is documented
- Prompt template is available
- Logo positioning rules are defined
- Style trigger keywords are listed

**Documentation Structure:**
```markdown

