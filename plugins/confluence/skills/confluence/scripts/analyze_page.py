#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Analyze Confluence page structure (ADF format) to understand its components.

This tool helps you decide which modification script to use by showing all
components in the page, including those nested inside macros.

Usage:
    # Show all components
    uv run scripts/analyze_page.py PAGE_ID

    # Filter by component type
    uv run scripts/analyze_page.py PAGE_ID --type table
    uv run scripts/analyze_page.py PAGE_ID --type codeBlock
    uv run scripts/analyze_page.py PAGE_ID --type bulletList

    # Show structure only (no content preview)
    uv run scripts/analyze_page.py PAGE_ID --structure-only
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import get_auth, get_page_adf


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_text_from_node(node: Dict) -> str:
    """Extract plain text from ADF node."""
    if not isinstance(node, dict):
        return ""

    if node.get("type") == "text":
        return node.get("text", "")

    text_parts = []
    content = node.get("content", [])
    for child in content:
        text_parts.append(extract_text_from_node(child))

    return "".join(text_parts)


def find_nearest_heading(content: List[Dict], target_index: int) -> Optional[str]:
    """Find the nearest heading before target_index."""
    for i in range(target_index - 1, -1, -1):
        node = content[i]
        if node.get("type") == "heading":
            return extract_text_from_node(node)
    return None


