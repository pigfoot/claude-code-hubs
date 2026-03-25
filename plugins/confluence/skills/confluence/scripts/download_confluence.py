#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "atlassian-python-api>=3.41.0",
#   "python-dotenv>=1.0.0",
#   "PyYAML>=6.0",
#   "markdownify>=0.12.0",
#   "beautifulsoup4>=4.12.0",
#   "requests>=2.31.0",
# ]
# ///
"""
Download Confluence pages to Markdown

Usage:
    # Single page (v2 ADF format, preserves all elements)
    uv run download_confluence.py 123456789

    # With child pages
    uv run download_confluence.py --download-children 123456789

    # Multiple pages
    uv run download_confluence.py 123456 456789 789012

    # Custom output directory
    uv run download_confluence.py --output-dir ./docs 123456789

    # Legacy mode (v1 Storage format, old behavior)
    uv run download_confluence.py --legacy 123456789

Environment Variables (in .env file or exported):
    CONFLUENCE_URL - Confluence base URL (e.g., https://company.atlassian.net)
    CONFLUENCE_USER - Your email address
    CONFLUENCE_API_TOKEN - API token
"""

import sys
import argparse
import os
import re
from pathlib import Path
from typing import Optional, List, Dict

import yaml
import requests
from dotenv import load_dotenv
from atlassian import Confluence
from markdownify import markdownify as md
from bs4 import BeautifulSoup

# Import router for API selection transparency
sys.path.insert(0, str(Path(__file__).parent))
from confluence_router import ConfluenceRouter, OperationType
from confluence_adf_utils import get_page_adf
from adf_to_markdown import adf_to_markdown
import requests as _requests


def get_confluence_client(env_file: Optional[str] = None) -> Confluence:
    """Get authenticated Confluence client from environment variables."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

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


def sanitize_filename(name: str) -> str:
    """Convert string to safe filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "_", name)
    return name[:100]  # Limit length


def convert_storage_to_markdown(storage_html: str) -> str:
    """
    Convert Confluence storage format to Markdown.

    Handles common Confluence macros and elements.
    """
    soup = BeautifulSoup(storage_html, "html.parser")

    # Handle Confluence-specific elements

    # Convert code blocks
    for code_macro in soup.find_all("ac:structured-macro", {"ac:name": "code"}):
        language = ""
        lang_param = code_macro.find("ac:parameter", {"ac:name": "language"})
        if lang_param:
            language = lang_param.get_text()

        body = code_macro.find("ac:plain-text-body")
        if body:
            code_text = body.get_text()
            new_tag = soup.new_tag("pre")
            code_tag = soup.new_tag("code")
            code_tag["class"] = f"language-{language}" if language else ""
            code_tag.string = code_text
            new_tag.append(code_tag)
            code_macro.replace_with(new_tag)

    # Convert info/note/warning panels
    for panel in soup.find_all(
        "ac:structured-macro", {"ac:name": ["info", "note", "warning", "tip"]}
    ):
        panel_type = panel.get("ac:name", "note").upper()
        body = panel.find("ac:rich-text-body")
        if body:
            content = body.decode_contents()
            blockquote = soup.new_tag("blockquote")
            blockquote.string = f"**{panel_type}**: {content}"
            panel.replace_with(blockquote)

    # Handle images
    for image in soup.find_all("ac:image"):
        attachment = image.find("ri:attachment")
        if attachment:
            filename = attachment.get("ri:filename", "image")
            img_tag = soup.new_tag("img")
            img_tag["src"] = f"./{filename}"
            img_tag["alt"] = filename
            image.replace_with(img_tag)

    # Convert to markdown
    markdown = md(str(soup), heading_style="atx", bullets="-")

    # Clean up
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)  # Remove excessive newlines

    return markdown.strip()


