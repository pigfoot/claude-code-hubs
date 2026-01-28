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
import os
import sys
from pathlib import Path
import requests

# Import from confluence_adf_utils.py
sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import (
    find_heading_index,
    get_auth,
)


def upload_attachment(base_url, auth, page_id, image_path):
    """
    Upload image as attachment to Confluence page.

    Args:
        base_url: Confluence base URL
        auth: Authentication tuple
        page_id: Confluence page ID
        image_path: Path to image file

    Returns:
        Attachment ID or None if failed
    """
    # Prepare upload
    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/rest/api/content/{page_id}/child/attachment"

    # Read file
    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}

        # Upload
        response = requests.post(
            url, auth=auth, files=files, headers={"X-Atlassian-Token": "no-check"}
        )

    if response.ok:
        result = response.json()
        # Get attachment ID from results
        if "results" in result and len(result["results"]) > 0:
            attachment_id = result["results"][0]["id"]
            print(f"   Uploaded: {Path(image_path).name} (ID: {attachment_id})")
            return attachment_id

    print(f"   ⚠️ Upload failed: {response.status_code}")
    return None


def add_media_group(adf, attachment_ids, image_filenames, after_heading=None):
    """
    Add mediaGroup (multiple images) to page.

    Args:
        adf: ADF document
        attachment_ids: List of attachment IDs
        image_filenames: List of image filenames (for logging)
        after_heading: Heading text to add images after (None = add at end)

    Returns:
        True if successful, False otherwise
    """
    content = adf.get("content", [])

    # Create mediaGroup node with multiple media children
    media_children = []
    for att_id in attachment_ids:
        media_node = {
            "type": "media",
            "attrs": {
                "id": att_id,
                "type": "file",
                "collection": "",
                "localId": f"media-{os.urandom(4).hex()}",
            },
        }
        media_children.append(media_node)

    media_group_node = {
        "type": "mediaGroup",
        "attrs": {"localId": f"mediagroup-{os.urandom(4).hex()}"},
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
            f"✅ Added image group ({len(attachment_ids)} images) after heading '{after_heading}'"
        )
    else:
        # Add at end
        content.append(media_group_node)
        print(f"✅ Added image group ({len(attachment_ids)} images) at end of page")

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
        print(f"📤 Uploading {len(args.images)} images...")
        attachment_ids = []
        for img_path in args.images:
            att_id = upload_attachment(base_url, auth, args.page_id, img_path)
            if not att_id:
                print(f"❌ Failed to upload {img_path}", file=sys.stderr)
                sys.exit(1)
            attachment_ids.append(att_id)

        # Now modify page to add media group reference
        def modify(adf):
            return add_media_group(adf, attachment_ids, image_names, args.after_heading)

        from confluence_adf_utils import execute_modification

        execute_modification(
            args.page_id,
            modify,
            dry_run=False,
            version_message=f"Added image group ({len(args.images)} images) via Python REST API",
        )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
