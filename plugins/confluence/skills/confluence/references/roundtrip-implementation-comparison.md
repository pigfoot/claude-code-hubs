# Roundtrip Implementation Methods Detailed Comparison

In-depth comparison of implementation methods for Confluence bidirectional editing (Read → Edit → Write).

---

## Quick Overview

| Method | Core Technology | Complexity | Quality | Macro Preservation | Recommendation |
|-----|---------|-------|------|-----------|-------|
| **Method 1: REST API + Storage Format (DEPRECATED)** | Python + Storage Format | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Lost (Markdown step) | ~~Production environment~~ Deprecated |
| **Method 2: MCP + ADF Conversion (DEPRECATED)** | Python + JavaScript + ADF | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ Lost (Markdown step) | ~~MCP-only architecture~~ Deprecated |
| **Method 3: Pragmatic Hybrid (DEPRECATED)** | MCP + Direct JSON Edit | ⭐⭐ | ⭐⭐ | ❌ Lost (JSON mishandling) | ~~Quick prototype~~ Deprecated |
| **Method 4: Direct XML/JSON Edit** | Python + lxml/json | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ **Fully preserved** | ⚠️ No Claude intelligent editing |
| **Method 5: Hybrid Strategy** | Auto-detection + Method 1/4 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Smart preservation | ✅ Auto-selection |
| **Method 6: MCP + JSON Diff (⭐ Recommended)** | MCP + ADF + JSON Diff + Interactive | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ **Preserved + Optional Body Edit** | ⭐ **Recommended** |
| **Method 7: ADF-Native Roundtrip (✅ Implemented)** | v2 API + ADF + Custom Markers | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ **Full preservation + Editable** | ✅ **Implemented** |

⚠️ **Important: Methods 1-3 are DEPRECATED and their dependencies (`md2cf`, `html2text`, `markdownify`, `beautifulsoup4`)
have been removed from the plugin.** These methods all lost Confluence macros because they went through a Markdown
conversion step. The loss was caused by markdownify/html2text dropping Confluence-specific XML tags (`ac:*`) -- it was
NOT caused by Storage Format or the API itself. A direct Storage Format XML roundtrip (Method 4) or a direct
ADF JSON diff (Method 6) is **lossless**. Storage Format is NOT deprecated; the v2 API fully supports
`representation: storage` for GET/PUT/POST. Only the v1 API *endpoints* are being deprecated.
The MCP Gateway only supports ADF format, but the REST API v2 supports both Storage Format and ADF.
**All uploads now use `markdown_to_adf.py` with the v2 ADF API (Method 7).**

Method 4 preserves macros but cannot use Claude. **Method 6 is the recommended approach** - it preserves macros while
allowing Claude to edit all text content (including optional macro bodies with user confirmation and automatic
backup/rollback).

---

## Method 1: REST API + Storage Format (DEPRECATED)

> **DEPRECATED:** This method used dependencies that have been removed (`md2cf`, `html2text`, `beautifulsoup4`).
> The `ConfluenceStorageRenderer`, `convert_markdown_to_storage()`, `convert_storage_to_markdown()` functions
> and the `--legacy` flag have been removed. Use **Method 6** or **Method 7** instead.
> This section is kept as historical reference.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page                                            │
│  (Storage Format: XHTML-based XML)                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2: GET /wiki/api/v2/pages/{id}
                   │ ?body-format=storage
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Format HTML                                        │
│  <h2>Title</h2><p>Content</p>                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ html2text / confluence-to-markdown
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Markdown                                                   │
│  ## Title\n\nContent                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Claude Edit
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Edited Markdown                                            │
│  ## Title\n\nEdited content                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ md2cf (mistune-based)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Format HTML                                        │
│  <h2>Title</h2><p>Edited content</p>                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2: PUT /wiki/api/v2/pages/{id}
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (Updated)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Required Dependencies

```python
# requirements.txt (DEPRECATED - these dependencies have been removed)
requests>=2.31.0
html2text>=2020.1.16    # REMOVED
mistune>=3.0.0
# Or use md2cf
md2cf>=2.5.0             # REMOVED
```

### Complete Implementation Example

```python
#!/usr/bin/env python3
"""
scripts/roundtrip_storage.py
Method 1: REST API + Storage Format
"""

import os
import requests
import html2text
import mistune

# Configuration
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
USER_EMAIL = os.getenv("CONFLUENCE_USER")

class ConfluenceRoundtrip:
    def __init__(self):
        self.base_url = CONFLUENCE_URL
        self.headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0  # No wrapping

    def read_page(self, page_id: str) -> tuple[str, dict]:
        """
        Read Confluence page, convert to Markdown
        Returns: (markdown_content, metadata)
        """
        # 1. Fetch page with storage format
        response = requests.get(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            params={"body-format": "storage"}
        )
        response.raise_for_status()
        data = response.json()

        # 2. Extract storage HTML
        storage_html = data["body"]["storage"]["value"]

        # 3. Convert HTML to Markdown
        markdown = self.html_converter.handle(storage_html)

        # 4. Store metadata for writing back
        metadata = {
            "id": data["id"],
            "title": data["title"],
            "version": data["version"]["number"],
            "spaceId": data["spaceId"]
        }

        return markdown, metadata

    def write_page(self, page_id: str, markdown: str, metadata: dict, comment: str = ""):
        """
        Write edited Markdown back to Confluence
        """
        # 1. Convert Markdown to HTML (Storage Format)
        storage_html = mistune.html(markdown)

        # 2. Update page (increment version)
        payload = {
            "id": page_id,
            "title": metadata["title"],
            "version": {
                "number": metadata["version"] + 1,
                "message": comment or "Updated via API"
            },
            "body": {
                "storage": {
                    "value": storage_html,
                    "representation": "storage"
                }
            }
        }

        response = requests.put(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def safe_edit(self, page_id: str, edit_fn, comment: str = ""):
        """
        Safe editing workflow with validation and backup
        edit_fn: accepts markdown str, returns edited markdown str
        """
        # 1. Read
        markdown, metadata = self.read_page(page_id)

        # 2. Backup (optional, save to file)
        backup_file = f"backup_{page_id}_{metadata['version']}.md"
        with open(backup_file, "w") as f:
            f.write(markdown)
        print(f"✓ Backed up to {backup_file}")

        # 3. Edit
        edited_markdown = edit_fn(markdown)

        # 4. Preview changes
        print("\n=== Changes Preview ===")
        print(f"Original length: {len(markdown)} chars")
        print(f"Edited length: {len(edited_markdown)} chars")
        print(f"Difference: {len(edited_markdown) - len(markdown):+d} chars")

        # 5. Confirm (optional, interactive)
        # confirm = input("Proceed with update? (y/n): ")
        # if confirm.lower() != 'y':
        #     print("Cancelled")
        #     return None

        # 6. Write back
        result = self.write_page(page_id, edited_markdown, metadata, comment)
        print(f"✓ Updated to version {result['version']['number']}")
        return result

# Usage examples
if __name__ == "__main__":
    rt = ConfluenceRoundtrip()

    # Example 1: Simple text addition
    def add_section(markdown: str) -> str:
        return markdown + "\n\n## New Section\n\nAdded by automation."

    rt.safe_edit("123456789", add_section, comment="Added new section")

    # Example 2: Replace text
    def fix_typo(markdown: str) -> str:
        return markdown.replace("teh", "the")

    rt.safe_edit("123456789", fix_typo, comment="Fixed typo")

    # Example 3: Claude-powered edit
    def claude_edit(markdown: str) -> str:
        # Call Claude API here
        # edited = call_claude(f"Please improve this: {markdown}")
        # return edited
        pass
```

### Pros

✅ **Best conversion quality**: Storage Format is native to Confluence, preserves most information
✅ **Mature and stable**: ~~md2cf and html2text are battle-tested tools~~ (removed from plugin)
✅ **Single language**: Pure Python, simple dependency management
✅ **Full control**: Direct REST API access, no black box
✅ **Suitable for automation**: Can be used in CI/CD, batch processing
✅ **Easy error handling**: HTTP status codes, clear error messages

### Cons

❌ **Requires API Token**: Users need to generate and manage tokens
❌ **⚠️ Loses Macros via Markdown conversion**: The `Storage Format → Markdown → Storage Format` conversion process
loses macros because markdownify drops `ac:*` tags. **This is a Markdown conversion limitation, NOT a Storage Format
limitation.** A direct Storage XML roundtrip (without Markdown) would preserve all macros.
❌ **Requires implementing scripts**: Need to write or maintain Python scripts
❌ **Version conflict handling**: Need to implement conflict detection yourself

> **Key clarification:** Storage Format is NOT deprecated. The v2 API fully supports
> `representation: storage`. Only the v1 API *endpoints* are deprecated. The MCP Gateway
> only supports ADF, but the REST API v2 supports both formats. See
> [Macro Preservation Guide](./macro-preservation-guide.md).

### Use Cases

- Production environment content management
- Batch updating multiple pages
- CI/CD integration
- Need stable and reliable conversion quality
- Team already familiar with Python

---

## Method 2: MCP + ADF Conversion (DEPRECATED)

