#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Insert new section (heading + paragraph) to Confluence page using REST API (fast method)

Avoids MCP + Claude tool invocation delays by using Python REST API directly.

Usage:
    uv run insert_section.py PAGE_ID \
        --after-heading "Overview" \
        --new-heading "Security Considerations" \
        --level 2 \
        --content "This section describes security measures..."
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
    find_heading_index,
)


def insert_section(adf, after_heading, new_heading_text, level, content_text):
    """
    Insert new section (heading + paragraph) after specified heading.

    Args:
        adf: ADF document
        after_heading: Heading text to insert section after (None = insert at end)
        new_heading_text: Text for the new heading
        level: Heading level (1-6)
        content_text: Paragraph text content (optional)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Find insert position
    if after_heading:
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False

        # Find the end of the section (next heading of same or higher level, or end)
        insert_idx = heading_idx + 1
        target_level = None

        # Get the level of the heading we're inserting after
        if content[heading_idx].get("type") == "heading":
            target_level = content[heading_idx].get("attrs", {}).get("level", 1)

        # Find next heading at same or higher level
        for i in range(heading_idx + 1, len(content)):
            node = content[i]
            if node.get("type") == "heading":
                node_level = node.get("attrs", {}).get("level", 1)
                if node_level <= target_level:
                    insert_idx = i
                    break
        else:
            # No heading found, insert at end
            insert_idx = len(content)
    else:
        # Insert at end
        insert_idx = len(content)

    # Create new heading
    new_heading = {
        "type": "heading",
        "attrs": {
            "level": level,
            "localId": f"heading-{os.urandom(4).hex()}"
        },
        "content": [
            {"type": "text", "text": new_heading_text}
        ]
    }

    # Insert heading
    content.insert(insert_idx, new_heading)
    insert_idx += 1

    # Create and insert paragraph if content provided
    if content_text:
        new_paragraph = {
            "type": "paragraph",
            "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
            "content": [
                {"type": "text", "text": content_text}
            ]
        }
        content.insert(insert_idx, new_paragraph)

    print(f"✅ Inserted section with heading level {level}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Insert new section to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--after-heading",
        help="Heading text to insert section after (omit to insert at end)"
    )
    parser.add_argument(
        "--new-heading",
        required=True,
        help="Text for the new heading (e.g., 'Security Considerations')"
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        default=2,
        help="Heading level 1-6 (default: 2)"
    )
    parser.add_argument(
        "--content",
        help="Paragraph text content (optional)"
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

        # Insert section
        if args.after_heading:
            print(f"🔍 Finding heading '{args.after_heading}'...")
        else:
            print(f"🔍 Inserting at end of page...")

        success = insert_section(
            adf,
            args.after_heading,
            args.new_heading,
            args.level,
            args.content
        )

        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n🔍 Dry run - would insert:")
            print(f"   After heading: {args.after_heading or '(end of page)'}")
            print(f"   New heading: {args.new_heading} (level {args.level})")
            if args.content:
                print(f"   Content: {args.content}")
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
            "Inserted section via Python REST API"
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
