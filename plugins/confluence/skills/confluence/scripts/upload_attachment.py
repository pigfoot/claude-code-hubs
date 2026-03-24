#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Upload any file type as attachment to a Confluence page via REST API.

Default (auto) mode detects file type:
  - Images (png/jpg/gif/svg/webp/bmp) → mediaSingle (inline display)
  - Non-images (pdf/docx/pptx/zip/...) → mediaGroup (file cards)

Manual override modes:
  --attach-only   Upload without modifying page content
  --media-single  Force mediaSingle display for all files
  --media-group   Force mediaGroup display for all files

Usage:
    # Auto mode (default) - images inline, non-images as cards
    uv run upload_attachment.py PAGE_ID --file ./screenshot.png --at-end
    uv run upload_attachment.py PAGE_ID --files ./photo.jpg ./report.pdf --at-end

    # Attach only (no page body change)
    uv run upload_attachment.py PAGE_ID --file ./report.pdf --attach-only

    # Force specific display mode
    uv run upload_attachment.py PAGE_ID --file ./diagram.pdf --media-single --at-end
    uv run upload_attachment.py PAGE_ID --files ./a.png ./b.png --media-group --at-end

    # Dry run
    uv run upload_attachment.py PAGE_ID --file ./doc.pdf --at-end --dry-run
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
    execute_modification,
    is_image_file,
)


def add_media_single_nodes(adf, upload_results, after_heading=None):
    """Insert one mediaSingle block per uploaded file."""
    content = adf.get("content", [])

    nodes = []
    for result in upload_results:
        nodes.append(
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "id": result["fileId"],
                            "type": "file",
                            "collection": result["collectionName"],
                        },
                    }
                ],
            }
        )

    if after_heading:
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False
        for i, node in enumerate(nodes):
            content.insert(heading_idx + 1 + i, node)
        filenames = ", ".join(r["filename"] for r in upload_results)
        print(
            f"✅ Added {len(nodes)} mediaSingle block(s) after heading '{after_heading}': {filenames}"
        )
    else:
        content.extend(nodes)
        filenames = ", ".join(r["filename"] for r in upload_results)
        print(f"✅ Added {len(nodes)} mediaSingle block(s) at end of page: {filenames}")

    return True


def add_media_group_node(adf, upload_results, after_heading=None):
    """Insert one mediaGroup containing all uploaded files."""
    content = adf.get("content", [])

    media_children = []
    for result in upload_results:
        media_children.append(
            {
                "type": "media",
                "attrs": {
                    "id": result["fileId"],
                    "type": "file",
                    "collection": result["collectionName"],
                },
            }
        )

    group_node = {
        "type": "mediaGroup",
        "content": media_children,
    }

    if after_heading:
        heading_idx = find_heading_index(content, after_heading)
        if heading_idx is None:
            print(f"❌ Could not find heading: {after_heading}")
            return False
        content.insert(heading_idx + 1, group_node)
        print(
            f"✅ Added mediaGroup ({len(upload_results)} files) after heading '{after_heading}'"
        )
    else:
        content.append(group_node)
        print(f"✅ Added mediaGroup ({len(upload_results)} files) at end of page")

    return True


