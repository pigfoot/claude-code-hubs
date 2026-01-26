#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add table row to Confluence page using REST API (fast method)

Avoids MCP + Claude tool invocation delays by using Python REST API directly.
Estimated time: 10-20 seconds (vs MCP roundtrip: ~13 minutes)

Usage:
    uv run add_table_row.py 2117534137 \
        --table-heading "Access Control Inventory" \
        --after-row-containing "GitHub" \
        --cells "New Location" "New Access" "New Privilege" "New Auth" "New Issues"
"""

import argparse
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    get_auth,
    get_page_adf,
    update_page_adf,
    insert_table_row,
)


def main():
    parser = argparse.ArgumentParser(
        description="Add a table row to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--table-heading",
        required=True,
        help="Heading text before the table (e.g., 'Access Control Inventory')"
    )
    parser.add_argument(
        "--after-row-containing",
        required=True,
        help="Text in first cell of row to insert after (e.g., 'GitHub')"
    )
    parser.add_argument(
        "--cells",
        nargs="+",
        required=True,
        help="Cell contents for the new row"
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

        # Insert row
        print(f"🔍 Finding table '{args.table_heading}'...")
        success = insert_table_row(
            adf,
            args.table_heading,
            args.after_row_containing,
            args.cells
        )

        if not success:
            sys.exit(1)

        if args.dry_run:
            print("\n🔍 Dry run - would insert:")
            print(f"   Table: {args.table_heading}")
            print(f"   After row containing: {args.after_row_containing}")
            print(f"   New cells: {args.cells}")
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
            "Added table row via Python REST API"
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
