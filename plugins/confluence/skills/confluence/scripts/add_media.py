#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Add image (mediaSingle) to Confluence page using REST API (fast method)

Images are added as attachments and referenced in ADF.

Usage:
    uv run add_media.py PAGE_ID --after-heading "Screenshots" --image-path "./screenshot.png"
    uv run add_media.py PAGE_ID --at-end --image-path "./diagram.jpg" --width 500
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


def add_media(adf, upload_result, width=None, after_heading=None):
    """
    Add mediaSingle (image/file) to page.

    Args:
        adf: ADF document
        upload_result: Dict from upload_attachment_file() with fileId, collectionName, filename
        width: Optional width in pixels
        after_heading: Heading text to add after (None = add at end)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Create mediaSingle node using correct fileId and collectionName
    media_attrs = {
        "id": upload_result["fileId"],
        "type": "file",
        "collection": upload_result["collectionName"],
    }

    if width:
        media_attrs["width"] = width

    media_single_node = {
        "type": "mediaSingle",
        "attrs": {"layout": "center"},
        "content": [{"type": "media", "attrs": media_attrs}],
    }

    if after_heading:
        # Find heading
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False

        # Insert after heading
        content.insert(heading_idx + 1, media_single_node)
        print(f"✅ Added '{upload_result['filename']}' after heading '{after_heading}'")
    else:
        # Add at end
        content.append(media_single_node)
        print(f"✅ Added '{upload_result['filename']}' at end of page")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add image to Confluence page via REST API (fast!)"
    )
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--image-path",
        required=True,
        help="Path to image file (e.g., './screenshot.png')",
    )
    parser.add_argument(
        "--after-heading", help="Add image after this heading (e.g., 'Screenshots')"
    )
    parser.add_argument(
        "--at-end", action="store_true", help="Add image at end of page"
    )
    parser.add_argument("--width", type=int, help="Optional image width in pixels")
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

    # Validate image file exists
    if not Path(args.image_path).exists():
        print(f"❌ Error: Image file not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    # Build dry-run description
    location = (
        f"after heading '{args.after_heading}'"
        if args.after_heading
        else "at end of page"
    )
    width_info = f" (width: {args.width}px)" if args.width else ""
    description = (
        f"Upload and add image '{Path(args.image_path).name}' {location}{width_info}"
    )

    if args.dry_run:
        print("🔍 Dry run - would do:")
        print(f"   {description}")
        print("\n✅ Dry run complete (no changes made)")
        sys.exit(0)

    # For media, we need to upload first, then modify page
    # So we can't use execute_modification directly
    try:
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        # Upload attachment
        print(f"📤 Uploading {Path(args.image_path).name}...")
        upload_result = upload_attachment_file(
            base_url, auth, args.page_id, args.image_path
        )

        if not upload_result:
            print("❌ Failed to upload file", file=sys.stderr)
            sys.exit(1)

        # Now modify page to add media reference
        def modify(adf):
            return add_media(
                adf,
                upload_result,
                args.width,
                args.after_heading,
            )

        from confluence_adf_utils import execute_modification

        execute_modification(
            args.page_id,
            modify,
            dry_run=False,  # Already handled dry-run above
            version_message=f"Added '{Path(args.image_path).name}' via Python REST API",
        )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