def add_auto_nodes(adf, upload_results, after_heading=None):
    """Auto mode: images as mediaSingle, non-images as mediaGroup."""
    images = [r for r in upload_results if is_image_file(r["filename"])]
    non_images = [r for r in upload_results if not is_image_file(r["filename"])]

    success = True

    if images:
        if not add_media_single_nodes(adf, images, after_heading):
            success = False

    if non_images:
        if not add_media_group_node(adf, non_images, after_heading):
            success = False

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Upload any file type to Confluence page via REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Auto mode (default) - images inline, non-images as file cards
    %(prog)s PAGE_ID --file screenshot.png --at-end
    %(prog)s PAGE_ID --files photo.jpg report.pdf --at-end

    # Attach only (no page body change)
    %(prog)s PAGE_ID --file report.pdf --attach-only

    # Force display mode
    %(prog)s PAGE_ID --file diagram.pdf --media-single --at-end
    %(prog)s PAGE_ID --files a.png b.png --media-group --at-end
        """,
    )
    parser.add_argument("page_id", help="Confluence page ID")

    # File input (mutually exclusive: single or multiple)
    file_group = parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument("--file", help="Single file to upload")
    file_group.add_argument("--files", nargs="+", help="Multiple files to upload")

    # Display mode (optional — default is auto)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--attach-only",
        action="store_true",
        help="Upload as attachment only (no page body modification)",
    )
    mode_group.add_argument(
        "--media-single",
        action="store_true",
        help="Force mediaSingle display for all files",
    )
    mode_group.add_argument(
        "--media-group",
        action="store_true",
        help="Force mediaGroup display for all files",
    )

    # Position (for auto / media-single / media-group)
    parser.add_argument(
        "--after-heading",
        help="Insert after this heading text",
    )
    parser.add_argument(
        "--at-end",
        action="store_true",
        help="Insert at end of page",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without uploading",
    )

    args = parser.parse_args()

    # Determine mode
    if args.attach_only:
        mode = "attach-only"
    elif args.media_single:
        mode = "media-single"
    elif args.media_group:
        mode = "media-group"
    else:
        mode = "auto"

    # Collect file paths
    file_paths = [args.file] if args.file else args.files

    # Validate files exist
    for fp in file_paths:
        if not Path(fp).exists():
            print(f"❌ Error: File not found: {fp}", file=sys.stderr)
            sys.exit(1)

    # Validate position for non-attach-only modes
    if mode != "attach-only" and not args.after_heading and not args.at_end:
        print(
            "❌ Error: Specify --after-heading or --at-end for file placement (or use --attach-only)",
            file=sys.stderr,
        )
        sys.exit(1)

    # Dry run
    filenames = [Path(fp).name for fp in file_paths]
    location = (
        f"after heading '{args.after_heading}'"
        if args.after_heading
        else "at end of page"
    )

    if args.dry_run:
        print("🔍 Dry run - would do:")
        print(f"   Mode: {mode}")
        print(f"   Files: {', '.join(filenames)}")
        if mode != "attach-only":
            print(f"   Position: {location}")
        if mode == "auto":
            img_files = [f for f in filenames if is_image_file(f)]
            non_img_files = [f for f in filenames if not is_image_file(f)]
            if img_files:
                print(f"   → Images (mediaSingle): {', '.join(img_files)}")
            if non_img_files:
                print(f"   → Non-images (mediaGroup): {', '.join(non_img_files)}")
        print("\n✅ Dry run complete (no changes made)")
        sys.exit(0)

    try:
        print("🔐 Authenticating...")
        base_url, auth = get_auth()

        # Upload all files
        print(f"📤 Uploading {len(file_paths)} file(s)...")
        upload_results = []
        for fp in file_paths:
            result = upload_attachment_file(base_url, auth, args.page_id, fp)
            if not result:
                print(f"❌ Failed to upload {fp}", file=sys.stderr)
                sys.exit(1)
            upload_results.append(result)

        # Attach-only mode: done
        if mode == "attach-only":
            print(
                f"\n✅ Uploaded {len(upload_results)} file(s) as attachments (page body unchanged)"
            )
            for r in upload_results:
                print(f"   {r['filename']} → fileId: {r['fileId']}")
            sys.exit(0)

        # Display modes: modify page body
        def modify(adf):
            if mode == "media-single":
                return add_media_single_nodes(adf, upload_results, args.after_heading)
            elif mode == "media-group":
                return add_media_group_node(adf, upload_results, args.after_heading)
            else:  # auto
                return add_auto_nodes(adf, upload_results, args.after_heading)

        execute_modification(
            args.page_id,
            modify,
            dry_run=False,
            version_message=f"Added {len(upload_results)} attachment(s) via upload_attachment.py",
        )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