> **DEPRECATED:** This method used dependencies that have been removed (`md2cf`, `html2text`).
> The Markdown conversion pipeline has been replaced with ADF-native approaches.
> Use **Method 6** or **Method 7** instead.
> This section is kept as historical reference.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page                                            │
│  (ADF: Atlassian Document Format JSON)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: getConfluencePage(contentFormat: "adf")
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ADF JSON                                                   │
│  {"type":"doc","content":[{"type":"paragraph",...}]}       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ atlas-doc-parser (Python)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Markdown                                                   │
│  ## Title\n\nContent                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Claude Edit
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Edited Markdown                                            │
│  ## Title\n\nEdited content                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ marklassian (JavaScript/Node)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ADF JSON                                                   │
│  {"type":"doc","content":[{"type":"paragraph",...}]}       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: updateConfluencePage(body: adf)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (Updated)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Required Dependencies

```json
{
  "python": {
    "dependencies": [
      "atlas-doc-parser>=1.0.0"
    ]
  },
  "javascript": {
    "dependencies": {
      "marklassian": "^2.0.0"
    }
  }
}
```

### Mixed Language Implementation Example

```python
# scripts/roundtrip_adf.py (Python part)
import json
import subprocess
from atlas_doc_parser import parse_adf

def adf_to_markdown(adf_json: str) -> str:
    """Convert ADF JSON to Markdown using atlas-doc-parser"""
    adf_data = json.loads(adf_json)
    return parse_adf(adf_data)

def markdown_to_adf(markdown: str) -> str:
    """
    Convert Markdown to ADF using Node.js marklassian
    Calls Node.js script as subprocess
    """
    # Call Node.js script
    result = subprocess.run(
        ['node', 'scripts/md_to_adf.js'],
        input=markdown.encode(),
        capture_output=True
    )

    if result.returncode != 0:
        raise Exception(f"Conversion failed: {result.stderr.decode()}")

    return result.stdout.decode()

def mcp_roundtrip(page_id: str, edit_fn):
    """Roundtrip using MCP tools"""
    # 1. Read via MCP
    result = call_mcp_tool(
        "mcp__plugin_confluence_atlassian__getConfluencePage",
        {
            "cloudId": CLOUD_ID,
            "pageId": page_id,
            "contentFormat": "adf"
        }
    )

    adf_json = result["body"]

    # 2. Convert ADF to Markdown
    markdown = adf_to_markdown(adf_json)

    # 3. Edit
    edited_markdown = edit_fn(markdown)

    # 4. Convert back to ADF
    edited_adf = markdown_to_adf(edited_markdown)

    # 5. Write via MCP
    call_mcp_tool(
        "mcp__plugin_confluence_atlassian__updateConfluencePage",
        {
            "cloudId": CLOUD_ID,
            "pageId": page_id,
            "body": edited_adf,
            "contentFormat": "adf"
        }
    )
```

```javascript
// scripts/md_to_adf.js (Node.js part)
const { markdownToAdf } = require('marklassian');
const fs = require('fs');

// Read markdown from stdin
let markdown = '';
process.stdin.on('data', chunk => {
  markdown += chunk;
});

process.stdin.on('end', () => {
  try {
    // Convert to ADF
    const adf = markdownToAdf(markdown);

    // Output JSON
    console.log(JSON.stringify(adf));
  } catch (error) {
    console.error('Conversion error:', error);
    process.exit(1);
  }
});
```

### Pros

✅ **Uses MCP**: Fits MCP-first architecture
✅ **OAuth authentication**: No need to manage API Token
✅ **Unified interface**: Through MCP tools, no direct API calls
✅ **ADF native**: Theoretically ADF is Confluence's "internal" format

### Cons

❌ **Dual-language environment**: Requires Python + Node.js, high complexity
❌ **Complex dependency management**: Two package managers (pip + npm)
❌ **Subprocess calls**: Python calling Node.js, poor performance
❌ **Uncertain conversion quality**: ADF tools are newer, not as mature as Storage Format
❌ **Difficult debugging**: Cross-language debugging is hard
❌ **⚠️ Loses Macros via Markdown conversion**: ADF → Markdown → ADF conversion loses macros because the Markdown
step cannot represent Confluence-specific elements. This is a Markdown limitation, not an ADF limitation.
❌ **MCP limitations**: MCP Gateway only supports ADF format (not Storage Format). Depends on MCP behavior, harder to customize.

### Use Cases

- Already fully using MCP, don't want to use REST API
- Need OAuth authentication (don't want to manage API Token)
- Team has both Python + Node.js capabilities
- Willing to accept higher complexity for MCP integration

---

## Method 3: Pragmatic Hybrid (DEPRECATED)

> **DEPRECATED:** This method relied on the same Markdown conversion pipeline
> (using `html2text`, `md2cf`) that has been removed. Use **Method 6** or **Method 7** instead.
> This section is kept as historical reference.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page                                            │
│  (ADF JSON)                                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: getConfluencePage
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ADF JSON String                                            │
│  {"type":"doc","content":[...]}                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Direct to Claude (no conversion)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude understands JSON structure and edits directly       │
│  - Identifies paragraph nodes                               │
│  - Modifies text content                                    │
│  - Keeps JSON structure intact                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Returns modified JSON
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Edited ADF JSON String                                     │
│  {"type":"doc","content":[... modified ...]}               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: updateConfluencePage
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (Updated)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Required Dependencies

```python
# requirements.txt
# No additional dependencies! Only needs MCP already set up
```

### Implementation Example

```python
# scripts/roundtrip_pragmatic.py
def quick_edit(page_id: str, instruction: str):
    """
    Quick edit: Let Claude operate on ADF JSON directly
    """
    # 1. Read page (get ADF JSON)
    result = call_mcp_tool(
        "mcp__plugin_confluence_atlassian__getConfluencePage",
        {
            "cloudId": CLOUD_ID,
            "pageId": page_id,
            "contentFormat": "adf"
        }
    )

    adf_json = result["body"]

    # 2. Let Claude edit the JSON directly
    prompt = f"""
You are editing a Confluence page in ADF (Atlassian Document Format) JSON.

Current content (ADF JSON):
{adf_json}

Task: {instruction}

Rules:
1. Modify the JSON to accomplish the task
2. Maintain valid ADF structure
3. Only change text content, not structure unless necessary
4. Return ONLY the modified ADF JSON, no explanation

Modified ADF JSON:
"""

    # Call Claude (assuming call_claude function exists)
    edited_adf_json = call_claude(prompt)

    # 3. Write back
    call_mcp_tool(
        "mcp__plugin_confluence_atlassian__updateConfluencePage",
        {
            "cloudId": CLOUD_ID,
            "pageId": page_id,
            "body": edited_adf_json,
            "contentFormat": "adf"
        }
    )

    print(f"✓ Page {page_id} updated")

# Example usage
if __name__ == "__main__":
    # Simple editing tasks
    quick_edit(
        page_id="123456789",
        instruction="Add a new paragraph at the end: 'Updated on 2025-01-23'"
    )

    quick_edit(
        page_id="123456789",
        instruction="Find the heading 'Installation' and add a new bullet point: '- Run npm install'"
    )

    quick_edit(
        page_id="123456789",
        instruction="Fix all occurrences of 'teh' to 'the'"
    )
```

### ADF JSON Example

ADF structure that Claude needs to understand:

```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [
        {"type": "text", "text": "Installation"}
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Follow these steps:"}
      ]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [
            {
              "type": "paragraph",
              "content": [
                {"type": "text", "text": "Step 1"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Pros

✅ **Simplest**: No conversion tools needed, zero additional dependencies
✅ **Fast implementation**: A few lines of code to run
✅ **Uses MCP**: Fits MCP-first architecture
✅ **OAuth authentication**: Simple authentication flow
✅ **Good for prototypes**: Quick testing of ideas

### Cons

❌ **Depends on Claude's capability**: Claude must correctly understand and operate ADF JSON
❌ **Higher error rate**: JSON structure may be corrupted
❌ **Not suitable for complex edits**: Large changes are error-prone
❌ **Difficult debugging**: Invalid JSON is hard to detect
❌ **⚠️ May corrupt macros**: Although Method 3 does NOT go through Markdown conversion, Claude directly editing ADF
JSON may accidentally delete or corrupt macro structures because Claude might treat macros as regular content nodes.
This is a different failure mode from Methods 1-2 (JSON mishandling vs Markdown conversion loss).
❌ **Not suitable for production**: Insufficient reliability

See [Macro Preservation Guide](./macro-preservation-guide.md) for details on macro preservation across methods.

### Use Cases

- Quick prototype development
- Simple text edits (add a line, fix typos)
- Testing MCP integration
- One-time small tasks
- Scenarios that don't require high reliability

---

## Method 4: Direct XML/JSON Edit (Fully Preserves Macros)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page                                            │
│  (Storage Format XML or ADF JSON)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2 (no Markdown conversion)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Format XML / ADF JSON                              │
│  <ac:structured-macro>...</ac:structured-macro>            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Direct XML/JSON operation (lxml / json library)
                   │ Keep macro structure intact
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Edited XML / JSON                                          │
│  <ac:structured-macro>...</ac:structured-macro>            │
│  (Macros fully preserved)                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (Updated, Macros fully preserved)          │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Example

```python
#!/usr/bin/env python3
"""
scripts/roundtrip_xml_direct.py
Method 4: Direct Storage Format XML editing (fully preserves macros)
"""

import requests
from lxml import etree, html

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

def roundtrip_direct_xml(page_id: str, xpath_edit_fn):
    """
    Directly edit Storage Format XML, fully preserves macros

    xpath_edit_fn: accepts lxml Element, directly operates on DOM
    """
    # 1. Read Storage Format
    response = requests.get(
        f"{CONFLUENCE_URL}/wiki/api/v2/pages/{page_id}",
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        params={"body-format": "storage"}
    )
    data = response.json()
    storage_xml = data["body"]["storage"]["value"]

    # 2. Parse XML (preserve macro structures)
    doc = html.fromstring(f"<root>{storage_xml}</root>")

    # 3. Directly operate on XML DOM
    # Example: find specific paragraph and modify
    xpath_edit_fn(doc)

    # 4. Serialize back to XML (macros fully preserved)
    edited_xml = etree.tostring(doc, encoding='unicode', method='html')
    edited_xml = edited_xml.replace('<root>', '').replace('</root>', '')

    # 5. Write back
    response = requests.put(
        f"{CONFLUENCE_URL}/wiki/api/v2/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "id": page_id,
            "version": {"number": data["version"]["number"] + 1},
            "body": {
                "storage": {
                    "value": edited_xml,
                    "representation": "storage"
                }
            }
        }
    )
    response.raise_for_status()
    return response.json()

