#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add blockquote (citation/quote block) to Confluence page using REST API (fast method)

Usage:
    uv run add_blockquote.py PAGE_ID --after-heading "References" --quote "Important note here"
    uv run add_blockquote.py PAGE_ID --at-end --quote "According to the spec..."
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


def add_blockquote(adf, quote_text, after_heading=None):
    """
    Add blockquote to page.

    Args:
        adf: ADF document
        quote_text: Text content for the quote
        after_heading: Heading text to add quote after (None = add at end)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Create blockquote node with paragraph inside
    blockquote_node = {
        "type": "blockquote",
        "attrs": {"localId": f"blockquote-{os.urandom(4).hex()}"},
        "content": [
            {
                "type": "paragraph",
                "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
                "content": [
                    {"type": "text", "text": quote_text}
                ]
            }
        ]
    }

    if after_heading:
        # Find heading
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False

        # Insert after heading
        content.insert(heading_idx + 1, blockquote_node)
        print(f"✅ Added blockquote after heading '{after_heading}'")
    else:
        # Add at end
        content.append(blockquote_node)
        print(f"✅ Added blockquote at end of page")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add blockquote to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--quote",
        required=True,
        help="Text content for the quote"
    )
    parser.add_argument(
        "--after-heading",
        help="Add quote after this heading (e.g., 'References')"
    )
    parser.add_argument(
        "--at-end",
        action="store_true",
        help="Add quote at end of page"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.after_heading and not args.at_end:
        print("❌ Error: Must specify either --after-heading or --at-end", file=sys.stderr)
        sys.exit(1)

    # Build dry-run description
    location = f"after heading '{args.after_heading}'" if args.after_heading else "at end of page"
    description = f"Add blockquote {location}: \"{args.quote[:50]}...\""

    # Execute modification using helper
    execute_modification(
        args.page_id,
        lambda adf: add_blockquote(adf, args.quote, args.after_heading),
        dry_run=args.dry_run,
        dry_run_description=description,
        version_message="Added blockquote via Python REST API"
    )


if __name__ == "__main__":
    main()
