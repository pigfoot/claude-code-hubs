# Development Guidelines for Confluence ADF Scripts

## Core Principles

### 1. Always Use PEP 723 Inline Metadata

**✅ Correct**:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
```

**❌ Wrong**: Using heredoc or inline Python without metadata

```bash
# DON'T DO THIS
uv run python3 << 'EOF'
import requests
...
EOF
```

**Why?**

- PEP 723 enables `uv run` to auto-manage dependencies
- Heredoc creates token generation overhead (discovered in performance analysis)
- Can't reuse scripts without metadata
- Harder to debug and maintain

### 2. Always Run with `uv run`

**✅ Correct**:

```bash
uv run scripts/add_table_row.py PAGE_ID --args...
```

**❌ Wrong**:

```bash
python3 scripts/add_table_row.py PAGE_ID --args...
cd scripts && python3 add_table_row.py PAGE_ID --args...
```

**Why?**

- `uv run` ensures correct dependency isolation
- Works consistently across environments
- Documented in SKILL.md

### 3. Support Recursive Search for Nested Structures

**Problem**: Confluence pages often have content nested in macros (expand panels, info boxes, etc.)

**Solution**: Use recursive search functions from `confluence_adf_utils.py`

**✅ Correct**:

```python
from confluence_adf_utils import find_table_recursive, find_list_recursive

# Finds tables even inside expand macros
table_node = find_table_recursive(adf, heading_text)

# Finds lists even inside panel macros
list_node = find_list_recursive(adf, heading_text, "bulletList")
```

**❌ Wrong**: Only searching top-level content

```python
# This misses content inside macros
content = adf.get("content", [])
for node in content:
    if node.get("type") == "table":
        ...
```

### 4. Performance: Avoid AI Tool Invocation Chains

**Problem Discovered**: MCP roundtrip takes ~13 minutes due to AI processing delays (91% of time)

**Root Cause**:

- AI tool invocation intervals: ~5-6 minutes between calls
- Token generation for large heredocs: significant overhead
- Multiple tool boundaries require full context processing

**Solution**: Single Python script with REST API

**✅ Correct**:

```python
# Single script does: auth → read → modify → write
# Total time: ~1.2 seconds
def main():
    base_url, auth = get_auth()
    page_data = get_page_adf(base_url, auth, page_id)
    # ... modify ...
    update_page_adf(base_url, auth, page_id, title, adf, version)
```

**❌ Wrong**: Multiple MCP tool calls through Claude

```
MCP Read → AI thinks → Bash heredoc → AI thinks → Python → AI thinks → MCP Write
Total time: ~13 minutes (782 seconds)
```

### 5. Reuse Shared Utilities

**✅ Correct**:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    get_auth,
    get_page_adf,
    update_page_adf,
    find_table_recursive,
)
```

**❌ Wrong**: Duplicating code in every script

```python
# Don't copy-paste get_auth(), get_page_adf(), etc.
# Use the shared library!
```

### 6. Always Provide --dry-run Option

**Template**:

```python
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show what would be done without actually updating"
)

# In main():
if args.dry_run:
    print("\n🔍 Dry run - would do:")
    print(f"   Action: {description}")
    print("\n✅ Dry run complete (no changes made)")
    return

# Otherwise proceed with update
result = update_page_adf(...)
```

## Script Template

Use this template for new ADF modification scripts:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Brief description of what this script does.

Usage:
    uv run script_name.py PAGE_ID --param value
"""

import argparse
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    get_auth,
    get_page_adf,
    update_page_adf,
    # Import other helpers as needed
)


def modify_page(adf, **kwargs):
    """
    Modify the ADF document.

    Returns:
        True if successful, False otherwise
    """
    # Your modification logic here
    # Use recursive search functions for nested content
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Short description"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    # Add your arguments
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        print(f"📖 Reading page {args.page_id}...")
        page_data = get_page_adf(base_url, auth, args.page_id)

        title = page_data.get("title", "")
        version = page_data.get("version", {}).get("number", 1)

        # Parse ADF body
        import json
        body_value = page_data.get("body", {}).get("atlas_doc_format", {}).get("value")
        adf = json.loads(body_value) if isinstance(body_value, str) else body_value

        # Modify
        success = modify_page(adf, **vars(args))
        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n✅ Dry run complete (no changes made)")
            return

        # Update
        print(f"📝 Updating page...")
        result = update_page_adf(base_url, auth, args.page_id, title, adf, version)

        print(f"✅ Page updated to version {result['version']['number']}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Testing Checklist

Before committing a new script:

- [ ] Uses PEP 723 inline metadata
- [ ] Imports from `confluence_adf_utils.py`
- [ ] Uses recursive search functions (when applicable)
- [ ] Provides `--dry-run` option
- [ ] Tested with `--dry-run` successfully
- [ ] Tested actual update successfully
- [ ] Added to SKILL.md Utility Scripts table
- [ ] No Chinese text in code/comments/docs
- [ ] Execution time documented (~1s for structural mods)

## Common Mistakes to Avoid

### ❌ Using Heredoc for Python

```bash
# DON'T
uv run python3 << 'EOF'
import requests
...
EOF
```

### ❌ Only Searching Top-Level Content

```python
# DON'T - misses content in expand/panel macros
content = adf.get("content", [])
for node in content:
    if node.get("type") == "table":
        ...
```

### ❌ Running Without uv

```bash
# DON'T
python3 scripts/add_table_row.py ...

# DO
uv run scripts/add_table_row.py ...
```

### ❌ Duplicating Core Logic

```python
# DON'T - copy-paste get_auth(), get_page_adf(), etc.
# DO - import from confluence_adf_utils
```

### ❌ Creating Temporary Analysis Scripts

```bash
# DON'T - create one-off scripts in /tmp/
uv run /tmp/analyze_gemini_page.py
uv run /tmp/show_all_blocks.py

# DO - use the existing analyze_page.py tool
uv run scripts/analyze_page.py PAGE_ID
uv run scripts/analyze_page.py PAGE_ID --type codeBlock
```

**Why?**

- Temporary scripts are not reusable
- Each time creates unnecessary overhead
- `analyze_page.py` is built for this purpose, with proper features:
  - Filters by component type
  - Shows location context (which heading, inside what macro)
  - Suggests which modification tool to use
  - Properly structured and documented

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Structural modifications | ~1-2 seconds | Using REST API scripts |
| Document upload | ~5-10 seconds | Depends on size/images |
| MCP roundtrip | ~13 minutes | ⚠️ Too slow, avoid for structural mods |

## Related Documentation

- [README_ADF_UTILS.md](README_ADF_UTILS.md) - API reference for utility functions
- [SKILL.md](../SKILL.md) - User-facing documentation
- [../references/comparison-tables.md](../references/comparison-tables.md) - Performance analysis