def download_attachments(
    confluence: Confluence, page_id: str, output_dir: Path
) -> List[str]:
    """Download all attachments from a page."""

    attachments_dir = output_dir / f"{page_id}_attachments"
    downloaded = []

    try:
        attachments = confluence.get_attachments_from_content(page_id)
        results = attachments.get("results", [])

        if not results:
            return downloaded

        attachments_dir.mkdir(parents=True, exist_ok=True)

        for att in results:
            filename = att["title"]
            download_url = confluence.url + att["_links"]["download"]

            print(f"   📎 {filename}...", end=" ")

            try:
                response = requests.get(
                    download_url,
                    auth=(
                        os.getenv("CONFLUENCE_USER"),
                        os.getenv("CONFLUENCE_API_TOKEN"),
                    ),
                    stream=True,
                )
                response.raise_for_status()

                file_path = attachments_dir / filename
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded.append(str(file_path))
                print("✅")

            except Exception as e:
                print(f"❌ {e}")

    except Exception as e:
        print(f"   ⚠️ Could not fetch attachments: {e}")

    return downloaded


def download_page_v2(
    page_id: str,
    output_dir: Path,
    confluence: Confluence,
    download_children: bool = False,
) -> Dict:
    """
    Download a Confluence page to Markdown using v2 API (ADF format).

    Preserves all Confluence-specific elements (expand, emoji, mention,
    inlineCard, panel, status, date) using custom markers.

    Returns dict with page info and file path.
    """
    base_url = os.getenv("CONFLUENCE_URL", "")
    auth = (os.getenv("CONFLUENCE_USER", ""), os.getenv("CONFLUENCE_API_TOKEN", ""))

    # Fetch page via v2 API
    page = get_page_adf(base_url, auth, page_id)

    title = page.get("title", "Untitled")
    space_id = page.get("spaceId", "")
    version_info = page.get("version", {})
    version_num = version_info.get("number", 1)

    # Extract ADF body
    body = page.get("body", {})
    adf_body = body.get("atlas_doc_format", {})
    adf_value = adf_body.get("value", "{}")
    if isinstance(adf_value, str):
        import json

        adf_dict = json.loads(adf_value)
    else:
        adf_dict = adf_value

    print(f"\n📄 {title}")
    print(f"   Space ID: {space_id} | Version: {version_num} | Format: ADF (v2)")

    # Convert ADF to markdown with custom markers
    markdown_content = adf_to_markdown(adf_dict)

    # Build page URL from v2 response
    page_links = page.get("_links", {})
    web_url = page_links.get("webui", "")
    base = page_links.get("base", base_url)

    # Get space key via v1 API (v2 only has spaceId)
    try:
        space_info = confluence.get_space(None, space_id=space_id) if space_id else {}
    except Exception:
        space_info = {}
    space_key = space_info.get("key", "")

    # If space_key not found via v1, try extracting from webui URL
    if not space_key and web_url:
        space_match = re.search(r"/spaces/([^/]+)/", web_url)
        if space_match:
            space_key = space_match.group(1)

    # Detect page width via v1 content-appearance property
    api_base = base_url.rstrip("/").replace("/wiki", "")
    page_width = "full"  # default
    try:
        prop_url = f"{api_base}/wiki/rest/api/content/{page_id}/property/content-appearance-published"
        prop_resp = _requests.get(prop_url, auth=auth)
        if prop_resp.ok:
            appearance = prop_resp.json().get("value", "full-width")
            page_width = "full" if appearance == "full-width" else "fixed"
    except Exception:
        pass

    # Create frontmatter
    confluence_meta = {
        "id": page_id,
        "space": space_key,
        "version": version_num,
        "url": f"{base}{web_url}"
        if web_url and not web_url.startswith("http")
        else web_url,
        "format": "adf",
    }
    if page_width != "full":
        confluence_meta["width"] = page_width

    frontmatter = {
        "title": title,
        "confluence": confluence_meta,
    }

    parent_id = page.get("parentId")
    if parent_id:
        frontmatter["parent"] = {"id": parent_id}

    # Write markdown file
    safe_title = sanitize_filename(title)
    output_file = output_dir / f"{safe_title}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
        f.write("---\n\n")
        f.write(markdown_content)

    print(f"   ✅ Saved: {output_file}")

    # Download attachments
    attachments = download_attachments(confluence, page_id, output_dir)

    result = {
        "id": page_id,
        "title": title,
        "file": str(output_file),
        "attachments": attachments,
    }

    # Download children if requested
    if download_children:
        children = confluence.get_page_child_by_type(page_id, type="page")
        for child in children:
            child_result = download_page_v2(
                child["id"], output_dir, confluence, download_children=True
            )
            result.setdefault("children", []).append(child_result)

    return result