def analyze_table(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a table node."""
    rows = node.get("content", [])
    row_count = len([r for r in rows if r.get("type") == "tableRow"])

    # Get first cell of first row as preview
    preview = ""
    if rows:
        first_row = rows[0]
        cells = first_row.get("content", [])
        if cells:
            preview = extract_text_from_node(cells[0])

    return {
        "type": "table",
        "rows": row_count,
        "preview": truncate_text(preview),
        "context": context,
        "tool": "add_table_row.py"
    }


def analyze_list(node: Dict, list_type: str, context: str = "") -> Dict[str, Any]:
    """Analyze a list node (bullet or ordered)."""
    items = node.get("content", [])
    item_count = len([i for i in items if i.get("type") == "listItem"])

    # Get first item as preview
    preview = ""
    if items:
        preview = extract_text_from_node(items[0])

    return {
        "type": list_type,
        "items": item_count,
        "preview": truncate_text(preview),
        "context": context,
        "tool": "add_list_item.py"
    }


def analyze_codeblock(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a code block node."""
    lang = node.get("attrs", {}).get("language", "plain")
    code_text = ""

    for text_node in node.get("content", []):
        if text_node.get("type") == "text":
            code_text = text_node.get("text", "")
            break

    lines = code_text.split('\n')
    first_line = lines[0] if lines else ""

    return {
        "type": "codeBlock",
        "language": lang,
        "lines": len(lines),
        "preview": truncate_text(first_line),
        "context": context,
        "tool": "add_to_codeblock.py"
    }


def analyze_panel(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a panel node."""
    panel_type = node.get("attrs", {}).get("panelType", "info")
    content_text = extract_text_from_node(node)

    return {
        "type": "panel",
        "panelType": panel_type,
        "preview": truncate_text(content_text),
        "context": context,
        "tool": "add_panel.py"
    }


def analyze_heading(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a heading node."""
    level = node.get("attrs", {}).get("level", 1)
    text = extract_text_from_node(node)

    return {
        "type": "heading",
        "level": level,
        "text": text,
        "context": context,
        "tool": "insert_section.py (to add section after this heading)"
    }


def analyze_expand(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze an expand macro."""
    title = node.get("attrs", {}).get("title", "(no title)")

    return {
        "type": "expand",
        "title": title,
        "context": context,
        "tool": "(contains nested content - see child components below)"
    }


def analyze_blockquote(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a blockquote node."""
    quote_text = extract_text_from_node(node)

    return {
        "type": "blockquote",
        "preview": truncate_text(quote_text),
        "context": context,
        "tool": "add_blockquote.py"
    }


def analyze_rule(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a horizontal rule node."""
    return {
        "type": "rule",
        "context": context,
        "tool": "add_rule.py"
    }


def analyze_media_single(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a mediaSingle (image) node."""
    media_node = node.get("content", [{}])[0]
    media_id = media_node.get("attrs", {}).get("id", "unknown")

    return {
        "type": "mediaSingle",
        "media_id": media_id,
        "context": context,
        "tool": "add_media.py"
    }


def analyze_media_group(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a mediaGroup (multiple images) node."""
    media_count = len(node.get("content", []))

    return {
        "type": "mediaGroup",
        "images": media_count,
        "context": context,
        "tool": "add_media_group.py"
    }


def analyze_nested_expand(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a nestedExpand node."""
    title = node.get("attrs", {}).get("title", "(no title)")

    return {
        "type": "nestedExpand",
        "title": title,
        "context": context,
        "tool": "add_nested_expand.py"
    }


def analyze_inline_card(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze an inlineCard node."""
    url = node.get("attrs", {}).get("url", "")

    return {
        "type": "inlineCard",
        "url": truncate_text(url, 50),
        "context": context,
        "tool": "add_inline_card.py"
    }


def analyze_status(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a status label (inline) node."""
    status_text = node.get("attrs", {}).get("text", "")
    status_color = node.get("attrs", {}).get("color", "neutral")

    return {
        "type": "status",
        "text": status_text,
        "color": status_color,
        "context": context,
        "tool": "add_status.py"
    }


def analyze_mention(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a mention (inline) node."""
    mention_text = node.get("attrs", {}).get("text", "")

    return {
        "type": "mention",
        "text": mention_text,
        "context": context,
        "tool": "add_mention.py"
    }


def analyze_date(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze a date (inline) node."""
    timestamp = node.get("attrs", {}).get("timestamp", "")

    return {
        "type": "date",
        "timestamp": timestamp,
        "context": context,
        "tool": "add_date.py"
    }


def analyze_emoji(node: Dict, context: str = "") -> Dict[str, Any]:
    """Analyze an emoji (inline) node."""
    emoji_shortname = node.get("attrs", {}).get("shortName", "")

    return {
        "type": "emoji",
        "shortName": emoji_shortname,
        "context": context,
        "tool": "add_emoji.py"
    }


def find_components_recursive(
    node,
    components: List[Dict],
    filter_type: Optional[str] = None,
    context: str = "",
    parent_headings: List[str] = None
):
    """
    Recursively find all components in ADF document.

    Args:
        node: ADF node to search
        components: List to accumulate found components
        filter_type: Optional type filter (e.g., "table", "codeBlock")
        context: Description of where this component is located
        parent_headings: List of parent heading texts
    """
    if parent_headings is None:
        parent_headings = []

    if isinstance(node, dict):
        node_type = node.get("type")

        # Build context string
        location = ""
        if parent_headings:
            location = f"After heading: '{parent_headings[-1]}'"
        if context:
            location = f"{location} | {context}" if location else context

        # Analyze specific node types
        if node_type == "heading":
            # Track heading for context
            heading_text = extract_text_from_node(node)
            if not filter_type or filter_type == "heading":
                components.append(analyze_heading(node, location))
            # Add to parent_headings for subsequent nodes
            parent_headings = parent_headings + [heading_text]

        elif node_type == "table":
            if not filter_type or filter_type == "table":
                components.append(analyze_table(node, location))

        elif node_type == "bulletList":
            if not filter_type or filter_type == "bulletList":
                components.append(analyze_list(node, "bulletList", location))

        elif node_type == "orderedList":
            if not filter_type or filter_type == "orderedList":
                components.append(analyze_list(node, "orderedList", location))

        elif node_type == "codeBlock":
            if not filter_type or filter_type == "codeBlock":
                components.append(analyze_codeblock(node, location))

        elif node_type == "panel":
            if not filter_type or filter_type == "panel":
                components.append(analyze_panel(node, location))

        elif node_type == "expand":
            if not filter_type or filter_type == "expand":
                components.append(analyze_expand(node, location))
            # Recurse into expand content with updated context
            expand_context = f"Inside expand: '{node.get('attrs', {}).get('title', 'no title')}'"
            if context:
                expand_context = f"{context} > {expand_context}"

        elif node_type == "blockquote":
            if not filter_type or filter_type == "blockquote":
                components.append(analyze_blockquote(node, location))

        elif node_type == "rule":
            if not filter_type or filter_type == "rule":
                components.append(analyze_rule(node, location))

        elif node_type == "mediaSingle":
            if not filter_type or filter_type == "mediaSingle":
                components.append(analyze_media_single(node, location))

        elif node_type == "mediaGroup":
            if not filter_type or filter_type == "mediaGroup":
                components.append(analyze_media_group(node, location))

        elif node_type == "nestedExpand":
            if not filter_type or filter_type == "nestedExpand":
                components.append(analyze_nested_expand(node, location))

        elif node_type == "inlineCard":
            if not filter_type or filter_type == "inlineCard":
                components.append(analyze_inline_card(node, location))

        elif node_type == "status":
            if not filter_type or filter_type == "status":
                components.append(analyze_status(node, location))

        elif node_type == "mention":
            if not filter_type or filter_type == "mention":
                components.append(analyze_mention(node, location))

        elif node_type == "date":
            if not filter_type or filter_type == "date":
                components.append(analyze_date(node, location))

        elif node_type == "emoji":
            if not filter_type or filter_type == "emoji":
                components.append(analyze_emoji(node, location))

        # Recursively search nested structures
        for key, value in node.items():
            new_context = context
            if node_type == "expand":
                new_context = f"Inside expand: '{node.get('attrs', {}).get('title', 'no title')}'"
                if context:
                    new_context = f"{context} > {new_context}"

            find_components_recursive(
                value,
                components,
                filter_type,
                new_context,
                parent_headings
            )

    elif isinstance(node, list):
        for item in node:
            find_components_recursive(
                item,
                components,
                filter_type,
                context,
                parent_headings
            )


def print_component(comp: Dict, show_content: bool = True):
    """Print a component in a readable format."""
    comp_type = comp["type"]
    context = comp.get("context", "")
    tool = comp.get("tool", "")

    print(f"\n  Type: {comp_type}")
    if context:
        print(f"  Location: {context}")

    if comp_type == "table":
        print(f"  Rows: {comp['rows']}")
        if show_content:
            print(f"  First cell: {comp['preview']}")

    elif comp_type in ["bulletList", "orderedList"]:
        print(f"  Items: {comp['items']}")
        if show_content:
            print(f"  First item: {comp['preview']}")

    elif comp_type == "codeBlock":
        print(f"  Language: {comp['language']}")
        print(f"  Lines: {comp['lines']}")
        if show_content:
            print(f"  First line: {comp['preview']}")

    elif comp_type == "panel":
        print(f"  Panel type: {comp['panelType']}")
        if show_content:
            print(f"  Content: {comp['preview']}")

    elif comp_type == "heading":
        print(f"  Level: {comp['level']}")
        print(f"  Text: {comp['text']}")

    elif comp_type == "expand":
        print(f"  Title: {comp['title']}")

    elif comp_type == "blockquote":
        if show_content:
            print(f"  Quote: {comp['preview']}")

    elif comp_type == "rule":
        print(f"  (Horizontal divider line)")

    elif comp_type == "mediaSingle":
        print(f"  Media ID: {comp['media_id']}")

    elif comp_type == "mediaGroup":
        print(f"  Images: {comp['images']}")

    elif comp_type == "nestedExpand":
        print(f"  Title: {comp['title']}")

    elif comp_type == "inlineCard":
        print(f"  URL: {comp['url']}")

    elif comp_type == "status":
        print(f"  Text: {comp['text']}")
        print(f"  Color: {comp['color']}")

    elif comp_type == "mention":
        print(f"  Text: {comp['text']}")

    elif comp_type == "date":
        print(f"  Timestamp: {comp['timestamp']}")

    elif comp_type == "emoji":
        print(f"  Shortname: {comp['shortName']}")

    if tool:
        print(f"  → Modify with: {tool}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Confluence page structure (helps decide which script to use)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--type",
        choices=[
            "table", "bulletList", "orderedList", "codeBlock", "panel", "heading", "expand",
            "blockquote", "rule", "mediaSingle", "mediaGroup", "nestedExpand", "inlineCard",
            "status", "mention", "date", "emoji"
        ],
        help="Filter by component type"
    )
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help="Show structure only (no content preview)"
    )

    args = parser.parse_args()

    try:
        # Get authentication
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        # Get page
        print(f"📖 Reading page {args.page_id}...\n")
        page_data = get_page_adf(base_url, auth, args.page_id)

        title = page_data.get("title", "")
        version = page_data.get("version", {}).get("number", 1)

        print("=" * 80)
        print(f"Page: {title}")
        print(f"Version: {version}")
        print(f"URL: {base_url}/pages/{args.page_id}")
        print("=" * 80)

        # Parse ADF body
        body_value = page_data.get("body", {}).get("atlas_doc_format", {}).get("value")
        adf = json.loads(body_value) if isinstance(body_value, str) else body_value

        # Find all components
        components = []
        find_components_recursive(adf, components, args.type)

        # Print results
        if not components:
            if args.type:
                print(f"\n❌ No components of type '{args.type}' found")
            else:
                print("\n❌ No supported components found")
            return

        # Group by type
        by_type = {}
        for comp in components:
            comp_type = comp["type"]
            if comp_type not in by_type:
                by_type[comp_type] = []
            by_type[comp_type].append(comp)

        # Print summary
        print(f"\n📊 Found {len(components)} component(s):")
        for comp_type, comps in sorted(by_type.items()):
            print(f"  - {comp_type}: {len(comps)}")

        # Print details
        print("\n" + "=" * 80)
        print("COMPONENT DETAILS")
        print("=" * 80)

        for i, comp in enumerate(components, 1):
            print(f"\n[{i}] ", end="")
            print_component(comp, show_content=not args.structure_only)

        print("\n" + "=" * 80)
        print("AVAILABLE MODIFICATION TOOLS (15 total)")
        print("=" * 80)
        print("""
  Block Elements:
    add_table_row.py          - Add row to table
    add_list_item.py          - Add item to bullet/ordered list
    add_to_codeblock.py       - Add line to code block
    add_panel.py              - Add info/warning/note/success panel
    add_blockquote.py         - Add blockquote (citation)
    add_rule.py               - Add horizontal rule (divider)
    add_media.py              - Add single image
    add_media_group.py        - Add image group (multiple images)
    add_nested_expand.py      - Add nested expand panel
    insert_section.py         - Insert new section (heading + content)

  Inline Elements:
    add_status.py             - Add status label (TODO/DONE/etc.)
    add_mention.py            - Add @mention (notify user)
    add_date.py               - Add date (timestamp)
    add_emoji.py              - Add emoji
    add_inline_card.py        - Add inline card (URL preview)

  Run with: uv run scripts/<script_name> PAGE_ID [options]
  Use --help to see script-specific options
        """)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
