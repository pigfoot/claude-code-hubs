#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add date inline in Confluence page

Dates are inline nodes used for deadlines and timestamps.

Usage:
    uv run add_date.py PAGE_ID --search-text "Deadline:" --date "2026-03-15"
    uv run add_date.py PAGE_ID --search-text "Release date" --date "2026-12-31"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import execute_modification


def find_and_add_date_recursive(node, search_text, date_timestamp):
    """
    Recursively find paragraph/listItem containing search text and add date inline.

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
                    # Found it! Add date inline after the text
                    date_node = {
                        "type": "date",
                        "attrs": {
                            "timestamp": str(date_timestamp),
                            "localId": f"date-{os.urandom(4).hex()}"
                        }
                    }

                    # Add space before date
                    space_node = {"type": "text", "text": " "}

                    # Insert after the text node
                    content.insert(i + 1, space_node)
                    content.insert(i + 2, date_node)

                    return True

        # Recursively search in nested structures
        for value in node.values():
            if find_and_add_date_recursive(value, search_text, date_timestamp):
                return True

    elif isinstance(node, list):
        for item in node:
            if find_and_add_date_recursive(item, search_text, date_timestamp):
                return True

    return False


def add_date(adf, search_text, date_str):
    """
    Add date inline after search text (searches entire document including macros).

    Args:
        adf: ADF document
        search_text: Text to search for
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        True if successful, False otherwise
    """
    # Convert date string to timestamp (milliseconds since epoch)
    try:
        date_obj = datetime.fromisoformat(date_str)
        timestamp = int(date_obj.timestamp() * 1000)
    except ValueError:
        print(f"❌ Invalid date format: {date_str} (expected YYYY-MM-DD)")
        return False

    if find_and_add_date_recursive(adf, search_text, timestamp):
        print(f"✅ Added date '{date_str}' after '{search_text}'")
        return True
    else:
        print(f"❌ Could not find text: {search_text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add date inline in Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--search-text",
        required=True,
        help="Text to search for (date will be added after this text)"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Date in ISO format (YYYY-MM-DD, e.g., '2026-03-15')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.fromisoformat(args.date)
    except ValueError:
        print(f"❌ Error: Invalid date format '{args.date}' (expected YYYY-MM-DD)", file=sys.stderr)
        sys.exit(1)

    # Build dry-run description
    description = f"Add date '{args.date}' after text '{args.search_text[:40]}...'"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_date(adf, args.search_text, args.date),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added date '{args.date}' via Python REST API"
    )


if __name__ == "__main__":
    main()
