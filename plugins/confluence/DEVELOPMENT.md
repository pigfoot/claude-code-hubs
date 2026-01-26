# Confluence Plugin - Development Notes

Technical documentation for skill developers and contributors.

## Table of Contents
- [Markdown Conversion Engine](#markdown-conversion-engine)
- [Technical Decisions](#technical-decisions)
- [Output Compatibility](#output-compatibility)
- [Testing](#testing)

---

## Markdown Conversion Engine

### Why mistune 3.x instead of md2cf?

This plugin uses **mistune 3.x** (latest stable release) with a custom `ConfluenceStorageRenderer` instead of the older `md2cf` library.

**Key Reasons:**

| Aspect | md2cf | mistune 3.x (our choice) |
|--------|-------|-------------------------|
| **Last Update** | Uses mistune 0.8.4 (2017) | mistune 3.0+ (2024, actively maintained) |
| **Dependencies** | Complex dependency chain | Clean, minimal dependencies |
| **Build Issues** | PyYAML build failures on Python 3.12+ | No build issues |
| **Customization** | Limited | Full control via custom renderer |
| **Maintenance** | Stagnant | Active development |

### Implementation

Our custom renderer extends `mistune.HTMLRenderer`:

```python
class ConfluenceStorageRenderer(mistune.HTMLRenderer):
    def image(self, alt, url, title=None):
        # Handles both local attachments and external URLs
        # Tracks local images for upload

    def block_code(self, code, info=None):
        # Renders as Confluence code macro with language syntax highlighting

    def block_quote(self, text):
        # Renders as Confluence quote macro (better UI rendering)

    def table(self, text):
        # Full table support with alignment
```

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

**Why it's better:** Confluence UI renders native quote macros with proper styling (blue left border, background color). HTML `<blockquote>` has minimal styling.

### 2. Image Tag Style

**md2cf approach:**
```html
<ac:image><ri:attachment ri:filename="image.png"></ri:attachment></ac:image>
```

**Our approach:**
```html
<ac:image><ri:attachment ri:filename="image.png" /></ac:image>
```

**Why it's different:** Self-closing XML tags (`/>`) are more modern and concise. Both are valid XML and functionally identical in Confluence.

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

### Running Comparison Tests

If you want to verify compatibility yourself:

```bash
# Install md2cf in a virtual environment
python3 -m venv test_env
source test_env/bin/activate
pip install md2cf

# Test with md2cf
python << 'EOF'
from md2cf.confluence_renderer import ConfluenceRenderer
import mistune

renderer = ConfluenceRenderer()
parser = mistune.Markdown(renderer=renderer)
print(parser(open('test.md').read()))
EOF

# Test with our implementation
uv run plugins/confluence/skills/confluence/scripts/upload_confluence.py test.md --dry-run
```

### Comprehensive Test Coverage

Our test suite verifies:

1. ✅ Special character escaping (`<script>`, `&`, quotes)
2. ✅ Nested lists (3+ levels deep)
3. ✅ Multiple images (local attachments tracked)
4. ✅ External image URLs
5. ✅ Code blocks with language syntax highlighting
6. ✅ Tables with column alignment
7. ✅ Strikethrough text
8. ✅ Blockquotes with Confluence macros
9. ✅ Auto-link detection
10. ✅ Unicode characters (emoji, CJK)

See test files:
- `/tmp/test_comprehensive.md` - Edge case test document
- `/tmp/test_full_conversion.py` - Automated validation

---

## Contributing

### Adding New Markdown Features

To add support for new markdown features:

1. **Add renderer method** in `ConfluenceStorageRenderer`:
   ```python
   def new_feature(self, text):
       # Convert to Confluence storage format
       return f'<confluence-markup>{text}</confluence-markup>\n'
   ```

2. **Enable plugin** if needed:
   ```python
   parser = mistune.create_markdown(
       renderer=renderer,
       plugins=['table', 'strikethrough', 'url', 'new-plugin']
   )
   ```

3. **Add test case** in comprehensive test suite

4. **Update documentation** in README.md

### Confluence Storage Format Reference

Official documentation:
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Structured Macros](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html#ConfluenceStorageFormat-StructuredMacros)
- [Rich Text Editor](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html#ConfluenceStorageFormat-RichTextEditor)

Common macros used:
- `ac:structured-macro ac:name="code"` - Code blocks with syntax highlighting
- `ac:structured-macro ac:name="quote"` - Blockquotes
- `ac:image` + `ri:attachment` - Image attachments
- `ac:image` + `ri:url` - External images

---

## FAQ for Developers

**Q: Why not use the Confluence REST API's built-in markdown conversion?**

A: The REST API doesn't have a markdown conversion endpoint. We must convert to storage format client-side before uploading.

**Q: Can I use other markdown parsers like markdown-it or CommonMark?**

A: Yes, but mistune is Python-native, fast, and has excellent plugin support. Since our upload scripts use Python (for atlassian-python-api), mistune is the natural choice.

**Q: What about Mermaid/PlantUML diagrams?**

A: Convert diagrams to PNG/SVG first using external tools (mermaid-cli, plantuml), then reference with markdown image syntax: `![diagram](./diagram.png)`. Our renderer will handle them as image attachments.

**Q: Does this work with Confluence Data Center (self-hosted)?**

A: Yes! The storage format is identical. Just set `cloud=False` in the Confluence client initialization and adjust the URL to your self-hosted instance.

---

## License

This plugin is part of the claude-code-hubs project. See root LICENSE for details.
