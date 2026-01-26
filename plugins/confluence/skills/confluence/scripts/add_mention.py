#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add @mention (user mention) inline in Confluence page

Mentions are inline nodes used to notify specific users.

Usage:
    uv run add_mention.py PAGE_ID --search-text "Review by" --user-id "557058..."
    uv run add_mention.py PAGE_ID --search-text "Assigned to" --user-id "557058..." --display-name "John Doe"
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import execute_modification


def find_and_add_mention_recursive(node, search_text, user_id, display_name):
    """
    Recursively find paragraph/listItem containing search text and add mention inline.

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
                    # Found it! Add mention inline after the text
                    mention_node = {
                        "type": "mention",
                        "attrs": {
                            "id": user_id,
                            "text": f"@{display_name or user_id}",
                            "accessLevel": "",
                            "localId": f"mention-{os.urandom(4).hex()}"
                        }
                    }

                    # Add space before mention
                    space_node = {"type": "text", "text": " "}

                    # Insert after the text node
                    content.insert(i + 1, space_node)
                    content.insert(i + 2, mention_node)

                    return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_add_mention_recursive(value, search_text, user_id, display_name):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_add_mention_recursive(item, search_text, user_id, display_name):
                return True

    return False


def add_mention(adf, search_text, user_id, display_name=None):
    """
    Add @mention inline after search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for
        user_id: User's account ID (Atlassian account ID)
        display_name: Optional display name for the user

    Returns:
        True if successful, False otherwise
    """
    if find_and_add_mention_recursive(adf, search_text, user_id, display_name):
        display = display_name or user_id
        print(f"✅ Added mention @{display} after '{search_text}'")
        return True
    else:
        print(f"❌ Could not find text: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add @mention inline in Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for (mention will be added after this text)"
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User's Atlassian account ID (e.g., '557058...')"
    )
    parser.add_argument(
        "--display-name",
        help="Optional display name for the user (e.g., 'John Doe')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Build dry-run description
    display = args.display_name or args.user_id
    description = f"Add mention @{display} after text '{args.search_text[:40]}...'"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_mention(adf, args.search_text, args.user_id, args.display_name),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added mention @{display} via Python REST API"
    )


if __name__ == "__main__":
    main()
