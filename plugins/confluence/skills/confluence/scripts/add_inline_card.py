#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add inline card (link preview card) to Confluence page

InlineCard creates a rich preview card for URLs inline in text.

Usage:
    uv run add_inline_card.py PAGE_ID --search-text "See documentation" --url "https://developer.atlassian.com"
    uv run add_inline_card.py PAGE_ID --search-text "GitHub repo" --url "https://github.com/user/repo"
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import execute_modification


def find_and_add_inline_card_recursive(node, search_text, url):
    """
    Recursively find paragraph/listItem containing search text and add inline card.

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
                    # Found it! Add inline card after the text
                    card_node = {
                        "type": "inlineCard",
                        "attrs": {
                            "url": url,
                            "localId": f"card-{os.urandom(4).hex()}"
                        }
                    }

                    # Add space before card
                    space_node = {"type": "text", "text": " "}

                    # Insert after the text node
                    content.insert(i + 1, space_node)
                    content.insert(i + 2, card_node)

                    return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_add_inline_card_recursive(value, search_text, url):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_add_inline_card_recursive(item, search_text, url):
                return True

    return False


def add_inline_card(adf, search_text, url):
    """
    Add inline card after search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for
        url: URL for the card

    Returns:
        True if successful, False otherwise
    """
    if find_and_add_inline_card_recursive(adf, search_text, url):
        print(f"✅ Added inline card for '{url}' after '{search_text}'")
        return True
    else:
        print(f"❌ Could not find text: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add inline card to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for (card will be added after this text)"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL for the card (e.g., 'https://developer.atlassian.com')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Validate URL format
    if not args.url.startswith(('http://', 'https://')):
        print(f"❌ Error: URL must start with http:// or https://", file=sys.stderr)
        sys.exit(1)

    # Build dry-run description
    description = f"Add inline card for '{args.url}' after text '{args.search_text[:40]}...'"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_inline_card(adf, args.search_text, args.url),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added inline card for '{args.url}' via Python REST API"
    )


if __name__ == "__main__":
    main()