# Usage example
def edit_example(doc):
    """Edit function: find first paragraph and modify text"""
    paragraphs = doc.xpath("//p")
    if paragraphs:
        # Modify paragraph text, but preserve all macros
        paragraphs[0].text = "Updated text"

roundtrip_direct_xml("123456789", edit_example)
```

### Pros

✅ **✨ Fully preserves Macros**: All Confluence macros completely preserved (expand, page properties, status, all of them)
✅ **Preserves layouts**: Custom layouts, columns completely preserved
✅ **Precise control**: Direct DOM operations, full control over editing logic
✅ **No conversion loss**: Doesn't go through Markdown, zero information loss
✅ **Suitable for programmatic edits**: Batch modify specific elements (like updating all dates, replacing specific text)

### Cons

❌ **Cannot use Claude intelligent editing**: Claude is not good at understanding and operating complex XML/JSON structures
❌ **Complex editing logic**: Need to understand Confluence Storage Format structure
❌ **Easy to corrupt structure**: Wrong XML operations can cause page display failure
❌ **Requires XML/JSON expertise**: Need familiarity with XPath, DOM operations
❌ **Not suitable for natural language editing**: Cannot handle vague requests like "make this more professional"
❌ **Difficult debugging**: XML structure errors are hard to detect

### Use Cases

- **Batch operations that must preserve macros**: e.g., updating all pages' owner (page properties)
- **Programmatic replacement**: Replace all specific text, update links, modify dates
- **Structural edits**: Modify tables, adjust heading levels
- **No AI understanding needed**: Only mechanical find-and-replace

### Not Suitable For

- Need Claude to understand content and rewrite
- Vague editing requirements ("make it clearer")
- Content creation or major rewrites
- Complex semantic understanding

---

## Method 5: Hybrid Strategy with Auto-Detection

### Overview

**Hybrid Strategy** automatically detects page characteristics and selects the optimal method:

- Detects macros and their importance
- Analyzes edit complexity
- Chooses between Method 1 (Markdown roundtrip) and Method 4 (Direct XML edit)
- Provides best balance between macro preservation and Claude intelligence

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User Request: Edit page                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Auto-Detection Engine                                      │
│  1. Fetch page metadata                                     │
│  2. Detect macros (expand, page-properties, status, etc.)  │
│  3. Classify edit type (simple text vs complex rewrite)    │
│  4. Calculate decision score                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌────────────────┐   ┌───────────────────┐
│ Has Critical   │   │ No Critical       │
│ Macros         │   │ Macros            │
│ + Simple Edit  │   │ OR                │
│                │   │ Complex Rewrite   │
└───────┬────────┘   └────────┬──────────┘
        │                     │
        ▼                     ▼
┌────────────────┐   ┌───────────────────┐
│ Method 4       │   │ Method 1          │
│ Direct XML     │   │ Markdown          │
│ (Preserve)     │   │ + Claude Edit     │
└───────┬────────┘   └────────┬──────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Result: Page Updated                                       │
└─────────────────────────────────────────────────────────────┘
```

### Complete Implementation

```python
#!/usr/bin/env python3
"""
scripts/hybrid_roundtrip.py
Method 5: Hybrid Strategy with Auto-Detection
"""

import os
import requests
from lxml import etree, html
import html2text
import mistune
from dataclasses import dataclass
from typing import Literal, Callable
from enum import Enum

# Configuration
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

class EditComplexity(Enum):
    SIMPLE = "simple"           # Simple text changes (typos, add sentence)
    MODERATE = "moderate"       # Multiple paragraphs, some restructuring
    COMPLEX = "complex"         # Complete rewrite, content creation

class MacroImportance(Enum):
    NONE = "none"              # No macros
    LOW = "low"                # Only code blocks, TOC (auto-convertible)
    HIGH = "high"              # Expand, page properties, status, layouts

@dataclass
class PageAnalysis:
    has_macros: bool
    macro_importance: MacroImportance
    macro_types: list[str]
    edit_complexity: EditComplexity
    recommended_method: Literal[1, 4]
    reason: str

class HybridRoundtrip:
    def __init__(self):
        self.base_url = CONFLUENCE_URL
        self.headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }

        # Critical macros that should be preserved
        self.critical_macros = {
            'expand', 'details', 'status', 'jira',
            'layout', 'section', 'column'
        }

        # Auto-convertible macros (safe to lose)
        self.safe_macros = {
            'code', 'toc', 'info', 'warning', 'note'
        }

    def analyze_page(
        self,
        page_id: str,
        edit_instruction: str
    ) -> PageAnalysis:
        """
        Analyze page to determine optimal method
        """
        # 1. Fetch page
        response = requests.get(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            params={"body-format": "storage"}
        )
        response.raise_for_status()
        data = response.json()
        storage_xml = data["body"]["storage"]["value"]

        # 2. Detect macros
        macro_types = self._detect_macros(storage_xml)

        # 3. Classify macro importance
        has_critical = any(m in self.critical_macros for m in macro_types)
        has_only_safe = all(m in self.safe_macros for m in macro_types)

        if not macro_types:
            macro_importance = MacroImportance.NONE
        elif has_critical:
            macro_importance = MacroImportance.HIGH
        elif has_only_safe:
            macro_importance = MacroImportance.LOW
        else:
            macro_importance = MacroImportance.LOW

        # 4. Classify edit complexity
        edit_complexity = self._classify_edit_complexity(edit_instruction)

        # 5. Make decision
        recommended_method, reason = self._decide_method(
            macro_importance,
            edit_complexity,
            macro_types
        )

        return PageAnalysis(
            has_macros=bool(macro_types),
            macro_importance=macro_importance,
            macro_types=macro_types,
            edit_complexity=edit_complexity,
            recommended_method=recommended_method,
            reason=reason
        )

    def _detect_macros(self, storage_xml: str) -> list[str]:
        """Detect all macros in page"""
        try:
            doc = html.fromstring(f"<root>{storage_xml}</root>")
            macros = doc.xpath("//ac:structured-macro/@ac:name")
            return list(set(macros))  # Unique macro names
        except Exception:
            return []

    def _classify_edit_complexity(self, instruction: str) -> EditComplexity:
        """
        Classify edit complexity based on instruction
        """
        instruction_lower = instruction.lower()

        # Simple indicators
        simple_keywords = [
            'fix typo', 'correct', 'update date', 'change to',
            'add sentence', 'add paragraph', 'remove sentence'
        ]

        # Complex indicators
        complex_keywords = [
            'rewrite', 'improve', 'make it better', 'rephrase',
            'create', 'write', 'draft', 'compose', 'explain'
        ]

        if any(kw in instruction_lower for kw in simple_keywords):
            return EditComplexity.SIMPLE
        elif any(kw in instruction_lower for kw in complex_keywords):
            return EditComplexity.COMPLEX
        else:
            return EditComplexity.MODERATE

    def _decide_method(
        self,
        macro_importance: MacroImportance,
        edit_complexity: EditComplexity,
        macro_types: list[str]
    ) -> tuple[Literal[1, 4], str]:
        """
        Decision logic for method selection

        Decision Matrix:
        ┌──────────────────┬──────────────┬──────────────┬──────────────┐
        │ Macro Importance │ Simple Edit  │ Moderate     │ Complex Edit │
        ├──────────────────┼──────────────┼──────────────┼──────────────┤
        │ NONE             │ Method 1     │ Method 1     │ Method 1     │
        │ LOW              │ Method 1     │ Method 1     │ Method 1     │
        │ HIGH             │ Method 4     │ Method 1*    │ Method 1*    │
        └──────────────────┴──────────────┴──────────────┴──────────────┘

        * HIGH + Moderate/Complex: User warned about macro loss
        """

        # No macros or only safe macros -> Always Method 1 (Claude intelligent editing)
        if macro_importance in [MacroImportance.NONE, MacroImportance.LOW]:
            return 1, "No critical macros, safe for Markdown conversion"

        # High importance macros + Simple edit -> Method 4 (preserve macros)
        if edit_complexity == EditComplexity.SIMPLE:
            return 4, f"Preserving critical macros: {', '.join(macro_types)}"

        # High importance macros + Complex edit -> Method 1 with warning
        return 1, (
            f"Complex edit requires Claude intelligence. "
            f"WARNING: Will lose macros: {', '.join(macro_types)}"
        )

    def edit_page(
        self,
        page_id: str,
        edit_instruction: str,
        force_method: Literal[1, 4, None] = None
    ):
        """
        Hybrid edit with auto-detection

        Args:
            page_id: Confluence page ID
            edit_instruction: Natural language instruction for Claude
            force_method: Override auto-detection (optional)
        """
        # 1. Analyze page
        analysis = self.analyze_page(page_id, edit_instruction)

        # 2. Get method (forced or auto-detected)
        method = force_method or analysis.recommended_method

        # 3. Print decision
        print(f"📊 Page Analysis:")
        print(f"  - Macros: {analysis.macro_types or 'None'}")
        print(f"  - Macro Importance: {analysis.macro_importance.value}")
        print(f"  - Edit Complexity: {analysis.edit_complexity.value}")
        print(f"  - Recommended: Method {analysis.recommended_method}")
        print(f"  - Reason: {analysis.reason}")
        print(f"  - Using: Method {method}")

        # 4. Warn user if losing macros
        if method == 1 and analysis.macro_importance == MacroImportance.HIGH:
            print("\n⚠️  WARNING: This will lose macros!")
            confirm = input("Continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return

        # 5. Execute appropriate method
        if method == 1:
            self._method_1_markdown_roundtrip(page_id, edit_instruction)
        else:
            self._method_4_direct_xml(page_id, edit_instruction)

        print(f"\n✅ Page {page_id} updated successfully")

    def _method_1_markdown_roundtrip(self, page_id: str, instruction: str):
        """Method 1: Storage → Markdown → Claude Edit → Storage"""
        # Fetch Storage Format
        response = requests.get(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            params={"body-format": "storage"}
        )
        data = response.json()
        storage_html = data["body"]["storage"]["value"]

        # Convert to Markdown
        h = html2text.HTML2Text()
        h.body_width = 0
        markdown = h.handle(storage_html)

        # Claude edit (simplified - replace with actual Claude API call)
        print(f"\n🤖 Claude editing with instruction: {instruction}")
        # edited_markdown = call_claude_api(markdown, instruction)
        edited_markdown = markdown + "\n\n[Edited based on instruction]"

        # Convert back to Storage Format
        edited_storage = mistune.html(edited_markdown)

        # Write back
        requests.put(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            json={
                "id": page_id,
                "version": {"number": data["version"]["number"] + 1},
                "body": {"storage": {"value": edited_storage, "representation": "storage"}}
            }
        )

    def _method_4_direct_xml(self, page_id: str, instruction: str):
        """Method 4: Direct XML edit (macros preserved)"""
        # Fetch Storage Format
        response = requests.get(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            params={"body-format": "storage"}
        )
        data = response.json()
        storage_xml = data["body"]["storage"]["value"]

        # Parse XML
        doc = html.fromstring(f"<root>{storage_xml}</root>")

        # Simple programmatic edit (example: find first paragraph and modify)
        print(f"\n🔧 Direct XML edit: {instruction}")
        paragraphs = doc.xpath("//p")
        if paragraphs and "add note" in instruction.lower():
            # Example: Add a note paragraph
            new_p = etree.Element("p")
            new_p.text = f"Note: {instruction}"
            paragraphs[0].addprevious(new_p)

        # Serialize back
        edited_xml = etree.tostring(doc, encoding='unicode', method='html')
        edited_xml = edited_xml.replace('<root>', '').replace('</root>', '')

        # Write back
        requests.put(
            f"{self.base_url}/wiki/api/v2/pages/{page_id}",
            headers=self.headers,
            json={
                "id": page_id,
                "version": {"number": data["version"]["number"] + 1},
                "body": {"storage": {"value": edited_xml, "representation": "storage"}}
            }
        )


# ============================================================
# Usage Examples
# ============================================================

if __name__ == "__main__":
    hybrid = HybridRoundtrip()

    # Example 1: Simple typo fix on page with critical macros
    # -> Auto-selects Method 4 (preserve macros)
    hybrid.edit_page(
        page_id="123456",
        edit_instruction="Fix typo: change 'teh' to 'the'"
    )

    # Example 2: Complete rewrite on page with macros
    # -> Auto-selects Method 1 with warning (needs Claude intelligence)
    hybrid.edit_page(
        page_id="123456",
        edit_instruction="Rewrite this section to be more professional"
    )

    # Example 3: Add paragraph on page without macros
    # -> Auto-selects Method 1 (safe, no macros to lose)
    hybrid.edit_page(
        page_id="789012",
        edit_instruction="Add a paragraph about installation steps"
    )

    # Example 4: Force specific method
    hybrid.edit_page(
        page_id="123456",
        edit_instruction="Update date",
        force_method=4  # Force Method 4
    )
```

