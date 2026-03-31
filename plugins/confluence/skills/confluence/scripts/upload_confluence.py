#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "atlassian-python-api>=3.41.0",
#   "mistune>=3.0.0",
#   "python-dotenv>=1.0.0",
#   "PyYAML>=6.0",
# ]
# ///
"""
Upload Markdown to Confluence

CRITICAL: DO NOT USE MCP FOR CONFLUENCE PAGE UPLOADS - size limits apply!
This script uses REST API directly (no size limits).

Usage:
    # Update existing page with images
    uv run upload_confluence.py document.md --id 780369923

    # Create new page
    uv run upload_confluence.py document.md --space DEV --parent-id 123456

    # Dry-run (preview without uploading)
    uv run upload_confluence.py document.md --id 780369923 --dry-run

Environment Variables (in .env file or exported):
    CONFLUENCE_URL - Confluence base URL (e.g., https://company.atlassian.net/wiki)
    CONFLUENCE_USER - Your email address
    CONFLUENCE_API_TOKEN - API token from https://id.atlassian.com/manage-profile/security/api-tokens
"""

import sys
import argparse
import re
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import yaml
from dotenv import load_dotenv
from atlassian import Confluence

# Import router for API selection transparency
sys.path.insert(0, str(Path(__file__).parent))
from confluence_router import ConfluenceRouter, OperationType
from confluence_adf_utils import (
    get_page_adf,
    update_page_adf,
    create_page_adf,
    _set_page_width,
)
from markdown_to_adf import markdown_to_adf


def get_confluence_client(env_file: Optional[str] = None) -> Confluence:
    """Get authenticated Confluence client from environment variables."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv(Path(__file__).parent.parent / ".env")
        load_dotenv()  # Also try CWD for overrides

    url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USER")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([url, username, api_token]):
        missing = []
        if not url:
            missing.append("CONFLUENCE_URL")
        if not username:
            missing.append("CONFLUENCE_USER")
        if not api_token:
            missing.append("CONFLUENCE_API_TOKEN")
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return Confluence(url=url, username=username, password=api_token, cloud=True)


def parse_markdown_file(file_path: Path) -> Tuple[Dict, str, Optional[str]]:
    """
    Parse markdown file and extract frontmatter, content, and title.

    Returns:
        Tuple of (frontmatter_dict, markdown_content, extracted_title)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = {}
    markdown_content = content
    title = None

    # Parse frontmatter (between --- markers)
    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                markdown_content = parts[2].strip()
            except yaml.YAMLError as e:
                print(
                    f"WARNING: Failed to parse YAML frontmatter: {e}", file=sys.stderr
                )

    # Extract title from frontmatter
    if "title" in frontmatter:
        title = frontmatter["title"]

    # Fallback: extract title from first H1 heading
    if not title:
        match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        if match:
            title = match.group(1).strip()

    # Last fallback: use filename
    if not title:
        title = file_path.stem.replace("_", " ")

    return frontmatter, markdown_content, title


def _upload_attachments(
    confluence: Confluence,
    page_id: str,
    attachments: List[str],
    skip_existing: bool = True,
) -> None:
    """Upload attachment files to a Confluence page."""

    for i, attachment_path in enumerate(attachments, 1):
        filename = os.path.basename(attachment_path)
        print(f"   {i}. {filename}...", end=" ")

        if not os.path.exists(attachment_path):
            print("❌ File not found")
            continue

        try:
            # Check if attachment already exists
            if skip_existing:
                existing = confluence.get_attachments_from_content(page_id)
                if any(att["title"] == filename for att in existing.get("results", [])):
                    print("(exists, skipping)")
                    continue

            # Determine content type
            ext = os.path.splitext(filename)[1].lower()
            content_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".pdf": "application/pdf",
            }
            content_type = content_types.get(ext, "application/octet-stream")

            # Upload
            confluence.attach_file(
                filename=attachment_path,
                name=filename,
                content_type=content_type,
                page_id=page_id,
                comment="Uploaded via upload_confluence.py",
            )
            print("✅")

        except Exception as e:
            print(f"❌ Error: {e}")


