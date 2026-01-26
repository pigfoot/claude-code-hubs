#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add line to code block in Confluence page using REST API (fast method)

Usage:
    uv run add_to_codeblock.py PAGE_ID \
        --search-text "brew install uv" \
        --add-line "brew install node" \
        --position after
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
)


def find_and_update_codeblock(node, search_text, add_line, position):
    """
    Recursively find and update code block containing search text.

    Returns:
        True if found and updated, False otherwise
    """
    if isinstance(node, dict):
        if node.get("type") == "codeBlock":
            # Get code content
            code_content = ""
            text_nodes = node.get("content", [])

            for text_node in text_nodes:
                if text_node.get("type") == "text":
                    code_content = text_node.get("text", "")
                    break

            # Check if search text is in this code block
            if search_text in code_content:
                # Add the new line
                lines = code_content.split('\n')
                new_lines = []

                for line in lines:
                    if position == "before" and search_text in line:
                        new_lines.append(add_line)
                        new_lines.append(line)
                    elif position == "after" and search_text in line:
                        new_lines.append(line)
                        new_lines.append(add_line)
                    else:
                        new_lines.append(line)

                # Update the text node
                for text_node in text_nodes:
                    if text_node.get("type") == "text":
                        text_node["text"] = '\n'.join(new_lines)
                        break

                return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_update_codeblock(value, search_text, add_line, position):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_update_codeblock(item, search_text, add_line, position):
                return True

    return False


def add_to_codeblock(adf, search_text, add_line, position="after"):
    """
    Add line to code block containing search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for in code blocks
        add_line: Line to add
        position: "after" or "before"

    Returns:
        True if successful, False otherwise
    """
    if find_and_update_codeblock(adf, search_text, add_line, position):
        print(f"✅ Added line to code block {position} '{search_text}'")
        return True
    else:
        print(f"❌ Could not find code block containing: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add line to code block in Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for in code blocks (e.g., 'brew install uv')"
    )
    parser.add_argument(
        "--add-line",
        required=True,
        help="Line to add (e.g., 'brew install node')"
    )
    parser.add_argument(
        "--position",
        choices=["before", "after"],
        default="after",
        help="Add line before or after search text (default: after)"
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

        # Add to code block
        print(f"🔍 Finding code block with '{args.search_text}'...")
        success = add_to_codeblock(
            adf,
            args.search_text,
            args.add_line,
            args.position
        )

        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n🔍 Dry run - would add:")
            print(f"   Search text: {args.search_text}")
            print(f"   Add line: {args.add_line}")
            print(f"   Position: {args.position}")
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
            "Added line to code block via Python REST API"
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
