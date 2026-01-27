#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add emoji inline in Confluence page

Emojis are inline nodes for adding visual expressions.

Usage:
    uv run add_emoji.py PAGE_ID --search-text "Great work" --emoji ":thumbsup:"
    uv run add_emoji.py PAGE_ID --search-text "Important" --emoji ":warning:"
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import execute_modification


def find_and_add_emoji_recursive(node, search_text, emoji_shortname, emoji_id):
    """
    Recursively find paragraph/listItem containing search text and add emoji inline.

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
                    # Found it! Add emoji inline after the text
                    emoji_node = {
                        "type": "emoji",
                        "attrs": {
                            "shortName": emoji_shortname,
                            "id": emoji_id,
                            "text": emoji_shortname,
                            "localId": f"emoji-{os.urandom(4).hex()}"
                        }
                    }

                    # Add space before emoji
                    space_node = {"type": "text", "text": " "}

                    # Insert after the text node
                    content.insert(i + 1, space_node)
                    content.insert(i + 2, emoji_node)

                    return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_add_emoji_recursive(value, search_text, emoji_shortname, emoji_id):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_add_emoji_recursive(item, search_text, emoji_shortname, emoji_id):
                return True

    return False


def add_emoji(adf, search_text, emoji_shortname):
    """
    Add emoji inline after search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for
        emoji_shortname: Emoji shortname (e.g., ":smile:", ":thumbsup:")

    Returns:
        True if successful, False otherwise
    """
    # For simplicity, use shortname as ID (Confluence will resolve it)
    # Common emojis: :smile: :thumbsup: :warning: :fire: :check: :x:
    emoji_id = emoji_shortname.strip(":")

    if find_and_add_emoji_recursive(adf, search_text, emoji_shortname, emoji_id):
        print(f"✅ Added emoji {emoji_shortname} after '{search_text}'")
        return True
    else:
        print(f"❌ Could not find text: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add emoji inline in Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for (emoji will be added after this text)"
    )
    parser.add_argument(
        "--emoji",
        required=True,
        help="Emoji shortname (e.g., ':smile:', ':thumbsup:', ':warning:')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Build dry-run description
    description = f"Add emoji {args.emoji} after text '{args.search_text[:40]}...'"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_emoji(adf, args.search_text, args.emoji),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added emoji {args.emoji} via Python REST API"
    )


if __name__ == "__main__":
    main()
