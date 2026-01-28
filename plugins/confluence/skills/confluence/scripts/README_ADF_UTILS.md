# Confluence ADF Utils - Developer Guide

`confluence_adf_utils.py` provides shared functions to quickly build new Confluence structural modification tools.

## Why Use This Utility Library?

**Performance Comparison**:

- MCP Roundtrip (via Claude): ~13 minutes
- Python REST API Direct: **~1.2 seconds** (650x speedup)

**Core Advantages**:

- Avoids AI tool invocation delays between calls (accounts for 91% of total time)
- Direct ADF JSON manipulation for precise structural control
- Lightweight dependencies (only `requests` and `python-dotenv`)

## Quick Start

### 1. Basic Usage - Read and Update Pages

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
import sys
from pathlib import Path

# Import utils
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import get_auth, get_page_adf, update_page_adf

# Get credentials
base_url, auth = get_auth()

# Read page
page_data = get_page_adf(base_url, auth, "PAGE_ID")
title = page_data["title"]
version = page_data["version"]["number"]

# Get ADF body
import json
body_value = page_data["body"]["atlas_doc_format"]["value"]
adf = json.loads(body_value) if isinstance(body_value, str) else body_value

# Modify ADF (your custom logic here)
# ...

# Write back
result = update_page_adf(base_url, auth, "PAGE_ID", title, adf, version, "My update")
print(f"Updated to version {result['version']['number']}")
```

### 2. Using Convenience Functions - Automatic Read/Write

```python
from confluence_adf_utils import quick_update_page, insert_table_row

def add_my_row(adf, page_data):
    return insert_table_row(
        adf,
        table_heading="My Table",
        after_row_containing="GitHub",
        new_row_cells=["Col1", "Col2", "Col3"]
    )

result = quick_update_page("PAGE_ID", add_my_row, "Added new row")
```

## Core Function Reference

### Authentication & I/O

#### `get_auth() -> Tuple[str, Tuple[str, str]]`

Get authentication credentials from environment variables.

**Environment Variables**:

- `CONFLUENCE_URL` - Confluence base URL (e.g., `https://company.atlassian.net/wiki`)
- `CONFLUENCE_USER` - Email address
- `CONFLUENCE_API_TOKEN` - API token from <https://id.atlassian.com/manage-profile/security/api-tokens>

#### `get_page_adf(base_url, auth, page_id) -> Dict`

Read page content in ADF format.

#### `update_page_adf(base_url, auth, page_id, title, body, version, version_message=None) -> Dict`

Update page content in ADF format.

### Navigation & Finding

#### `find_heading_index(content, heading_text) -> Optional[int]`

Find a heading containing the specified text in the content array.

#### `find_table_after_heading(content, heading_text) -> Optional[Tuple[int, Dict]]`

Find the first table after a specified heading. Returns `(table_index, table_node)` or `None`.

#### `find_row_containing_text(table_node, search_text) -> Optional[int]`

Find the first row in a table whose first cell contains the specified text.

### Construction & Modification

#### `create_table_row(cells: List[str]) -> Dict`

Create a new ADF table row node.

**Example**:

```python
new_row = create_table_row(["Cell 1", "Cell 2", "Cell 3"])
```

#### `insert_table_row(adf, table_heading, after_row_containing, new_row_cells) -> bool`

Insert a new row into a specified table.

**Parameters**:

- `adf`: Complete ADF document
- `table_heading`: Heading text before the table
- `after_row_containing`: Text in the first cell of the row to insert after
- `new_row_cells`: Cell contents for the new row (list of strings)

**Returns**: `True` if successful, `False` if failed

### Convenience Functions

#### `quick_update_page(page_id, modify_fn, version_message=None) -> Dict`

Automatically handles the read → modify → write workflow.

**Parameters**:

- `page_id`: Confluence page ID
- `modify_fn`: Function that accepts `(adf, page_data)` and returns `True/False`
- `version_message`: Version update message (optional)

**Example**:

```python
def my_modification(adf, page_data):
    # Your custom logic
    content = adf.get("content", [])
    # ... modify content ...
    return True  # Success

result = quick_update_page("123456", my_modification, "My changes")
```

## Building New Tools - Examples

