#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add info/warning/note/success panel to Confluence page using REST API (fast method)

Avoids MCP + Claude tool invocation delays by using Python REST API directly.

Usage:
    uv run add_panel.py PAGE_ID \
        --after-heading "Overview" \
        --panel-type warning \
        --content "Important: Review access quarterly"
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


def add_panel(adf, after_heading, panel_type, content_text):
    """
    Add info/warning/note/success panel after specified heading.

    Args:
        adf: ADF document
        after_heading: Heading text to insert panel after
        panel_type: "info", "warning", "note", or "success"
        content_text: Text content for the panel

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Find heading
    heading_idx = find_heading_index(content, after_heading)
    if heading_idx is None:
        print(f"❌ Could not find heading: {after_heading}")
        return False

    # Create panel node
    panel = {
        "type": "panel",
        "attrs": {"panelType": panel_type, "localId": f"panel-{os.urandom(4).hex()}"},
        "content": [
            {
                "type": "paragraph",
                "attrs": {"localId": f"para-{os.urandom(4).hex()}"},
                "content": [{"type": "text", "text": content_text}],
            }
        ],
    }

    # Insert after heading
    content.insert(heading_idx + 1, panel)
    print(f"✅ Added {panel_type} panel after heading")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add panel to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--after-heading",
        required=True,
        help="Heading text to insert panel after (e.g., 'Overview')",
    )
    parser.add_argument(
        "--panel-type",
        choices=["info", "warning", "note", "success"],
        default="info",
        help="Type of panel (default: info)",
    )
    parser.add_argument("--content", required=True, help="Text content for the panel")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually updating",
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

        # Add panel
        print(f"🔍 Finding heading '{args.after_heading}'...")
        success = add_panel(adf, args.after_heading, args.panel_type, args.content)

        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n🔍 Dry run - would add:")
            print(f"   After heading: {args.after_heading}")
            print(f"   Panel type: {args.panel_type}")
            print(f"   Content: {args.content}")
            print("\n✅ Dry run complete (no changes made)")
            return

        # Update page
        print("📝 Updating page...")
        result = update_page_adf(
            base_url,
            auth,
            args.page_id,
            title,
            adf,
            version,
            f"Added {args.panel_type} panel via Python REST API",
        )

        new_version = result.get("version", {}).get("number")
        print("✅ Page updated successfully!")
        print(f"   New version: {new_version}")
        print(f"   URL: {base_url}/pages/{args.page_id}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