def upload_to_confluence_adf(
    page_id: Optional[str],
    title: str,
    adf_body: dict,
    attachments: List[str],
    space_key: Optional[str] = None,
    parent_id: Optional[str] = None,
    skip_existing_attachments: bool = True,
    confluence: Optional[Confluence] = None,
    full_width: bool = True,
) -> Dict:
    """Upload page content via v2 API using ADF format.

    Supports both update (page_id) and create (space_key) modes.
    """
    base_url = os.getenv("CONFLUENCE_URL", "")
    auth = (os.getenv("CONFLUENCE_USER", ""), os.getenv("CONFLUENCE_API_TOKEN", ""))

    if page_id:
        # UPDATE MODE via v2 API
        page_info = get_page_adf(base_url, auth, page_id)
        current_version = page_info.get("version", {}).get("number", 1)
        current_title = page_info.get("title", title)
        use_title = title or current_title

        print(f"📄 Updating page {page_id} via v2 API (ADF)")
        print(f"   Current version: {current_version} → {current_version + 1}")

        result = update_page_adf(
            base_url,
            auth,
            page_id,
            use_title,
            adf_body,
            current_version,
            version_message="Updated via upload_confluence.py (ADF)",
        )

        # Set page width (v2 API doesn't support this directly)
        api_base = base_url.rstrip("/").replace("/wiki", "")
        appearance = "full-width" if full_width else "fixed-width"
        _set_page_width(api_base, auth, page_id, appearance)

        page_links = result.get("_links", {})
        base = page_links.get("base", base_url)
        web_url = page_links.get("webui", "")
        full_url = (
            f"{base}{web_url}"
            if web_url and not web_url.startswith("http")
            else web_url
        )

        print("✅ Page updated successfully")

    else:
        # CREATE MODE via v2 API
        if not space_key:
            raise ValueError("space_key is required to create new page")

        # Resolve space key to space ID (v2 API requires spaceId)
        if confluence:
            try:
                space_info = confluence.get_space(space_key)
                space_id = str(space_info.get("id", ""))
            except Exception:
                space_id = space_key  # Fallback: try using key as ID
        else:
            space_id = space_key

        print(f"📄 Creating new page in space {space_key} via v2 API (ADF)")

        result = create_page_adf(
            base_url,
            auth,
            space_id,
            title,
            adf_body,
            parent_id=parent_id,
        )

        page_id = result.get("id", "")
        page_links = result.get("_links", {})
        base = page_links.get("base", base_url)
        web_url = page_links.get("webui", "")
        full_url = (
            f"{base}{web_url}"
            if web_url and not web_url.startswith("http")
            else web_url
        )

        print(f"✅ Page created (ID: {page_id})")

    # Upload attachments via v1 API (v2 attachment API is the same)
    if attachments and confluence:
        print(f"\n📎 Uploading {len(attachments)} attachments...")
        _upload_attachments(confluence, page_id, attachments, skip_existing_attachments)

    return {
        "id": result.get("id", page_id),
        "title": result.get("title", title),
        "version": result.get("version", {}).get("number", "unknown"),
        "url": full_url,
    }


