# Roundtrip Workflow (Read → Edit → Write)

## Overview

The **roundtrip workflow** enables reading existing Confluence pages, editing their content (typically with AI
assistance), and writing changes back to Confluence. This is more complex than the markdown-first approach due to format
conversion challenges.

## Important Limitations

⚠️ **Critical Warning:**
> "When the MCP fetches and updates pages, it loses macros (page properties, layouts, table of contents)"
>
> - [Confluence Community
>   Discussion](https://community.atlassian.com/forums/Confluence-questions/Confluence-MCP-amp-page-macros/qaq-p/3073340)

**What Gets Lost:**

- ❌ Confluence macros (TOC, page properties, layouts, etc.)
- ❌ Special formatting (info panels, expand blocks)
- ❌ Advanced table formatting
- ❌ Embedded diagrams (except Draw.io with metadata)

**Conversion Quality:**
> "Two-way conversion challenges: Tools exist for both directions, but the conversion isn't always lossless due to
> Confluence's custom macro elements"
>
> - [Confluence to Markdown Converter](https://github.com/highsource/confluence-to-markdown-converter)

## When to Use Roundtrip

✅ **Good Use Cases:**

- Simple text updates (add paragraphs, fix typos)
- List modifications (add/remove items)
- Code block updates
- Basic table edits
- Heading changes

❌ **Bad Use Cases:**

- Pages with complex macros
- Pages with custom layouts
- Status reports with live data
- Pages with page properties
- Collaborative documents in active use

## Implementation Methods

### Method 1: REST API + Storage Format (Recommended)

**Overview:**
Uses Confluence's native Storage Format (XHTML-based) for best preservation.

**Workflow:**

```
REST API v2 (read)
    ↓ body.storage (Confluence XHTML)
Confluence HTML → Markdown conversion
    ↓
Edit Markdown (Claude)
    ↓
Markdown → Confluence HTML conversion
    ↓ body.storage
REST API v2 (write)
```

**Tools:**

- **Read**: Confluence REST API v2
- **HTML → Markdown**:
  [confluence-to-markdown-converter](https://github.com/highsource/confluence-to-markdown-converter)
- **Markdown → HTML**: [md2cf](https://pypi.org/project/md2cf/) (uses mistune)

**Python Implementation:**

```python
#!/usr/bin/env python3
"""
scripts/confluence_roundtrip.py
Roundtrip workflow for editing Confluence pages
"""

import requests
from md2cf import md2cf
from confluence_to_markdown import ConfluenceToMarkdown

# Configuration
CONFLUENCE_URL = "https://your-site.atlassian.net"
API_TOKEN = "your_api_token"
USER_EMAIL = "your@email.com"

def read_page(page_id: str) -> tuple[str, dict]:
    """
    Read Confluence page content in storage format
    Returns: (markdown_content, page_metadata)
    """
    # Fetch page with storage format
    response = requests.get(
        f"{CONFLUENCE_URL}/wiki/api/v2/pages/{page_id}",
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        params={"body-format": "storage"}
    )
    response.raise_for_status()
    data = response.json()

    # Extract storage HTML
    storage_html = data["body"]["storage"]["value"]

    # Convert to Markdown
    converter = ConfluenceToMarkdown()
    markdown = converter.convert(storage_html)

    # Return markdown and metadata for writing back
    metadata = {
        "id": data["id"],
        "title": data["title"],
        "version": data["version"]["number"],
        "spaceId": data["spaceId"]
    }

    return markdown, metadata

def write_page(page_id: str, markdown: str, metadata: dict):
    """
    Write edited Markdown back to Confluence
    """
    # Convert Markdown to Confluence Storage Format
    storage_html = md2cf.convert_markdown(markdown)

    # Update page (increment version)
    response = requests.put(
        f"{CONFLUENCE_URL}/wiki/api/v2/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "id": page_id,
            "title": metadata["title"],
            "version": {
                "number": metadata["version"] + 1
            },
            "body": {
                "storage": {
                    "value": storage_html,
                    "representation": "storage"
                }
            }
        }
    )
    response.raise_for_status()
    return response.json()

# Usage example
if __name__ == "__main__":
    page_id = "123456789"

    # Read
    markdown, metadata = read_page(page_id)
    print(f"Page: {metadata['title']}")
    print(f"Original content:\n{markdown}\n")

    # Edit (could be done by Claude)
    edited_markdown = markdown + "\n\n## New Section\n\nAdded by automation."

    # Write back
    result = write_page(page_id, edited_markdown, metadata)
    print(f"Updated to version {result['version']['number']}")
```

**Pros:**

- ✅ Better format preservation (Storage Format is native)
- ✅ Mature tooling (md2cf is well-tested)
- ✅ Direct API control

**Cons:**

- ❌ Still loses macros
- ❌ Requires Python dependencies
- ❌ Need to manage API credentials

---

### Method 2: MCP + ADF Conversion

**Overview:**
Uses MCP tools with ADF (Atlassian Document Format) JSON conversion.

**Workflow:**

```
MCP getConfluencePage
    ↓ ADF JSON
ADF → Markdown conversion (atlas-doc-parser)
    ↓
Edit Markdown (Claude)
    ↓
Markdown → ADF conversion (marklassian)
    ↓ ADF JSON
MCP updateConfluencePage
```

**Tools:**

- **Read/Write**: Official Atlassian MCP or [@aashari](https://github.com/aashari/mcp-server-atlassian-confluence)
- **ADF → Markdown**: [atlas-doc-parser](https://atlas-doc-parser.readthedocs.io/) (Python)
- **Markdown → ADF**: [marklassian](https://marklassian.netlify.app/) (JavaScript/Node)

**Hybrid Python + Node Implementation:**

```python
# Python: ADF to Markdown
from atlas_doc_parser import parse_adf_to_markdown

def adf_to_markdown(adf_json: str) -> str:
    """Convert ADF JSON to Markdown"""
    return parse_adf_to_markdown(adf_json)
```

```javascript
// Node.js: Markdown to ADF
const { markdownToAdf } = require('marklassian');

function markdownToAdf(markdown) {
  return markdownToAdf(markdown);
}
```

**Pros:**

- ✅ Uses existing MCP infrastructure
- ✅ OAuth authentication (simpler)
- ✅ No need for separate API credentials

**Cons:**

- ❌ Requires both Python AND JavaScript
- ❌ More complex toolchain
- ❌ ADF conversion may be less mature than Storage Format
- ❌ Still loses macros

---

### Method 3: Pragmatic Hybrid (Quick Implementation)

**Overview:**
For simple edits, let Claude work directly with ADF JSON structure.

**Workflow:**

```
MCP getConfluencePage
    ↓ ADF JSON (as text)
Claude edits JSON directly
    ↓ Modified ADF JSON
MCP updateConfluencePage
```

**Implementation:**

```python
def quick_edit_page(page_id: str, edit_instruction: str):
    """
    Quick edit using MCP with Claude understanding ADF structure
    """
    # 1. Read page (returns ADF JSON string)
    result = mcp_tool_call("mcp__plugin_confluence_atlassian__getConfluencePage", {
        "cloudId": CLOUD_ID,
        "pageId": page_id,
        "contentFormat": "adf"  # Actually returns ADF regardless
    })

    adf_content = result["body"]  # JSON string

    # 2. Let Claude edit the ADF structure directly
    # Claude can understand and modify JSON structures
    prompt = f"""
    Edit this Confluence page ADF JSON according to: {edit_instruction}

    Current ADF:
    {adf_content}

    Return the modified ADF JSON only.
    """

    edited_adf = call_claude(prompt)

    # 3. Write back
    mcp_tool_call("mcp__plugin_confluence_atlassian__updateConfluencePage", {
        "cloudId": CLOUD_ID,
        "pageId": page_id,
        "body": edited_adf,
        "contentFormat": "adf"
    })
```

**Pros:**

- ✅ Fastest to implement
- ✅ No conversion libraries needed
- ✅ Uses existing MCP setup

**Cons:**

- ❌ Claude must understand ADF structure
- ❌ Error-prone for complex edits
- ❌ Still loses macros

**Best For:**

- Adding simple text paragraphs
- Updating list items
- Changing headings
- Quick fixes

---

## Comparison Table

| Method | Setup Complexity | Conversion Quality | Macro Preservation | Best For |
|--------|-----------------|-------------------|-------------------|----------|
| **REST API + Storage** | Medium | ⭐⭐⭐⭐ | ❌ | Production use, complex edits |
| **MCP + ADF** | High | ⭐⭐⭐ | ❌ | MCP-first architecture |
| **Pragmatic Hybrid** | Low | ⭐⭐ | ❌ | Simple edits, prototyping |

---

## Best Practices

### 1. Check Page Before Editing

```python
def is_safe_to_edit(page_id: str) -> tuple[bool, str]:
    """
    Check if page is safe for roundtrip editing
    Returns: (is_safe, reason)
    """
    page = get_page_metadata(page_id)

    # Check for macros
    if has_macros(page):
        return False, "Page contains macros that will be lost"

    # Check for custom layouts
    if has_custom_layout(page):
        return False, "Page has custom layout"

    # Check page properties
    if has_page_properties(page):
        return False, "Page has page properties"

    return True, "Safe to edit"
```

### 2. Create Backups

```python
def backup_page_before_edit(page_id: str):
    """Create a copy before editing"""
    original = get_page(page_id)

    # Create backup in same space
    create_page(
        title=f"{original['title']} (Backup {datetime.now()})",
        space_id=original['spaceId'],
        content=original['body']
    )
```

### 3. Validate After Write

```python
def validate_roundtrip(original_markdown: str, page_id: str) -> bool:
    """
    Validate that the roundtrip didn't lose critical content
    """
    # Read back the page
    new_markdown, _ = read_page(page_id)

    # Check for major differences
    original_lines = set(original_markdown.split('\n'))
    new_lines = set(new_markdown.split('\n'))

    # Calculate similarity
    similarity = len(original_lines & new_lines) / len(original_lines)

    if similarity < 0.95:
        print(f"Warning: Only {similarity*100:.1f}% similarity after roundtrip")
        return False

    return True
```

### 4. Use Version Comments

```python
def write_page_with_comment(page_id: str, markdown: str, metadata: dict, comment: str):
    """Write page with version comment for audit trail"""
    # ... (same as write_page but add version message)
    json={
        # ...
        "version": {
            "number": metadata["version"] + 1,
            "message": f"Automated edit: {comment}"
        }
    }
```

---

## Common Issues

### Issue: Macros Disappear After Edit

**Problem:** Page macros (TOC, info panels, etc.) are lost

**Solutions:**

1. **Don't use roundtrip** - Edit in Confluence web UI instead
2. **Use raw ADF blocks** in Markdown (if supported by converter)
3. **Warn users** before editing pages with macros

### Issue: Tables Lose Formatting

**Problem:** Complex table formatting doesn't survive conversion

**Solution:** Use simple Markdown tables only

```markdown
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
```

### Issue: Version Conflicts

**Problem:** Page was edited by someone else between read and write

**Solution:** Check version number and retry

```python
try:
    write_page(page_id, markdown, metadata)
except VersionConflictError:
    # Fetch latest version and retry
    markdown, metadata = read_page(page_id)
    # Re-apply edits...
```

### Issue: Conversion Encoding Errors

**Problem:** Special characters or emojis cause errors

**Solution:** Ensure UTF-8 encoding throughout

```python
requests.post(..., json=data)  # Not data=json.dumps(data)
```

---

## Decision Tree: Which Method?

```
┌─────────────────────────────────────┐
│  Does page have macros/properties?  │
└────────────┬───────────┬────────────┘
             │           │
            Yes          No
             │           │
             ▼           ▼
    ┌──────────────┐  ┌──────────────────┐
    │ Use Web UI   │  │  Roundtrip OK    │
    │ Don't script │  └────────┬─────────┘
    └──────────────┘           │
                               ▼
                    ┌──────────────────────┐
                    │  Need production-    │
                    │  quality conversion? │
                    └───┬──────────┬───────┘
                       Yes        No
                        │          │
                        ▼          ▼
                ┌──────────────┐  ┌──────────────┐
                │  Method 1:   │  │  Method 3:   │
                │  REST API +  │  │  Pragmatic   │
                │  Storage     │  │  Hybrid      │
                └──────────────┘  └──────────────┘
```

---

## Future Improvements

### Option: Selective Macro Preservation

Some converters support preserving specific macros:

```python
# Preserve code blocks as Confluence code macro
converter_options = {
    "preserve_code_macro": True,
    "preserve_info_panels": True
}
```

### Option: Hybrid Edit Mode

Edit in Markdown but preserve macro blocks:

```markdown
## My Section

This is editable text.

<!-- Preserve: Confluence Macro -->
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>This info panel is preserved</p>
  </ac:rich-text-body>
</ac:structured-macro>
<!-- End Preserve -->

More editable text.
```

---

## References

- [Confluence to Markdown Converter](https://github.com/highsource/confluence-to-markdown-converter)
- [md2cf Python Package](https://pypi.org/project/md2cf/)
- [atlas-doc-parser Documentation](https://atlas-doc-parser.readthedocs.io/)
- [marklassian - Markdown to ADF](https://marklassian.netlify.app/)
- [Confluence Storage Format
  Specification](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Confluence Community: MCP &
  Macros](https://community.atlassian.com/forums/Confluence-questions/Confluence-MCP-amp-page-macros/qaq-p/3073340)

## Related Documentation

- [Markdown-First Workflow](./markdown-first-workflow.md) - Recommended for new pages
- [CQL Reference](./cql_reference.md) - For searching pages before editing
- [Troubleshooting](./troubleshooting.md) - Common issues
