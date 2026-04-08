#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Read a Confluence page via REST API v2.

Replaces MCP getConfluencePage for the Confluence skill.
Outputs page content as Markdown (default) or raw ADF JSON (--format adf).

Usage:
    # Read page as Markdown
    uv run --managed-python scripts/read_page.py PAGE_ID

    # Read page as ADF JSON (for Method 6 editing)
    uv run --managed-python scripts/read_page.py PAGE_ID --format adf

    # Accept Confluence URL (short or full)
    uv run --managed-python scripts/read_page.py "https://site.atlassian.net/wiki/x/ZQGBfg"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import get_auth, get_page_adf
from adf_to_markdown import adf_to_markdown
from url_resolver import resolve_confluence_url


def main():
    parser = argparse.ArgumentParser(description="Read a Confluence page via REST API")
    parser.add_argument(
        "page_id",
        help="Confluence page ID, or a full/short Confluence URL",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "adf"],
        default="markdown",
        help="Output format: 'markdown' (default, human-readable) or 'adf' (JSON for Method 6)",
    )
    args = parser.parse_args()

    # Resolve URL or ID
    resolved = resolve_confluence_url(args.page_id)
    if resolved["type"] == "unknown":
        print(f"❌ Cannot resolve page ID from: {args.page_id}", file=sys.stderr)
        sys.exit(1)
    page_id = resolved["value"]

    # Get credentials
    try:
        base_url, auth = get_auth()
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch page
    try:
        page = get_page_adf(base_url, auth, page_id)
    except Exception as e:
        print(f"❌ Failed to read page {page_id}: {e}", file=sys.stderr)
        sys.exit(1)

    title = page.get("title", "")
    version = page.get("version", {}).get("number", "?")
    space_id = page.get("spaceId", "")
    adf_body = page.get("body", {}).get("atlas_doc_format", {}).get("value", "{}")

    # Parse ADF
    try:
        adf_doc = json.loads(adf_body) if isinstance(adf_body, str) else adf_body
    except json.JSONDecodeError:
        adf_doc = {}

    if args.format == "adf":
        output = {
            "page_id": page_id,
            "title": title,
            "version": version,
            "space_id": space_id,
            "adf": adf_doc,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Markdown output
        md = adf_to_markdown(adf_doc) if adf_doc else ""
        print(f"Page: {title}")
        print(f"ID: {page_id} | Space: {space_id} | Version: {version}")
        print("---")
        print(md)


if __name__ == "__main__":
    main()