def dry_run_preview(
    title: str,
    content: str,
    space_key: Optional[str],
    page_id: Optional[str],
    parent_id: Optional[str],
    attachments: List[str],
) -> None:
    """Print preview of what would be uploaded."""
    print("=" * 70)
    print("DRY-RUN MODE - No changes will be made")
    print("=" * 70)

    mode = "UPDATE" if page_id else "CREATE"
    print(f"\nMode: {mode}")
    print(f"Title: {title}")

    if page_id:
        print(f"Page ID: {page_id}")
    else:
        print(f"Space: {space_key}")

    if parent_id:
        print(f"Parent ID: {parent_id}")

    if attachments:
        print(f"\nAttachments ({len(attachments)}):")
        for att in attachments:
            exists = "✅" if os.path.exists(att) else "❌ NOT FOUND"
            print(f"   - {att} {exists}")

    print("\nContent preview (first 500 chars):")
    print("-" * 70)
    print(content[:500])
    if len(content) > 500:
        print("...")
    print("-" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Upload Markdown to Confluence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Update existing page
    %(prog)s document.md --id 780369923

    # Create new page
    %(prog)s document.md --space DEV --parent-id 123456

    # Dry-run preview
    %(prog)s document.md --id 780369923 --dry-run

IMPORTANT:
    - For Mermaid/PlantUML: Convert to PNG/SVG FIRST, then reference with ![alt](path)
    - DO NOT use MCP for page uploads - use this script (no size limits)
        """,
    )

    parser.add_argument("file", type=str, help="Markdown file to upload")
    parser.add_argument("--id", type=str, help="Page ID (for updates)")
    parser.add_argument("--space", type=str, help="Space key (required for new pages)")
    parser.add_argument(
        "--title", type=str, help="Page title (overrides frontmatter/H1)"
    )
    parser.add_argument("--parent-id", type=str, help="Parent page ID")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without uploading"
    )
    parser.add_argument(
        "--env-file", type=str, help="Path to .env file with credentials"
    )
    parser.add_argument(
        "--force-reupload",
        action="store_true",
        help="Re-upload all attachments even if they exist",
    )
    parser.add_argument(
        "--width",
        type=str,
        choices=["full", "narrow"],
        help="Page width layout (default: full, overrides frontmatter)",
    )
    args = parser.parse_args()

    # Display routing decision for transparency
    router = ConfluenceRouter()
    decision = router.route_operation(OperationType.WRITE)
    if decision.warning:
        print(decision.warning, file=sys.stderr)
        print()

    # Validate file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Parse markdown
    try:
        print(f"\n📖 Reading: {args.file}")
        frontmatter, markdown_content, extracted_title = parse_markdown_file(file_path)
        print(f"   Length: {len(markdown_content)} characters")
    except Exception as e:
        print(f"ERROR: Failed to parse markdown: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine user intent based on CLI arguments
    # Priority:
    # 1. Explicit --id → Update that page
    # 2. Explicit --space (without --id) → Create new page (ignore frontmatter id)
    # 3. No arguments → Use frontmatter
    title = args.title or extracted_title

    if args.id:
        # User explicitly wants to update a specific page
        page_id = args.id
        space_key = args.space or frontmatter.get("confluence", {}).get("space")
    elif args.space:
        # User explicitly wants to create a new page (ignore frontmatter id)
        page_id = None
        space_key = args.space
    else:
        # No CLI arguments, use frontmatter
        page_id = frontmatter.get("confluence", {}).get("id")
        space_key = frontmatter.get("confluence", {}).get("space")

    parent_id = args.parent_id or frontmatter.get("parent", {}).get("id")

    # Page width: CLI > frontmatter > default (full)
    confluence_conf = frontmatter.get("confluence", {})
    if args.width:
        full_width = args.width == "full"
    elif confluence_conf.get("width"):
        full_width = confluence_conf["width"] != "narrow"
    else:
        full_width = True

    # Validate
    if not page_id and not space_key:
        print(
            "ERROR: Either --id (update) or --space (create) required", file=sys.stderr
        )
        sys.exit(1)

    # Convert Markdown to ADF
    try:
        print("\n🔄 Converting to ADF format (v2 API)...")
        adf_body = markdown_to_adf(markdown_content)
        adf_content = adf_body.get("content", [])
        print(f"   ADF nodes: {len(adf_content)}")
        # Track image references for attachment upload
        import json as _json

        adf_str = _json.dumps(adf_body)
        attachments = re.findall(r'"__fileName":\s*"([^"]+)"', adf_str)
        if attachments:
            print(f"   Images found: {len(attachments)}")
            for att in attachments:
                print(f"      - {att}")
    except Exception as e:
        print(f"ERROR: ADF conversion failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Dry-run mode
    if args.dry_run:
        import json as _json

        dry_run_preview(
            title,
            _json.dumps(adf_body, indent=2)[:2000],
            space_key,
            page_id,
            parent_id,
            attachments,
        )
        return

    # Get Confluence client (for attachments and space resolution)
    try:
        confluence = get_confluence_client(env_file=args.env_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Upload via v2 API
    print("\n📤 Uploading to Confluence (ADF v2)...")
    print("=" * 70)

    try:
        result = upload_to_confluence_adf(
            page_id=page_id,
            title=title,
            adf_body=adf_body,
            attachments=attachments,
            space_key=space_key,
            parent_id=parent_id,
            skip_existing_attachments=not args.force_reupload,
            confluence=confluence,
            full_width=full_width,
        )

        print("=" * 70)
        print("✅ UPLOAD COMPLETE! (ADF v2)")
        print(f"   Title: {result['title']}")
        print(f"   ID: {result['id']}")
        print(f"   Version: {result['version']}")
        print(f"   URL: {result['url']}")
        print("=" * 70)

    except Exception as e:
        print("=" * 70)
        print(f"❌ ERROR: {e}", file=sys.stderr)
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