### Example 1: Add List Item

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["requests>=2.31.0", "python-dotenv>=1.0.0"]
# ///
"""Add list item to Confluence page"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import quick_update_page, find_heading_index

def add_list_item(adf, page_data, heading_text, item_text, insert_position="end"):
    """Add item to bulletList after specified heading"""
    content = adf.get("content", [])

    # Find heading
    heading_idx = find_heading_index(content, heading_text)
    if heading_idx is None:
        print(f"❌ Could not find heading: {heading_text}")
        return False

    # Find bulletList after heading
    list_node = None
    for i in range(heading_idx + 1, len(content)):
        if content[i].get("type") == "bulletList":
            list_node = content[i]
            break

    if list_node is None:
        print(f"❌ Could not find bulletList after heading")
        return False

    # Create new list item
    import os
    new_item = {
        "type": "listItem",
        "attrs": {"localId": f"item-{os.urandom(4).hex()}"},
        "content": [
            {
                "type": "paragraph",
                "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
                "content": [{"type": "text", "text": item_text}]
            }
        ]
    }

    # Insert
    if insert_position == "end":
        list_node["content"].append(new_item)
    else:
        list_node["content"].insert(0, new_item)

    print(f"✅ Added list item")
    return True

def main():
    parser = argparse.ArgumentParser(description="Add list item to Confluence")
    parser.add_argument("page_id", help="Page ID")
    parser.add_argument("--before-heading", required=True, help="Heading before the list")
    parser.add_argument("--item", required=True, help="Item text")
    parser.add_argument("--position", choices=["start", "end"], default="end")
    args = parser.parse_args()

    def modify(adf, page_data):
        return add_list_item(adf, page_data, args.before_heading, args.item, args.position)

    result = quick_update_page(args.page_id, modify, "Added list item")
    print(f"✅ Updated to version {result['version']['number']}")

if __name__ == "__main__":
    main()
```

**Usage**:

```bash
uv run scripts/add_list_item.py PAGE_ID \
  --before-heading "Requirements" \
  --item "New security requirement" \
  --position end
```

### Example 2: Insert Info Panel

```python
def add_info_panel(adf, page_data, after_heading, panel_type, content_text):
    """Add info/warning/note panel after specified heading"""
    import os

    content = adf.get("content", [])
    heading_idx = find_heading_index(content, after_heading)

    if heading_idx is None:
        return False

    # Create panel node
    panel = {
        "type": "panel",
        "attrs": {
            "panelType": panel_type,  # "info", "warning", "note", "success"
            "localId": f"panel-{os.urandom(4).hex()}"
        },
        "content": [
            {
                "type": "paragraph",
                "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
                "content": [{"type": "text", "text": content_text}]
            }
        ]
    }

    # Insert after heading
    content.insert(heading_idx + 1, panel)
    return True
```

## ADF Structure Quick Reference

### Common Node Types

```python
# Document root
{"type": "doc", "content": [...]}

# Heading (level 1-6)
{"type": "heading", "attrs": {"level": 2}, "content": [...]}

# Paragraph
{"type": "paragraph", "content": [{"type": "text", "text": "..."}]}

# Table
{"type": "table", "content": [
    {"type": "tableRow", "content": [
        {"type": "tableCell", "content": [...]}
    ]}
]}

# Bullet List
{"type": "bulletList", "content": [
    {"type": "listItem", "content": [...]}
]}

# Panel (info/warning/note/success)
{"type": "panel", "attrs": {"panelType": "info"}, "content": [...]}
```

### LocalId Generation

Every ADF node needs a unique `localId`:

```python
import os
local_id = f"node-{os.urandom(4).hex()}"  # e.g., "node-a3f2b1c4"
```

## Development Workflow Recommendations

1. **Understand Target Structure**

   ```bash
   # Read page and observe ADF structure
   uv run python3 -c "
   from confluence_adf_utils import get_auth, get_page_adf
   import json
   base_url, auth = get_auth()
   page = get_page_adf(base_url, auth, 'PAGE_ID')
   adf = json.loads(page['body']['atlas_doc_format']['value'])
   print(json.dumps(adf, indent=2))
   " | less
   ```

2. **Build Modification Function**
   - Write modification logic first (pure JSON operations)
   - Wrap with `quick_update_page`

3. **Test**

   ```bash
   # Test with dry-run first
   uv run scripts/my_new_tool.py PAGE_ID --dry-run

   # Execute after confirmation
   uv run scripts/my_new_tool.py PAGE_ID
   ```

## Error Handling

```python
from confluence_adf_utils import quick_update_page

def my_modification(adf, page_data):
    try:
        # Your logic
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

try:
    result = quick_update_page("PAGE_ID", my_modification)
except ValueError as e:
    print(f"❌ Update failed: {e}")
    sys.exit(1)
```

## Related Documentation

- [SKILL.md](../SKILL.md) - Complete usage guide
- [comparison-tables.md](../references/comparison-tables.md) - Performance analysis
- [Official ADF Documentation](https://developer.atlassian.com/cloud/confluence/apis/document/structure/)

## Contributing New Tools

Contributions of new structural modification tools are welcome!

**Implemented Tools** ✅:

- [x] `add_list_item.py` - Add bullet/numbered list items
- [x] `add_panel.py` - Insert info/warning/note/success panels
- [x] `insert_section.py` - Insert new sections (heading + content)

**Future Tool Ideas** 💡:

- [ ] `duplicate_table.py` - Duplicate entire tables
- [ ] `reorder_sections.py` - Reorder sections
- [ ] `add_code_block.py` - Insert code blocks with syntax highlighting
- [ ] `add_attachment.py` - Upload file attachments
- [ ] `create_toc.py` - Generate table of contents

Each new tool should:

1. Use PEP 723 inline metadata (`# /// script`)
2. Reuse core functions from `confluence_adf_utils.py`
3. Provide `--dry-run` option
4. Add entry to SKILL.md Utility Scripts table