def download_page(
    confluence: Confluence,
    page_id: str,
    output_dir: Path,
    download_children: bool = False,
) -> Dict:
    """
    Download a Confluence page to Markdown using v1 API (Storage format).

    Legacy mode: does not preserve Confluence-specific elements.
    Returns dict with page info and file path.
    """

    # Fetch page
    page = confluence.get_page_by_id(
        page_id, expand="body.storage,version,space,ancestors"
    )

    title = page["title"]
    space_key = page["space"]["key"]
    version = page["version"]["number"]
    storage_html = page["body"]["storage"]["value"]

    print(f"\n📄 {title}")
    print(f"   Space: {space_key} | Version: {version} | Format: Storage (v1 legacy)")

    # Convert to markdown
    markdown_content = convert_storage_to_markdown(storage_html)

    # Create frontmatter
    ancestors = page.get("ancestors", [])
    parent_id = ancestors[-1]["id"] if ancestors else None

    frontmatter = {
        "title": title,
        "confluence": {
            "id": page_id,
            "space": space_key,
            "version": version,
            "url": confluence.url + page["_links"]["webui"],
        },
    }
    if parent_id:
        frontmatter["parent"] = {"id": parent_id}

    # Write markdown file
    safe_title = sanitize_filename(title)
    output_file = output_dir / f"{safe_title}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
        f.write("---\n\n")
        f.write(markdown_content)

    print(f"   ✅ Saved: {output_file}")

    # Download attachments
    attachments = download_attachments(confluence, page_id, output_dir)

    result = {
        "id": page_id,
        "title": title,
        "file": str(output_file),
        "attachments": attachments,
    }

    # Download children if requested
    if download_children:
        children = confluence.get_page_child_by_type(page_id, type="page")
        for child in children:
            child_result = download_page(
                confluence, child["id"], output_dir, download_children=True
            )
            result.setdefault("children", []).append(child_result)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Download Confluence pages to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single page
    %(prog)s 123456789

    # With child pages
    %(prog)s --download-children 123456789

    # Multiple pages
    %(prog)s 123456 456789

    # Custom output directory
    %(prog)s --output-dir ./docs 123456789
        """,
    )

    parser.add_argument("page_ids", type=str, nargs="+", help="Page ID(s) to download")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=".",
        help="Output directory (default: current)",
    )
    parser.add_argument(
        "--download-children",
        "-c",
        action="store_true",
        help="Also download child pages",
    )
    parser.add_argument("--env-file", type=str, help="Path to .env file")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy v1 Storage format (default: v2 ADF format)",
    )

    args = parser.parse_args()

    # Display routing decision for transparency
    router = ConfluenceRouter()
    decision = router.route_operation(OperationType.READ)
    if decision.warning:
        print(decision.warning, file=sys.stderr)
        print()

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get Confluence client
    try:
        confluence = get_confluence_client(env_file=args.env_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    use_v2 = not args.legacy
    api_label = "v2 ADF" if use_v2 else "v1 Storage (legacy)"

    print("=" * 70)
    print(f"Downloading Confluence pages to Markdown ({api_label})")
    print("=" * 70)

    results = []

    for page_id in args.page_ids:
        try:
            if use_v2:
                result = download_page_v2(
                    page_id,
                    output_dir,
                    confluence,
                    download_children=args.download_children,
                )
            else:
                result = download_page(
                    confluence,
                    page_id,
                    output_dir,
                    download_children=args.download_children,
                )
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error downloading page {page_id}: {e}", file=sys.stderr)

    print("\n" + "=" * 70)
    print(f"✅ Downloaded {len(results)} page(s) to {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