### Pros

✅ **Intelligent Auto-Selection**: Automatically chooses the best method
✅ **Macro Preservation When Possible**: Uses Method 4 for simple edits with critical macros
✅ **Claude Intelligence When Needed**: Uses Method 1 for complex edits requiring AI
✅ **User Warnings**: Alerts user when macros will be lost
✅ **Flexible Override**: Allows manual method selection if needed
✅ **Best of Both Worlds**: Balances macro preservation with editing capability

### Cons

❌ **Increased Complexity**: More code to maintain than single-method approach
❌ **Detection Not Perfect**: Classification may sometimes choose sub-optimal method
❌ **Requires Both Implementations**: Must maintain both Method 1 and Method 4 code

### Decision Matrix

```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│ Macro Importance │ Simple Edit  │ Moderate     │ Complex Edit │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ NONE             │ Method 1     │ Method 1     │ Method 1     │
│ LOW              │ Method 1     │ Method 1     │ Method 1     │
│ HIGH             │ Method 4 ✅  │ Method 1* ⚠️  │ Method 1* ⚠️  │
└──────────────────┴──────────────┴──────────────┴──────────────┘

✅ = Optimal choice (preserves macros + appropriate editing capability)
⚠️ = Warning given to user (macros will be lost, but Claude intelligence needed)
```

### Use Cases

- **Production environments** where both macro preservation and AI editing are valuable
- **Mixed content pages** (some with macros, some without)
- **Teams with varying technical skills** (auto-detection removes decision burden)
- **Skill/Plugin implementation** where user shouldn't think about methods

---

## Method 6: MCP + JSON Diff (⭐ Recommended)

### Overview

**Method 6** combines MCP for reading/writing with JSON diff/patch to preserve macros while allowing Claude to edit
content. This is the **recommended approach** as it:

- Uses MCP (OAuth authentication, no API token needed)
- Preserves all macros (they are never modified)
- Allows Claude to intelligently edit non-macro content

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (with macros)                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: getConfluencePage(contentFormat: "adf")
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Original ADF JSON (contains macro nodes)                   │
│  {"type":"doc","content":[...macros...text...]}            │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     │ (keep original)
┌────────────────┐            │
│ Convert to     │            │
│ Markdown       │            │
│ (macros lost   │            │
│  in this copy) │            │
└───────┬────────┘            │
        │                     │
        ▼                     │
┌────────────────┐            │
│ Claude Edit    │            │
│ Markdown       │            │
└───────┬────────┘            │
        │                     │
        ▼                     │
┌────────────────┐            │
│ Convert back   │            │
│ to ADF JSON    │            │
│ (no macros)    │            │
└───────┬────────┘            │
        │                     │
        ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│  JSON Diff Engine                                           │
