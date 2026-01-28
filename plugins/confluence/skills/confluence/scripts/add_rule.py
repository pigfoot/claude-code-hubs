#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add horizontal rule (divider) to Confluence page using REST API (fast method)

Usage:
    uv run add_rule.py PAGE_ID --after-heading "Section Title"
    uv run add_rule.py PAGE_ID --at-end
"""

import argparse
import os
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    execute_modification,
    find_heading_index,
)


def add_rule(adf, after_heading=None):
    """
    Add horizontal rule to page.

    Args:
        adf: ADF document
        after_heading: Heading text to add rule after (None = add at end)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Create rule node
    rule_node = {"type": "rule", "attrs": {"localId": f"rule-{os.urandom(4).hex()}"}}

    if after_heading:
        # Find heading
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False

        # Insert after heading
        content.insert(heading_idx + 1, rule_node)
        print(f"✅ Added horizontal rule after heading '{after_heading}'")
    else:
        # Add at end
        content.append(rule_node)
        print("✅ Added horizontal rule at end of page")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add horizontal rule to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--after-heading", help="Add rule after this heading (e.g., 'Overview')"
    )
    parser.add_argument("--at-end", action="store_true", help="Add rule at end of page")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.after_heading and not args.at_end:
        print(
            "❌ Error: Must specify either --after-heading or --at-end", file=sys.stderr
        )
        sys.exit(1)

    # Build dry-run description
    if args.after_heading:
        description = f"Add horizontal rule after heading '{args.after_heading}'"
    else:
        description = "Add horizontal rule at end of page"

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_rule(adf, args.after_heading),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message="Added horizontal rule via Python REST API",
    )


if __name__ == "__main__":
    main()
