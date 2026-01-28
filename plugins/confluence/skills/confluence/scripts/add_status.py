#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add status label (TODO/DONE/IN PROGRESS) inline in Confluence page

Status labels are inline nodes commonly used for task tracking.

Usage:
    uv run add_status.py PAGE_ID --search-text "Implement feature" --status TODO
    uv run add_status.py PAGE_ID --search-text "Review code" --status "IN PROGRESS" --color blue
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import execute_modification


def find_and_add_status_recursive(node, search_text, status_text, status_color):
    """
    Recursively find paragraph/listItem containing search text and add status inline.

    Returns:
        True if found and updated, False otherwise
    """
    if isinstance(node, dict):
        node_type = node.get("type")

        # Check if this is a paragraph or listItem with text content
        if node_type in ["paragraph", "listItem"]:
            content = node.get("content", [])

            # Check if search_text is in this node
            for i, child in enumerate(content):
                if child.get("type") == "text" and search_text in child.get("text", ""):
                    # Found it! Add status inline after the text
                    status_node = {
                        "type": "status",
                        "attrs": {
                            "text": status_text,
                            "color": status_color,
                            "localId": f"status-{os.urandom(4).hex()}",
                        },
                    }

                    # Add space before status
                    space_node = {"type": "text", "text": " "}

                    # Insert after the text node
                    content.insert(i + 1, space_node)
                    content.insert(i + 2, status_node)

                    return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_add_status_recursive(
                value, search_text, status_text, status_color
            ):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_add_status_recursive(
                item, search_text, status_text, status_color
            ):
                return True

    return False


def add_status(adf, search_text, status_text, status_color="neutral"):
    """
    Add status label inline after search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for
        status_text: Status label text (e.g., "TODO", "DONE")
        status_color: Status color (neutral, purple, blue, red, yellow, green)

    Returns:
        True if successful, False otherwise
    """
    if find_and_add_status_recursive(adf, search_text, status_text, status_color):
        print(f"✅ Added status '{status_text}' after '{search_text}'")
        return True
    else:
        print(f"❌ Could not find text: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add status label inline in Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for (status will be added after this text)",
    )
    parser.add_argument(
        "--status",
        required=True,
        help="Status text (e.g., 'TODO', 'DONE', 'IN PROGRESS')",
    )
    parser.add_argument(
        "--color",
        choices=["neutral", "purple", "blue", "red", "yellow", "green"],
        default="neutral",
        help="Status color (default: neutral)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating",
    )

    args = parser.parse_args()

    # Build dry-run description
    description = f"Add status '{args.status}' ({args.color}) after text '{args.search_text[:40]}...'"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_status(adf, args.search_text, args.status, args.color),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added status '{args.status}' via Python REST API",
    )


if __name__ == "__main__":
    main()