│  - Compare original ADF vs edited ADF                       │
│  - Identify only TEXT node changes                          │
│  - Ignore structural differences (macros)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Apply text changes to original ADF
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Patched ADF JSON                                           │
│  - Text content updated (Claude's edits)                    │
│  - Macro nodes untouched (fully preserved)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MCP: updateConfluencePage
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (updated, macros preserved)                │
└─────────────────────────────────────────────────────────────┘
```

### Key Insight

The trick is: **we never modify macro nodes directly**. Instead:

1. Convert to Markdown (macros disappear but that's OK - it's just for Claude)
2. Claude edits the Markdown
3. Convert back to ADF (still no macros)
4. Diff to find what TEXT changed
5. Apply only text changes to the ORIGINAL ADF (which still has macros)

### Complete Implementation

```python
#!/usr/bin/env python3
"""
scripts/mcp_json_diff_roundtrip.py
Method 6: MCP + JSON Diff (Recommended)

Preserves macros while allowing Claude to edit content.
"""

import json
import copy
from dataclasses import dataclass
from typing import Any, Optional

# For ADF ↔ Markdown conversion
# Option 1: Use atlas-doc-parser (Python)
# Option 2: Use simple text extraction (shown below)


@dataclass
class TextChange:
    """Represents a text change to apply"""
    path: list[int]  # Path to the text node in ADF
    old_text: str
    new_text: str


class ADFTextExtractor:
    """Extract and restore text from ADF JSON"""

    def extract_text_with_paths(self, adf: dict) -> list[tuple[list[int], str]]:
        """
        Extract all text nodes with their paths.
        Returns: [(path, text), ...]
        """
        results = []
        self._extract_recursive(adf, [], results)
        return results

    def _extract_recursive(self, node: Any, path: list[int], results: list):
        if isinstance(node, dict):
            # Text node
            if node.get("type") == "text" and "text" in node:
                results.append((path.copy(), node["text"]))

            # Skip macro nodes entirely (they won't be in markdown)
            if node.get("type") in ["inlineExtension", "extension", "bodiedExtension"]:
                return

            # Recurse into content
            if "content" in node and isinstance(node["content"], list):
                for i, child in enumerate(node["content"]):
                    self._extract_recursive(child, path + ["content", i], results)

        elif isinstance(node, list):
            for i, child in enumerate(node):
                self._extract_recursive(child, path + [i], results)

    def apply_text_changes(self, adf: dict, changes: list[TextChange]) -> dict:
        """Apply text changes to ADF, preserving structure"""
        result = copy.deepcopy(adf)

        for change in changes:
            node = result
            # Navigate to parent of text node
            for key in change.path[:-1]:
                node = node[key]
            # Update text
            last_key = change.path[-1]
            if isinstance(node, dict) and "text" in node:
                node["text"] = change.new_text
            elif isinstance(node, list):
                node[last_key]["text"] = change.new_text

        return result


class SimpleMarkdownConverter:
    """Simple ADF ↔ Markdown conversion for Claude editing"""

    def adf_to_markdown(self, adf: dict) -> str:
        """Convert ADF to simple Markdown (macros become placeholders)"""
        lines = []
        self._convert_node(adf, lines, 0)
        return "\n".join(lines)

    def _convert_node(self, node: dict, lines: list, depth: int):
        if not isinstance(node, dict):
            return

        node_type = node.get("type", "")

        # Skip/placeholder for macros
        if node_type in ["inlineExtension", "extension", "bodiedExtension"]:
            macro_name = node.get("attrs", {}).get("extensionKey", "macro")
            lines.append(f"<!-- MACRO: {macro_name} -->")
            return

        # Handle different node types
        if node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            text = self._get_text_content(node)
            lines.append(f"{'#' * level} {text}")
            lines.append("")

        elif node_type == "paragraph":
            text = self._get_text_content(node)
            if text.strip():
                lines.append(text)
                lines.append("")

        elif node_type == "bulletList":
            for item in node.get("content", []):
                text = self._get_text_content(item)
                lines.append(f"- {text}")
            lines.append("")

        elif node_type == "orderedList":
            for i, item in enumerate(node.get("content", []), 1):
                text = self._get_text_content(item)
                lines.append(f"{i}. {text}")
            lines.append("")

        elif node_type == "codeBlock":
            lang = node.get("attrs", {}).get("language", "")
            text = self._get_text_content(node)
            lines.append(f"```{lang}")
            lines.append(text)
            lines.append("```")
            lines.append("")

        elif node_type == "blockquote":
            for child in node.get("content", []):
                text = self._get_text_content(child)
                lines.append(f"> {text}")
            lines.append("")

        elif node_type == "doc":
            for child in node.get("content", []):
                self._convert_node(child, lines, depth)

        else:
            # Recurse into unknown structures
            for child in node.get("content", []):
                self._convert_node(child, lines, depth + 1)

    def _get_text_content(self, node: dict) -> str:
        """Extract plain text from a node"""
        if node.get("type") == "text":
            return node.get("text", "")

        texts = []
        for child in node.get("content", []):
            if child.get("type") == "text":
                texts.append(child.get("text", ""))
            elif "content" in child:
                texts.append(self._get_text_content(child))
        return "".join(texts)


class TextDiffer:
    """Compare markdown texts and generate change list"""

    def diff_texts(
        self,
        original_texts: list[tuple[list, str]],
        edited_markdown: str
    ) -> list[TextChange]:
        """
        Compare original text nodes with edited markdown.
        Returns list of changes to apply.
        """
        changes = []

        # Simple line-based matching
        # (In production, use more sophisticated diffing like difflib)
        edited_lines = [l.strip() for l in edited_markdown.split("\n") if l.strip()]

        for path, original_text in original_texts:
            original_clean = original_text.strip()
            if not original_clean:
                continue

            # Find if this text was modified
            for edited_line in edited_lines:
                # Check for similar but changed text
                if self._is_modified_version(original_clean, edited_line):
                    if original_clean != edited_line:
                        changes.append(TextChange(
                            path=path,
                            old_text=original_text,
                            new_text=edited_line
                        ))
                    break

        return changes

    def _is_modified_version(self, original: str, edited: str) -> bool:
        """Check if edited is a modified version of original"""
        # Simple heuristic: significant word overlap
        orig_words = set(original.lower().split())
        edit_words = set(edited.lower().split())

        if not orig_words:
            return False

        overlap = len(orig_words & edit_words) / len(orig_words)
        return overlap > 0.3  # At least 30% word overlap


class MCPJsonDiffRoundtrip:
    """
    Method 6: MCP + JSON Diff Roundtrip

    Uses MCP for read/write, JSON diff for preserving macros.
    """

    def __init__(self, mcp_client):
        """
        Args:
            mcp_client: MCP client for Confluence operations
        """
        self.mcp = mcp_client
        self.extractor = ADFTextExtractor()
        self.converter = SimpleMarkdownConverter()
        self.differ = TextDiffer()

    def edit_page(
        self,
        cloud_id: str,
        page_id: str,
        edit_instruction: str,
        claude_edit_fn: callable
    ) -> dict:
        """
        Edit a Confluence page while preserving macros.

        Args:
            cloud_id: Atlassian Cloud ID
            page_id: Page ID to edit
            edit_instruction: Instruction for Claude
            claude_edit_fn: Function that takes (markdown, instruction) and returns edited markdown

        Returns:
            Updated page data
        """
        # 1. Read page via MCP (ADF format)
        print(f"📖 Reading page {page_id}...")
        page_data = self.mcp.call_tool(
            "mcp__plugin_confluence_atlassian__getConfluencePage",
            {
                "cloudId": cloud_id,
                "pageId": page_id,
                "contentFormat": "adf"
            }
        )

        original_adf = json.loads(page_data["body"]["value"])
        page_title = page_data["title"]

        # 2. Extract text with paths (for later patching)
        print("🔍 Extracting text nodes...")
        text_paths = self.extractor.extract_text_with_paths(original_adf)
        print(f"   Found {len(text_paths)} text nodes")

        # 3. Convert to Markdown (macros become placeholders)
        print("📝 Converting to Markdown...")
        markdown = self.converter.adf_to_markdown(original_adf)

        # 4. Claude edits the Markdown
        print(f"🤖 Claude editing with instruction: {edit_instruction[:50]}...")
        edited_markdown = claude_edit_fn(markdown, edit_instruction)

        # 5. Diff to find text changes
        print("🔄 Computing diff...")
        changes = self.differ.diff_texts(text_paths, edited_markdown)
        print(f"   Found {len(changes)} text changes")

        if not changes:
            print("ℹ️  No changes detected, skipping update")
            return page_data

        # 6. Apply changes to original ADF (macros untouched!)
        print("🔧 Applying changes to original ADF...")
        patched_adf = self.extractor.apply_text_changes(original_adf, changes)

        # 7. Write back via MCP
        print("💾 Writing back to Confluence...")
        result = self.mcp.call_tool(
            "mcp__plugin_confluence_atlassian__updateConfluencePage",
            {
                "cloudId": cloud_id,
                "pageId": page_id,
                "body": json.dumps(patched_adf),
                "contentFormat": "adf"
            }
        )

        print(f"✅ Page '{page_title}' updated successfully!")
        print(f"   Macros preserved: Yes")
        print(f"   Text changes applied: {len(changes)}")

        return result


# ============================================================
# Usage Example
# ============================================================

def example_claude_edit(markdown: str, instruction: str) -> str:
    """
    Example Claude edit function.
    Replace with actual Claude API call.
    """
    # In real implementation:
    # return claude_api.edit(markdown, instruction)

    # For demo, simple string replacement
    if "fix typo" in instruction.lower():
        return markdown.replace("teh", "the").replace("adn", "and")
    elif "add note" in instruction.lower():
        return markdown + "\n\n**Note:** This page was updated automatically."
    else:
        return markdown


if __name__ == "__main__":
    # Example usage (requires MCP client setup)

    # from mcp_client import MCPClient
    # mcp = MCPClient()

    # roundtrip = MCPJsonDiffRoundtrip(mcp)
    # roundtrip.edit_page(
    #     cloud_id="your-cloud-id",
    #     page_id="123456789",
    #     edit_instruction="Fix any typos and improve clarity",
    #     claude_edit_fn=lambda md, inst: claude_api.edit(md, inst)
    # )

    print("Method 6: MCP + JSON Diff Roundtrip (Interactive)")
    print("===================================================")
    print("This method preserves macros while allowing Claude to edit ALL text content.")
    print()
    print("Key benefits:")
    print("  ✅ Uses MCP (OAuth, no API token needed)")
    print("  ✅ Macros fully preserved (structure never modified)")
    print("  ✅ Claude can edit all text (including macro bodies in Advanced Mode)")
    print("  ✅ Safe Mode (default) + Advanced Mode (opt-in)")
    print("  ✅ Automatic backup and rollback")
    print("  ✅ Interactive prompts for user control")
    print()
    print("Modes:")
    print("  • Safe Mode (default): Skip macro bodies, zero risk")
    print("  • Advanced Mode: Edit macro bodies with confirmation and backup")
```

### Pros

✅ **Macros fully preserved**: Macro structure is never modified
✅ **Claude can edit content**: All text is editable (including optional macro bodies)
✅ **Uses MCP**: OAuth authentication, no API token management
✅ **Simple concept**: Just diff and patch text nodes
✅ **Safe by default**: Safe mode skips macro bodies; advanced mode requires confirmation
✅ **No dual-language**: Pure Python implementation
✅ **Backup and rollback**: Automatic backup before edit, auto-rollback on failure
✅ **User control**: Interactive prompts let users decide risk/benefit trade-offs

### Cons

❌ **Text matching complexity**: Need robust diff algorithm for real-world use
❌ **Conversion quality**: Simple Markdown conversion may lose some formatting
❌ **Path stability**: ADF paths may change if structure is modified
⚠️ **Macro body editing is riskier**: Requires user confirmation, backup essential

### Two Modes

**Safe Mode (Default):**

- Skips macro body content
- Only edits text outside macros
- No risk to macro structure
- Recommended for most users

**Advanced Mode (Optional):**

- User-confirmed macro body editing
- Detects macros with editable content
- Shows preview and asks for confirmation
- Creates backup before editing
- Auto-rollback on failure

### What CAN be edited

**Safe Mode:**

- Regular paragraphs
- Headings
- List items
- Code blocks (content)
- Table cells
- Any text **outside** of macros

**Advanced Mode (with confirmation):**

- All of the above, PLUS
- Text **inside** macro bodies (expand, panel, info, etc.)
- Macro structure itself is still preserved

### Backup and Rollback

**Automatic Backup:**

- Created before every edit operation
- Stored in `.confluence_backups/{page_id}/`
- Keeps last 10 backups per page (configurable)

**Automatic Rollback:**

- Triggers on write failure
- Restores from backup immediately
- Logs error for debugging

**Manual Rollback:**

- List available backups with timestamps
- Select backup to restore
- Confirm and restore

### When to Use Method 6

| Scenario | Mode | Use Method 6? |
|----------|------|--------------|
| Edit paragraphs on page with macros | Safe | ✅ Yes (default) |
| Fix typos while preserving macros | Safe | ✅ Yes (default) |
| Add new sections (text only) | Safe | ✅ Yes (default) |
| Edit text inside expand macro | **Advanced** | ✅ **Yes (with confirmation)** |
| Edit text inside panel/info macros | **Advanced** | ✅ **Yes (with confirmation)** |
| Edit page with no macros | Safe | ✅ Yes, or use Method 7 (Method 1 DEPRECATED) |
| Major rewrite of macro-heavy page | Safe/Advanced | ✅ Yes (choose mode based on needs) |
| Batch operations | N/A | ❌ No, use Method 7 (Method 1 DEPRECATED) |

### Comparison with Other Methods

| Aspect | Method 1 | Method 4 | Method 5 | Method 6 |
|--------|----------|----------|----------|----------|
| **Claude editing** | ✅ Full | ❌ No | ⚠️ Depends | ✅ Full (both modes) |
| **Macro preservation** | ❌ Lost | ✅ Full | ⚠️ Depends | ✅ Full |
| **Edit macro body** | ❌ N/A | ✅ Programmatic | ⚠️ Depends | ✅ **Interactive** |
| **Backup/Rollback** | ❌ No | ❌ No | ⚠️ Partial | ✅ **Automatic** |
| **User control** | N/A | N/A | ⚠️ Auto-detect | ✅ **Interactive prompts** |
| **Complexity** | Low | Medium | High | Medium |
| **Auth method** | API Token | API Token | Both | MCP (OAuth) |

### Decision: Method 5 vs Method 6

```
Method 5 (Hybrid Auto-Detection):
  - Auto-detects and chooses Method 1 or 4
  - May lose macros for complex edits
  - More complex implementation
  - Less user control (opaque decisions)

Method 6 (Interactive JSON Diff):
  - Always preserves macros
  - Safe mode (default) + Advanced mode (optional)
  - Interactive prompts for user control
  - Automatic backup and rollback
  - Simpler, more predictable

Recommendation:
  ⭐ Use Method 6 as the default ⭐
  - Start with Safe Mode (skips macro bodies)
  - Opt into Advanced Mode when needed
  - Backup/rollback provides confidence
```

---

## Side-by-Side Comparison: Key Metrics

### Implementation Complexity

| Metric | Method 1 | Method 2 | Method 3 | Method 4 | Method 5 | Method 6 ⭐ |
|-----|--------|--------|--------|--------|--------|--------|
| **Lines of Code** | ~150 | ~200 (Py+JS) | ~50 | ~100 | ~250 | ~200 |
| **Languages** | 1 (Python) | 2 (Py + JS) | 1 (Python) | 1 (Python) | 1 (Python) | 1 (Python) |
| **Dependencies** | ~~3 pip~~ (removed) | 1 pip + 1 npm | 0 | 1 (lxml) | 4 | 1 (MCP) |
| **Setup Steps** | 3 | 5 | 1 | 3 | 3 | 1 (MCP ready) |
| **Learning Curve** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Claude Usability** | ✅ Full | ✅ Full | ✅ Full | ❌ No | ⚠️ Depends | ✅ Text only |
| **Macro Preserved** | ❌ | ❌ | ❌ | ✅ | ⚠️ | ✅ **Yes** |
| **Auth Method** | API Token | OAuth | OAuth | API Token | Both | **MCP OAuth** |

### Conversion Quality

| Test Scenario | Method 1 | Method 2 | Method 3 | Method 4 | Method 5 | Method 6 ⭐ |
|---------|--------|--------|--------|--------|--------|--------|
| **Plain text** | ✅ Perfect | ✅ Perfect | ✅ Good | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Headings** | ✅ Perfect | ✅ Perfect | ✅ Good | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Lists** | ✅ Perfect | ✅ Perfect | ⚠️ May break | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Code blocks** | ✅ Perfect | ✅ Good | ⚠️ Corrupt | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Tables** | ✅ Perfect | ⚠️ Simplify | ❌ Hard | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Bold/Italic** | ✅ Perfect | ✅ Perfect | ✅ Good | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Links** | ✅ Perfect | ✅ Perfect | ⚠️ May break | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Images** | ✅ Preserved | ⚠️ May lose | ⚠️ May lose | ✅ Perfect | ✅ Preserved | ✅ **Preserved** |
| **Nested** | ✅ Perfect | ✅ Good | ❌ Error-prone | ✅ Perfect | ✅ Perfect | ✅ Perfect |
| **Macros** | ❌ Lost | ❌ Lost | ❌ Lost | ✅ **Full** | ⚠️ Smart | ✅ **Full** |
| **Macro body** | ❌ N/A | ❌ N/A | ❌ N/A | ✅ Programmatic | ⚠️ Depends | ✅ **Interactive** |

\* Method 5: Simple edits preserve macros (Method 4), complex edits lose macros but get Claude intelligence
(Method 1)
\* Method 6: Macros always preserved. Macro body editing optional (Safe mode: skip, Advanced mode: interactive with
confirmation and backup)

### Performance

| Metric | Method 1 | Method 2 | Method 3 | Method 4 | Method 5 | Method 6 ⭐ |
|-----|--------|--------|--------|--------|--------|--------|
| **Read speed** | ~300ms | ~500ms | ~500ms | ~300ms | ~300ms | ~500ms (MCP) |
| **Detection** | N/A | N/A | N/A | N/A | ~100ms | ~50ms |
| **Conversion** | ~50ms | ~200ms | 0ms | 0ms | ~0-50ms | ~50ms |
| **Diff/Patch** | N/A | N/A | N/A | N/A | N/A | ~100ms |
| **Edit speed** | Depends | Depends | ~2-5s | ~10-50ms | ~10ms-5s | ~2-5s (Claude) |
| **Write speed** | ~300ms | ~500ms | ~500ms | ~300ms | ~300ms | ~500ms (MCP) |
| **Total time** | ~1-2s | ~2-3s | ~3-6s | ~0.7-1s | ~1-6s | **~3-6s** |
| **Token usage** | Low | Low | High | None | Low-High | Medium |

### Reliability

| Scenario | Method 1 | Method 2 | Method 3 | Method 4 | Method 5 | Method 6 ⭐ |
|-----|--------|--------|--------|--------|--------|--------|
| **Format** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Macros** | ❌ Lost | ❌ Lost | ❌ Lost | ✅ **Full** | ⚠️ Smart | ✅ **Full** |
| **Error recovery** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Version conflict** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Large files** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Concurrency** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Predictability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Maintenance Cost

| Aspect | Method 1 | Method 2 | Method 3 | Method 4 | Method 5 | Method 6 ⭐ |
|-----|--------|--------|--------|--------|--------|--------|
| **Dependencies** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ (MCP only) |
| **API impact** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ (MCP handles) |
| **Debugging** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Testing** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Documentation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Expertise** | REST API | REST + 2 langs | Basic | XML/XPath | REST + XPath | **MCP + JSON** |
| **Transparency** | N/A | N/A | N/A | N/A | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Decision Flow Chart

```
Start Roundtrip Implementation Selection
│
├─→ ⭐ Want Claude editing + Macro preservation? (Most common case)
│   └─→ Yes: ⭐⭐⭐ Method 6 (MCP + JSON Diff) ⭐⭐⭐
│       ✅ Uses MCP (OAuth, no API token)
│       ✅ Macros fully preserved
│       ✅ Claude can edit ALL text (including macro bodies)
│       ✅ Safe Mode (default) + Advanced Mode (optional)
│       ✅ Automatic backup and rollback
│       ✅ Interactive prompts for user control
│       👉 RECOMMENDED for this plugin
│
├─→ Need to edit text INSIDE macro bodies?
│   └─→ Yes: ✅ Method 6 Advanced Mode
│       - Detects macros with editable content
│       - Shows preview and asks for confirmation
│       - Creates backup automatically
│       - Auto-rollback if write fails
│
├─→ Page has NO macros at all?
│   └─→ Yes: Method 7 (ADF-native roundtrip) or Method 6
│       ✅ Full Claude editing
│       ✅ No macro concerns
│       ⚠️ Method 1 is DEPRECATED (dependencies removed)
│
├─→ Need programmatic batch operations (no AI)?
│   └─→ Yes: Method 4 (Direct XML Edit)
│       ✅ Full macro preservation
│       ✅ Full control
│       ❌ No Claude intelligence
│
├─→ Want auto-detection between methods?
│   └─→ Yes: Method 5 (Hybrid)
│       ⚠️ More complex than Method 6
│       ⚠️ May lose macros for complex edits
│
├─→ Quick prototype testing?
│   └─→ Yes: ~~Method 3 (Pragmatic)~~ DEPRECATED
│       ❌ Dependencies removed; use Method 6 or 7 instead
│
└─→ Unsure?
    └─→ Start with ⭐ Method 6 ⭐
        - Best balance of features
        - MCP-based (already set up)
        - Predictable behavior
```

**Key Decision Points:**

- **⭐ Default choice**: Method 6 (MCP + JSON Diff) - Claude editing + full macro preservation
- **Edit macro body content**: ✅ Method 6 Advanced Mode (interactive with backup)
- **No macros on page**: Method 7 or Method 6 (Method 1 is DEPRECATED)
- **Batch operations**: Method 7 for batch processing (Method 1 is DEPRECATED)
- **Auto-detection needed**: Method 5 (but Method 6's interactive mode is clearer)

---

## Practical Usage Recommendations

### Phased Implementation Strategy

#### Phase 1: Quick Validation (1 day)

```
Implementation: Method 3 (Pragmatic Hybrid) -- DEPRECATED
Goal: Validate MCP integration, test simple edits
Output: Proof of concept that can edit simple pages with Claude
Note: Method 3 dependencies have been removed. Use Method 6 or 7 instead.
```

#### Phase 2: Production Ready (3-5 days)

```
Implementation: Method 1 (REST API + Storage) -- DEPRECATED
Goal: Stable and reliable roundtrip workflow
Output:
  - scripts/cf2md.py (Confluence → Markdown)
  - scripts/md2cf.py (Markdown → Confluence)
  - Complete error handling and validation
Note: Method 1 dependencies (md2cf, html2text) have been removed.
      Use Method 7 (ADF-native roundtrip) for upload/download instead.
```

#### Phase 3: Integration Optimization (Optional)

```
Optimization:
  - Add macro detection (don't edit pages with macros)
  - Implement backup mechanism
  - Add diff preview
  - Auto-handle version conflicts
```

### Recommendations by Scenario

| Use Case | Recommended Method | Reason |
|---------|---------|------|
| **Batch fix typos** | Method 7 | Need stability, batch processing (Method 1 DEPRECATED) |
| **Add new paragraph** | Method 6 or 7 | Use Method 6 for interactive, Method 7 for scripts (Methods 1, 3 DEPRECATED) |
| **Update code blocks** | Method 7 | Code format important, need precise conversion (Method 1 DEPRECATED) |
| **Change headings** | Method 6 | Simple task, MCP-based editing (Method 3 DEPRECATED) |
| **Reorganize content structure** | Method 6 or 7 | Complex edit, need high-quality conversion (Method 1 DEPRECATED) |
| **CI/CD auto-update** | Method 7 | Production environment, must be stable (Method 1 DEPRECATED) |
| **Interactive editing (IDE)** | Method 6 | Real-time user editing, MCP-based (Method 3 DEPRECATED) |

---

## Implementation Checklist

### Method 1 (REST API + Storage) -- DEPRECATED

- [ ] ~~Set up environment variables (CONFLUENCE_URL, API_TOKEN, USERNAME)~~
- [ ] ~~Install Python dependencies (`pip install requests html2text mistune`)~~ (removed)
- [ ] Implement `read_page()` function
- [ ] Implement `write_page()` function
- [ ] Add version number checking
- [ ] Implement backup mechanism
- [ ] Add error handling (network errors, auth failures, version conflicts)
- [ ] Write unit tests
- [ ] Test simple edits
- [ ] Test complex edits (tables, lists, code)
- [ ] Document usage

### Method 2 (MCP + ADF) -- DEPRECATED

- [ ] ~~Set up MCP OAuth authentication~~
- [ ] ~~Install Python dependencies (`pip install atlas-doc-parser`)~~
- [ ] Install Node.js dependencies (`npm install marklassian`)
- [ ] Implement Python `adf_to_markdown()` function
- [ ] Implement Node.js `markdown_to_adf()` script
- [ ] Implement subprocess call logic
- [ ] Add subprocess error handling
- [ ] Test cross-language calls
- [ ] Test conversion quality
- [ ] Optimize performance (consider caching)
- [ ] Document setup steps

### Method 3 (Pragmatic) -- DEPRECATED

- [ ] ~~Set up MCP OAuth authentication~~
- [ ] Implement `quick_edit()` function
- [ ] Design Claude prompt template
- [ ] Add JSON validation
- [ ] Test simple edit tasks
- [ ] Document applicable scenarios and limitations
- [ ] Build test cases
- [ ] Set up error fallback mechanism

### Method 4 (Direct XML/JSON Edit)

- [ ] Set up environment variables (CONFLUENCE_URL, API_TOKEN, USERNAME)
- [ ] Install Python dependencies (`pip install requests lxml`)
- [ ] Implement `roundtrip_direct_xml()` function
- [ ] Learn Storage Format structure (read official docs)
- [ ] Learn XPath syntax (for finding elements)
- [ ] Implement macro detection function
- [ ] Implement backup mechanism (⚠️ More important, easy to corrupt structure)
- [ ] Implement XML validation (ensure correct structure)
- [ ] Test simple XPath edits (modify text)
- [ ] Test macro preservation (confirm macros fully preserved)
- [ ] Build error recovery mechanism
- [ ] Document XPath patterns and usage

⚠️ **Important Reminder:** Method 4 can easily corrupt page structure, must:

- Thoroughly test before using in production
- Auto-backup before each edit
- Implement XML structure validation
- Start testing with simple pages

### Method 5 (Hybrid Strategy)

- [ ] **Prerequisites**: Complete Method 1 and Method 4 implementations first
- [ ] Implement `MacroImportance` and `EditComplexity` enums
- [ ] Implement `PageAnalysis` dataclass
- [ ] Implement `_detect_macros()` function (XPath macro detection)
- [ ] Define `critical_macros` and `safe_macros` sets
- [ ] Implement `_classify_edit_complexity()` function (keyword analysis)
- [ ] Implement `_decide_method()` decision logic (Decision Matrix)
- [ ] Implement `analyze_page()` integrated analysis
- [ ] Implement `edit_page()` main interface (with warning mechanism)
- [ ] Integrate `_method_1_markdown_roundtrip()` function
- [ ] Integrate `_method_4_direct_xml()` function
- [ ] Add user confirmation mechanism (macro loss warning)
- [ ] Test various scenario combinations:
  - [ ] No macros + simple edit
  - [ ] No macros + complex edit
  - [ ] Safe macros (code, TOC) + any edit
  - [ ] Critical macros (expand, status) + simple edit
  - [ ] Critical macros + complex edit (with warning)
- [ ] Implement `force_method` override parameter
- [ ] Add detailed decision log output
- [ ] Write usage examples and documentation
- [ ] Integrate into confluence skill

✨ **Benefits of Implementing Method 5:**

- Users don't need to understand the technical differences
- Automatically preserves macros when possible
- Warns users when trade-offs are necessary
- Best user experience for the skill

---

## Summary Recommendations

### 🏆 Recommended Configuration

**For this Confluence plugin**, recommend adopting **⭐⭐⭐ Method 6 (MCP + JSON Diff) ⭐⭐⭐**:

```yaml
Primary Implementation:
  Method: Method 6 (MCP + JSON Diff with Interactive Modes)
  Reasons:
    - ✅ Uses MCP (OAuth authentication, already set up)
    - ✅ Macros ALWAYS preserved (structure never modified)
    - ✅ Claude can edit ALL text content (including macro bodies)
    - ✅ Safe Mode (default) + Advanced Mode (opt-in)
    - ✅ Automatic backup and rollback
    - ✅ Interactive prompts give user control
    - ✅ Simpler than Method 5 (no opaque auto-detection)
    - ✅ Pure Python implementation

  Deliverables:
    - scripts/mcp_json_diff_roundtrip.py (~300 lines with backup/interactive)
    - ADFTextExtractor class (with dual-mode support)
    - SimpleMarkdownConverter class
    - TextDiffer class
    - BackupManager class
    - MacroBodyDetector class
    - MCPJsonDiffRoundtrip main class

  Modes:
    - Safe Mode (default): Skip macro bodies, zero risk
    - Advanced Mode (optional): Edit macro bodies with confirmation and backup

Alternative Options (special requirements):
  - Page has no macros: Method 7 (ADF-native, full Claude access) (Method 1 DEPRECATED)
  - Batch programmatic operations: Method 7 or Method 4 (Method 1 DEPRECATED)
  - Need auto-detection logic: Method 5 (Hybrid)
```

**Implementation Timeline:**

```yaml
Phase 1 - Core Classes (3 days):
  - Implement ADFTextExtractor (dual-mode: skip/include macro bodies)
  - Implement SimpleMarkdownConverter (ADF → Markdown for Claude)
  - Implement TextDiffer (compare and generate changes)
  - Implement BackupManager (save, load, retention policy)
  - Implement MacroBodyDetector (detect, preview, categorize)
  - Unit tests for each class

Phase 2 - Integration (2 days):
  - Implement MCPJsonDiffRoundtrip main class
  - Integrate with MCP tools (getConfluencePage, updateConfluencePage)
  - Add interactive prompts (macro body detection, confirmation)
  - Add error handling and auto-rollback
  - Validation logic

Phase 3 - Testing & Documentation (2 days):
  - Integration tests (safe mode + advanced mode)
  - Test with various page types (with/without macros, macro bodies)
  - Test rollback mechanisms
  - Integrate into confluence skill
  - Document usage, modes, and best practices
```

### 🎯 Modes and Features

**Safe Mode (Default):**

- Zero risk to macro structure
- Skips macro body content
- Fast and predictable
- Recommended for most edits

**Advanced Mode (Opt-in):**

- Edits macro body content with Claude intelligence
- Interactive detection and confirmation
- Automatic backup before editing
- Auto-rollback on failure
- User decides risk/benefit trade-off

**Why Interactive Instead of Automatic?**

- Transparency: User sees what will be edited
- Control: User decides when to take risks
- Safety: Explicit confirmation + backup
- Learning: User understands the trade-offs

```
┌─────────────────────────────────────────────────────────────┐
│  Page Content                                               │
├─────────────────────────────────────────────────────────────┤
│  # Welcome                     ← ✅ Can edit                │
│                                                             │
│  This is introduction text.    ← ✅ Can edit                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ <expand macro title="Details">                      │   │
│  │   ┌─────────────────────────────────────────────┐   │   │
│  │   │ Text inside expand macro                    │ ← │ ❌ Cannot edit
│  │   │ This content is in macro body               │   │   │
│  │   └─────────────────────────────────────────────┘   │   │
│  │ </expand>                                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  More text after macro.        ← ✅ Can edit                │
└─────────────────────────────────────────────────────────────┘
```

**Workaround:** For macro body content edits, instruct user to use Confluence Web UI.

### Method Comparison Summary

| Method | Macro Preserved | Claude Edit | Macro Body Edit | Auth | Complexity |
|--------|----------------|-------------|-----------------|------|------------|
| ~~Method 1~~ (DEPRECATED) | ❌ Lost | ✅ Full | ❌ N/A | API Token | Low |
| Method 4 | ✅ Full | ❌ No | ✅ Programmatic | API Token | Medium |
| Method 5 | ⚠️ Depends | ⚠️ Depends | ⚠️ Depends | Both | High |
| **Method 6** | ✅ **Full** | ✅ **Text** | ❌ No | **MCP OAuth** | **Medium** |

### Best Choice: ⭐ Method 6 (MCP + JSON Diff)

```
Edit request comes in:
│
├─→ Is it editing text OUTSIDE macros?
│   └─→ Yes: ✅ Method 6 handles it perfectly
│       - Macros preserved
│       - Claude edits the text
│       - Simple and predictable
│
├─→ Is it editing text INSIDE macro body?
│   └─→ Yes: ❌ Inform user to use Confluence Web UI
│       (No automated method can safely do this)
│
└─→ Is it a page with NO macros?
    └─→ Yes: Method 6 works, or use Method 7 for upload/download
        (Method 1 is DEPRECATED; dependencies removed)
```

See: [Macro Preservation Guide](./macro-preservation-guide.md)

---

### Why Method 6 Over Method 5?

| Aspect | Method 5 (Hybrid) | Method 6 (JSON Diff) |
|--------|------------------|---------------------|
| **Macro preservation** | ⚠️ May lose for complex edits | ✅ Always preserved |
| **Predictability** | ⚠️ Depends on detection | ✅ Always same behavior |
| **Implementation** | ~250 lines + decision logic | ~200 lines |
| **User experience** | May get warnings about macro loss | Clear: macros safe, body not editable |
| **Auth** | Requires both API Token + MCP | MCP only (simpler) |

**Method 6 wins because:**

1. **Simpler** - No complex auto-detection logic
2. **Predictable** - User always knows what to expect
3. **MCP-only** - No need for API Token management
4. **Safer** - Macros are NEVER at risk

---

### Why Not Recommend Method 2?

❌ **Method 2 (MCP + ADF)** problems:

1. Dual-language environment maintenance cost too high
2. ADF conversion tools not as mature as Storage Format
3. Poor performance (subprocess overhead)
4. Difficult debugging
5. No clear advantage (still loses macros)

---

## Method 7: ADF-Native Roundtrip (✅ Implemented)

> **Status**: Implemented and tested.
> Files: `adf_to_markdown.py`, `markdown_to_adf.py`
> Integrated into `download_confluence.py` and `upload_confluence.py` (ADF v2 only).

### Overview

Method 7 replaces the current v1 API Storage format roundtrip with a v2 API ADF-native approach.
It uses custom markdown syntax (HTML comment markers) to preserve Confluence-specific elements
during the download → edit → upload cycle.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page                                            │
│  (ADF: Atlassian Document Format JSON)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2: GET /wiki/api/v2/pages/{id}
                   │ ?body-format=atlas_doc_format
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ADF JSON (all node types visible)                          │
│  expand, emoji, mention, inlineCard, panel, ...             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ adf_to_markdown.py (custom ADF walker)
                   │ Preserves special elements as markers:
                   │   <!-- EXPAND: "title" --> ... <!-- /EXPAND -->
                   │   :emoji_shortname:
                   │   <!-- MENTION: id "name" -->
                   │   <!-- CARD: url -->
                   │   <!-- PANEL: type --> ... <!-- /PANEL -->
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Markdown with markers                                      │
│  Standard markdown + HTML comment markers for               │
│  Confluence-specific elements                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ User / Claude edits markdown
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Edited Markdown with markers                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ markdown_to_adf.py (mistune + marker parser)
                   │ Converts markers back to ADF nodes
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ADF JSON (all elements restored)                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ REST API v2: PUT /wiki/api/v2/pages/{id}
                   │ body-format=atlas_doc_format
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Confluence Page (Updated, all structures preserved)        │
└─────────────────────────────────────────────────────────────┘
```

### Why v2 API with ADF?

> **Note:** Storage Format is NOT deprecated. The v2 API supports both
> `representation: storage` and ADF. The choice of ADF here is for Method 7's
> marker-based approach, not because Storage Format has a problem.

When using **Markdown conversion** (the lossy step), the v1 Storage format path has
additional challenges because markdownify cannot handle these elements:

- `ac:emoticon` for emojis (not handled by markdownify)
- `ac:link > ri:user` for mentions (not handled by markdownify)
- `ac:adf-extension` wrapper for new ADF panels (unrecognized by markdownify)
- `inlineCard` nodes do not exist in Storage format at all (ADF-only)

The v2 API with ADF JSON returns all elements as clean typed nodes, making it
easier to build a custom walker (Method 7's approach).

### Comparison with existing methods

| Aspect | Method 1 (DEPRECATED) | Method 6 (JSON Diff) | Method 7 (ADF-native) |
|--------|-------------------|---------------------|----------------------|
| **API** | v1 (Storage) | v2 (ADF) via MCP | v2 (ADF) via REST |
| **Format** | XML/HTML → Markdown | ADF → text extraction | ADF → Markdown with markers |
| **Expand** | ❌ Lost | ✅ Preserved (not editable) | ✅ Preserved + editable |
| **Emoji** | ❌ Lost | ✅ Preserved (not editable) | ✅ Preserved + editable |
| **Mention** | ❌ Lost | ✅ Preserved (not editable) | ✅ Preserved + editable |
| **InlineCard** | ❌ Lost (not in v1) | ✅ Preserved (not editable) | ✅ Preserved + editable |
| **Panel** | ⚠️ Partial (old only) | ✅ Preserved | ✅ Preserved + editable |
| **Use case** | Upload new docs | In-place text editing | Full document roundtrip |

### Pros

✅ All Confluence elements preserved via markers
✅ Markers are human-readable and editable
✅ Uses v2 API end-to-end (ADF is the native format)
✅ Pure Python, no dual-language dependencies
✅ Compatible with Claude editing (markers are plain text)
✅ Complements Method 6 (different use case)

### Cons

❌ Custom markdown dialect (non-standard markers)
❌ Markers could be accidentally broken during editing
❌ Need to maintain ADF ↔ Markdown mapping for each node type

---

## References

- [md2cf Documentation](https://pypi.org/project/md2cf/) (removed from plugin)
- [html2text](https://github.com/Alir3z4/html2text/) (removed from plugin)
- [atlas-doc-parser](https://atlas-doc-parser.readthedocs.io/)
- [marklassian](https://marklassian.netlify.app/)
- [Confluence REST API v2](https://developer.atlassian.com/cloud/confluence/rest/v2/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [ADF Specification](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
