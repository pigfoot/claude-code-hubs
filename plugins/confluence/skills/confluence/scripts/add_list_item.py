#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add list item to Confluence page using REST API (fast method)

Avoids MCP + Claude tool invocation delays by using Python REST API directly.

Usage:
    uv run add_list_item.py PAGE_ID \
        --after-heading "Requirements" \
        --item "New security requirement" \
        --position end
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    get_auth,
    get_page_adf,
    update_page_adf,
    find_list_recursive,
)


def add_list_item(adf, heading_text, item_text, insert_position="end", list_type="bullet"):
    """
    Add item to a list after specified heading (supports recursive search in macros).

    Args:
        adf: ADF document
        heading_text: Heading text before the list
        item_text: Text for the new list item
        insert_position: "start" or "end"
        list_type: "bullet" or "numbered"

    Returns:
        True if successful, False otherwise
    """
    target_type = "bulletList" if list_type == "bullet" else "orderedList"

    # Find list after heading (supports nested in expand/panel macros)
    list_node = find_list_recursive(adf, heading_text, target_type)

    if list_node is None:
        print(f"❌ Could not find {list_type} list after heading: {heading_text}")
        return False

    # Create new list item
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
        print(f"✅ Added list item at end")
    else:
        list_node["content"].insert(0, new_item)
        print(f"✅ Added list item at start")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add list item to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--after-heading",
        required=True,
        help="Heading text before the list (e.g., 'Requirements')"
    )
    parser.add_argument(
        "--item",
        required=True,
        help="Text for the new list item"
    )
    parser.add_argument(
        "--position",
        choices=["start", "end"],
        default="end",
        help="Insert at start or end of list (default: end)"
    )
    parser.add_argument(
        "--list-type",
        choices=["bullet", "numbered"],
        default="bullet",
        help="Type of list (default: bullet)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    try:
        # Get authentication
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        # Get page
        print(f"📖 Reading page {args.page_id}...")
        page_data = get_page_adf(base_url, auth, args.page_id)

        title = page_data.get("title", "")
        version = page_data.get("version", {}).get("number", 1)
        print(f"   Title: {title}")
        print(f"   Current version: {version}")

        # Parse ADF body
        import json
        body_value = page_data.get("body", {}).get("atlas_doc_format", {}).get("value")
        if isinstance(body_value, str):
            adf = json.loads(body_value)
        else:
            adf = body_value

        # Add list item
        print(f"🔍 Finding list after heading '{args.after_heading}'...")
        success = add_list_item(
            adf,
            args.after_heading,
            args.item,
            args.position,
            args.list_type
        )

        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n🔍 Dry run - would add:")
            print(f"   Heading: {args.after_heading}")
            print(f"   List type: {args.list_type}")
            print(f"   Position: {args.position}")
            print(f"   Item: {args.item}")
            print("\n✅ Dry run complete (no changes made)")
            return

        # Update page
        print(f"📝 Updating page...")
        result = update_page_adf(
            base_url,
            auth,
            args.page_id,
            title,
            adf,
            version,
            "Added list item via Python REST API"
        )

        new_version = result.get("version", {}).get("number")
        print(f"✅ Page updated successfully!")
        print(f"   New version: {new_version}")
        print(f"   URL: {base_url}/pages/{args.page_id}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
