# Confluence Plugin - Development Notes

Technical documentation for skill developers and contributors.

## Table of Contents

- [Architecture Decision: ADF v2 + Method 6](#architecture-decision-adf-v2--method-6)
- [Markdown Conversion Engine](#markdown-conversion-engine)
- [Technical Decisions](#technical-decisions)
- [Output Compatibility](#output-compatibility)
- [Testing](#testing)

---

## Architecture Decision: ADF v2 + Method 6

### Why ADF v2 as the Single Format Path

This plugin standardizes on **Atlassian Document Format (ADF)** via the **v2 REST API** for all
page content operations. Storage Format (XHTML) is **not deprecated** by Atlassian (the v2 API
supports both), but this plugin exclusively uses ADF for simplicity and consistency.

**Rationale:**

- ADF is Atlassian's modern, structured document format (JSON-based)
- The v2 REST API treats ADF as a first-class citizen
- JSON is easier to diff, patch, and programmatically manipulate than XHTML
- Eliminates the need to maintain dual format paths

### Component Roles

| Component | Role | When Used |
|-----------|------|-----------|
| `markdown_to_adf.py` | Markdown → ADF converter (mistune) | **New page upload only** |
| `upload_confluence.py` | Uploads ADF to Confluence via v2 REST API | Creating new pages or full page replacement |
| `adf_to_markdown.py` | ADF → readable Markdown renderer | **Display utility only** (showing ADF as readable text for Claude/humans) |
| `download_confluence.py` | Fetches ADF from v2 REST API, renders as Markdown | Viewing/reading page content |
| `mcp_json_diff_roundtrip.py` | ADF JSON diff/patch engine | **Roundtrip editing** (Method 6) |

### Why Method 6 (JSON Diff) Doesn't Need Markdown Intermediate

Method 6 roundtrip editing works as follows:

1. **GET** ADF JSON from v2 REST API
2. Claude reads a Markdown **display rendering** of the ADF (for human readability)
3. Claude's edits are applied as **JSON diff/patch operations** directly on the ADF structure
4. **PUT** modified ADF JSON back via v2 REST API

The Markdown shown to Claude in step 2 is **display-only** — it is not parsed back into ADF.
The actual data flow is ADF JSON in, ADF JSON out. This design preserves all macros, formatting,
and structural elements that would be lost in a Markdown round-trip conversion.

### What v1 API Endpoints Are Still Needed

While page content operations use the v2 REST API exclusively, two operations still require
**v1 REST API** endpoints because no v2 equivalents exist:

| Operation | v1 Endpoint | Why No v2 |
|-----------|------------|-----------|
| **Attachment upload** | `POST /rest/api/content/{id}/child/attachment` | v2 API does not support attachment upload |
| **Page width (full-width layout)** | `PUT /rest/api/content/{id}/property/content-appearance-published` | v2 API does not expose page properties |

### Known Confluence API Limitations

**`__confluenceMetadata` lost on every update:**
The v2 API GET does not return `__confluenceMetadata` fields (internal metadata
Confluence attaches to inline cards / page links for hover previews). Since GET
never provides them, every PUT drops them. Confluence regenerates them after save,
but this causes a "Formatting was changed" entry in version comparison even when
no actual content was modified. This is a Confluence API design limitation — there
is no workaround.

**Marks array reordering:**
Confluence normalizes the order of `marks` arrays on save (e.g.,
`[underline, strong, link]` → `[link, strong, underline]`). This plugin
pre-sorts marks alphabetically via `normalize_adf_marks()` in
`update_page_adf()` and `create_page_adf()` to prevent spurious diffs.

### MCP Upload: Use ADF, Not Markdown

When uploading via MCP (no API token), always use `contentFormat: "adf"` with
ADF JSON produced by `markdown_to_adf()`. Do **not** use `contentFormat: "markdown"`.

MCP's built-in Markdown→ADF conversion has rendering issues:

- Emoji lines (✅/❌/⚠️) are merged into a single paragraph instead of list items
- The `markdown_to_adf.py` pre-processor fixes this by converting emoji lines to
  list items and bare `[ ]` checkboxes to task lists before parsing

**Upload priority**: REST API v2 ADF (primary) → MCP ADF (fallback, no API token).

### What Was Removed

The following were removed as part of the ADF-only simplification:

- **`--legacy` flag** on `download_confluence.py` (v1 Storage Format download)
- **Storage Format upload path** (v1 `PUT` with XHTML body)
- **`ConfluenceStorageRenderer`** class (mistune renderer that produced XHTML Storage Format)
- **Dual upload path logic** (auto-detection between Storage v1 and ADF v2)

---

## Markdown Conversion Engine

### Why mistune 3.x instead of md2cf?

This plugin uses **mistune 3.x** (latest stable release) for the `markdown_to_adf.py` converter (used by
`upload_confluence.py` for **new page uploads**) instead of the older `md2cf` library.

**Key Reasons:**

| Aspect | md2cf | mistune 3.x (our choice) |
|--------|-------|-------------------------|
| **Last Update** | Uses mistune 0.8.4 (2017) | mistune 3.0+ (2024, actively maintained) |
| **Dependencies** | Complex dependency chain | Clean, minimal dependencies |
| **Build Issues** | PyYAML build failures on Python 3.12+ | No build issues |
| **Customization** | Limited | Full control via custom renderer |
| **Maintenance** | Stagnant | Active development |

### Implementation

The `markdown_to_adf.py` module uses mistune to parse Markdown and produce ADF JSON nodes.
It is used exclusively by `upload_confluence.py` for new page creation / full page replacement.

**Note**: The legacy `ConfluenceStorageRenderer` (which produced XHTML Storage Format) has been
removed. All new page uploads now go through the ADF path.

**Plugins enabled:**

- `table` - GitHub Flavored Markdown tables
- `strikethrough` - ~~text~~ support
- `url` - Auto-link detection

---

## Technical Decisions

### 1. Blockquote Rendering

**md2cf approach:**

```html
<blockquote><p>Quote text</p></blockquote>
```

**Our approach (better):**

```html
<ac:structured-macro ac:name="quote">
  <ac:rich-text-body><p>Quote text</p></ac:rich-text-body>
</ac:structured-macro>
```

**Why it's better:** Confluence UI renders native quote macros with proper styling (blue left border, background color).
HTML `<blockquote>` has minimal styling.

### 2. Image Tag Style

**md2cf approach:**

```html
<ac:image><ri:attachment ri:filename="image.png"></ri:attachment></ac:image>
```

**Our approach:**

```html
<ac:image><ri:attachment ri:filename="image.png" /></ac:image>
```

**Why it's different:** Self-closing XML tags (`/>`) are more modern and concise. Both are valid XML and functionally
identical in Confluence.

### 3. Code Block Formatting

**Minor differences:**

- md2cf: No trailing newline in CDATA: `]]></ac:plain-text-body>`
- Ours: Trailing newline: `\n]]></ac:plain-text-body>`

**Impact:** Negligible. Both render identically in Confluence.

---

## Output Compatibility

### Comparison Test Results

We conducted side-by-side comparison tests between md2cf (mistune 0.8.4) and our implementation (mistune 3.x).

**Test document includes:**

- Special characters (`<`, `>`, `&`, `"`)
- Images (local and external)
- Code blocks (with language syntax)
- Blockquotes
- Tables (with alignment)
- Nested lists
- Unicode characters (emoji, CJK)

**Results:**

| Feature | Compatibility | Notes |
|---------|--------------|-------|
| **Special Characters** | ✅ 100% identical | Proper escaping: `&lt;`, `&gt;`, `&amp;`, `&quot;` |
| **Tables** | ✅ 100% identical | Full structure with `<thead>`, `<tbody>`, alignment |
| **Images** | ✅ Functionally identical | XML style difference (self-closing tag) |
| **Code Blocks** | ✅ Functionally identical | Minor whitespace difference |
| **Blockquotes** | ⭐ Improved | We use Confluence macros (better rendering) |
| **Nested Lists** | ✅ Identical | Proper `<ul>`, `<ol>` nesting |
| **Unicode** | ✅ Identical | Emoji, Chinese, Japanese preserved |

### Summary

- **Core features:** 100% compatible with md2cf
- **Intentional improvements:** Blockquote rendering
- **No breaking changes:** All existing markdown documents work
- **Better maintainability:** Modern, actively developed dependencies

---

## Testing

### Test Suite

Tests live in `plugins/confluence/tests/` with three modules:

```bash
# Unit tests (offline, no credentials needed) — 129 tests
uv run --python 3.14 --with "pytest>=8.0" --with "mistune>=3.0.0" \
  --with "requests>=2.31.0" --with "python-dotenv>=1.0.0" \
  pytest plugins/confluence/tests/test_adf_to_markdown.py plugins/confluence/tests/test_roundtrip.py \
         plugins/confluence/tests/test_search_cql.py plugins/confluence/tests/test_read_page.py -v

# Integration tests (requires API credentials, creates/deletes real pages) — 5 tests
uv run --python 3.14 --with "pytest>=8.0" --with "mistune>=3.0.0" \
  --with "requests>=2.31.0" --with "python-dotenv>=1.0.0" \
  pytest plugins/confluence/tests/test_integration.py -v

# All tests together
uv run --python 3.14 --with "pytest>=8.0" --with "mistune>=3.0.0" \
  --with "requests>=2.31.0" --with "python-dotenv>=1.0.0" \
  pytest plugins/confluence/tests/ -v
```

| Module | Tests | Requires API | What it covers |
|--------|-------|--------------|----------------|
| `test_adf_to_markdown.py` | 44 | No | ADF → Markdown for all node types, marks, real 37-element fixture |
| `test_roundtrip.py` | 47 | No | ADF → MD → ADF fidelity, marker-free markdown, multiple-status regression, marks normalization |
| `test_search_cql.py` | 20 | No | CQL HTTP layer, result formatting, Rovo OAuth suggestion flow (confidence < 0.6) |
| `test_read_page.py` | 18 | No | URL/ID resolution, Markdown output, ADF JSON output, error paths |
| `test_integration.py` | 5 | Yes | Upload → Confluence → download → compare, page update, cleanup |

### Integration Test Details

Integration tests create child pages under
[SIP (Special Interest Projects)](https://trendmicro.atlassian.net/wiki/x/glWyAg)
and delete them after each test. They are automatically skipped when
`CONFLUENCE_URL`, `CONFLUENCE_USER`, or `CONFLUENCE_API_TOKEN` are missing.

### Test Fixture

The real ADF fixture (`tests/fixtures/macro_integration_test.json`) was captured
from a 37-element Confluence page (ID: 2354807244). To recapture:

```bash
uv run plugins/confluence/tests/capture_fixture.py
```

---

## Contributing

### Adding New Markdown Features

To add support for new Markdown features in `markdown_to_adf.py`:

1. **Add ADF node generation** in `markdown_to_adf.py`
2. **Enable mistune plugin** if needed for parsing
3. **Add unit tests** in `tests/test_adf_to_markdown.py` and `tests/test_roundtrip.py`
4. **Update documentation** in README.md

### ADF and Confluence Format References

Official documentation:

- [Atlassian Document Format (ADF)][adf] - JSON document structure
- [Confluence REST API v2][v2api] - API documentation
- [Confluence Storage Format][storage] - XHTML format reference
  (not used by this plugin, but useful for understanding Confluence internals)

[adf]: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/
[v2api]: https://developer.atlassian.com/cloud/confluence/rest/v2/intro/
[storage]: https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html

---

## FAQ for Developers

**Q: Why not use the Confluence REST API's built-in markdown conversion?**

A: The REST API doesn't have a markdown conversion endpoint. For new page uploads, we convert Markdown to ADF JSON
client-side via `markdown_to_adf.py` (mistune) before uploading via the v2 REST API.

**Q: Can I use other markdown parsers like markdown-it or CommonMark?**

A: Yes, but mistune is Python-native, fast, and has excellent plugin support. Since our upload scripts use Python (for
atlassian-python-api), mistune is the natural choice.

**Q: What about Mermaid/PlantUML diagrams?**

A: Convert diagrams to PNG/SVG first using external tools (mermaid-cli, plantuml), then reference with markdown image
syntax: `![diagram](./diagram.png)`. Our renderer will handle them as image attachments.

**Q: Does this work with Confluence Data Center (self-hosted)?**

A: Yes! The storage format is identical. Just set `cloud=False` in the Confluence client initialization and adjust the
URL to your self-hosted instance.

---

## License

This plugin is part of the claude-code-hubs project. See root LICENSE for details.
