#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add image group (mediaGroup) to Confluence page using REST API (fast method)

MediaGroup displays multiple images in a row/grid layout.

Usage:
    uv run add_media_group.py PAGE_ID --after-heading "Screenshots" --images "./img1.png" "./img2.png" "./img3.png"
    uv run add_media_group.py PAGE_ID --at-end --images "./diagram1.jpg" "./diagram2.jpg"
"""

import argparse
import sys
from pathlib import Path

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    find_heading_index,
    get_auth,
    upload_attachment_file,
)


def add_media_group(adf, upload_results, after_heading=None):
    """
    Add mediaGroup (multiple files/images) to page.

    Args:
        adf: ADF document
        upload_results: List of dicts from upload_attachment_file()
        after_heading: Heading text to add after (None = add at end)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Create mediaGroup node with multiple media children
    media_children = []
    for result in upload_results:
        media_node = {
            "type": "media",
            "attrs": {
                "id": result["fileId"],
                "type": "file",
                "collection": result["collectionName"],
            },
        }
        media_children.append(media_node)

    media_group_node = {
        "type": "mediaGroup",
        "content": media_children,
    }

    if after_heading:
        # Find heading
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False

        # Insert after heading
        content.insert(heading_idx + 1, media_group_node)
        print(
            f"✅ Added media group ({len(upload_results)} files) after heading '{after_heading}'"
        )
    else:
        # Add at end
        content.append(media_group_node)
        print(f"✅ Added media group ({len(upload_results)} files) at end of page")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add image group to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="Paths to image files (e.g., './img1.png' './img2.png')",
    )
    parser.add_argument(
        "--after-heading", help="Add images after this heading (e.g., 'Screenshots')"
    )
    parser.add_argument(
        "--at-end", action="store_true", help="Add images at end of page"
    )
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

    # Validate all image files exist
    for img_path in args.images:
        if not Path(img_path).exists():
            print(f"❌ Error: Image file not found: {img_path}", file=sys.stderr)
            sys.exit(1)

    # Build dry-run description
    location = (
        f"after heading '{args.after_heading}'"
        if args.after_heading
        else "at end of page"
    )
    image_names = [Path(p).name for p in args.images]
    description = f"Upload and add image group ({len(args.images)} images: {', '.join(image_names)}) {location}"

    if args.dry_run:
        print("🔍 Dry run - would do:")
        print(f"   {description}")
        print("\n✅ Dry run complete (no changes made)")
        sys.exit(0)

    # For media group, we need to upload first, then modify page
    try:
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        # Upload all attachments
        print(f"📤 Uploading {len(args.images)} files...")
        upload_results = []
        for img_path in args.images:
            result = upload_attachment_file(base_url, auth, args.page_id, img_path)
            if not result:
                print(f"❌ Failed to upload {img_path}", file=sys.stderr)
                sys.exit(1)
            upload_results.append(result)

        # Now modify page to add media group reference
        def modify(adf):
            return add_media_group(adf, upload_results, args.after_heading)

        from confluence_adf_utils import execute_modification

        execute_modification(
            args.page_id,
            modify,
            dry_run=False,
            version_message=f"Added media group ({len(args.images)} files) via Python REST API",
        )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
