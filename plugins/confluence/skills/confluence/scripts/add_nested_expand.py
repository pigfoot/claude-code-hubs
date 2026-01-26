#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add nested expand (expand inside expand) to Confluence page using REST API

NestedExpand creates collapsible sections inside other expand panels.

Usage:
    uv run add_nested_expand.py PAGE_ID --parent-expand "Details" --title "More Info" --content "Additional details here"
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    execute_modification,
    find_node_recursive,
)


def find_expand_by_title(adf, expand_title):
    """
    Find expand node by title.

    Args:
        adf: ADF document
        expand_title: Title of the expand to find

    Returns:
        Expand node or None
    """
    def matches_title(node):
        return node.get("attrs", {}).get("title", "") == expand_title

    return find_node_recursive(adf, "expand", matches_title)


def add_nested_expand(adf, parent_expand_title, nested_title, nested_content):
    """
    Add nestedExpand inside an existing expand panel.

    Args:
        adf: ADF document
        parent_expand_title: Title of parent expand to add nested expand into
        nested_title: Title for the nested expand
        nested_content: Text content for the nested expand

    Returns:
        True if successful, False otherwise
    """
    # Find parent expand
    parent_expand = find_expand_by_title(adf, parent_expand_title)

    if parent_expand is None:
        print(f"❌ Could not find expand panel: {parent_expand_title}")
        return False

    # Create nested expand node
    nested_expand_node = {
        "type": "nestedExpand",
        "attrs": {
            "title": nested_title,
            "localId": f"nestedexpand-{os.urandom(4).hex()}"
        },
        "content": [
            {
                "type": "paragraph",
                "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
                "content": [
                    {"type": "text", "text": nested_content}
                ]
            }
        ]
    }

    # Add to parent expand's content
    if "content" not in parent_expand:
        parent_expand["content"] = []

    parent_expand["content"].append(nested_expand_node)
    print(f"✅ Added nested expand '{nested_title}' inside expand '{parent_expand_title}'")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add nested expand to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--parent-expand",
        required=True,
        help="Title of parent expand panel to add nested expand into"
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Title for the nested expand panel"
    )
    parser.add_argument(
        "--content",
        required=True,
        help="Text content for the nested expand"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Build dry-run description
    description = f"Add nested expand '{args.title}' inside expand '{args.parent_expand}' with content: \"{args.content[:50]}...\""

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_nested_expand(adf, args.parent_expand, args.title, args.content),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message=f"Added nested expand '{args.title}' via Python REST API"
    )


if __name__ == "__main__":
    main()
