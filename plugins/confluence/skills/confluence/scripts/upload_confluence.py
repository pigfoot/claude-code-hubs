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
import mistune
from dotenv import load_dotenv
from atlassian import Confluence

# Import router for API selection transparency
sys.path.insert(0, str(Path(__file__).parent))
from confluence_router import ConfluenceRouter, OperationType


class ConfluenceStorageRenderer(mistune.HTMLRenderer):
    """Renderer that outputs Confluence Storage Format (XHTML)."""

    def __init__(self):
        super().__init__()
        self.attachments = []

    def image(self, alt, url, title=None):
        """Handle image references and track attachments."""
        # Build alt attribute if present
        alt_attr = f' ac:alt="{alt}"' if alt else ''

        # Track local images as attachments
        if not url.startswith(('http://', 'https://', 'data:')):
            self.attachments.append(url)
            # Use just the filename for Confluence attachment reference
            filename = os.path.basename(url)
            return f'<ac:image{alt_attr}><ri:attachment ri:filename="{filename}" /></ac:image>'

        # External URLs
        return f'<ac:image{alt_attr}><ri:url ri:value="{url}" /></ac:image>'

    def block_code(self, code, info=None):
        """Render code blocks as Confluence code macros."""
        if info:
            return f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{info}</ac:parameter><ac:parameter ac:name="linenumbers">true</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>\n'
        return f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="linenumbers">true</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>\n'

    def block_quote(self, text):
        """Render blockquotes as Confluence quote macros."""
        return f'<ac:structured-macro ac:name="quote"><ac:rich-text-body>{text}</ac:rich-text-body></ac:structured-macro>\n'

    # Table support
    def table(self, text):
        """Render table with proper HTML structure."""
        return f'<table>\n{text}</table>\n'

    def table_head(self, text):
        """Render table header with proper tr wrapper."""
        return f'<thead><tr>\n{text}</tr>\n</thead>\n'

    def table_body(self, text):
        """Render table body."""
        return f'<tbody>\n{text}</tbody>\n'

    def table_row(self, text):
        """Render table row."""
        return f'<tr>\n{text}</tr>\n'

    def table_cell(self, text, align=None, head=False):
        """Render table cell."""
        tag = 'th' if head else 'td'
        align_attr = f' align="{align}"' if align else ''
        return f'<{tag}{align_attr}>{text}</{tag}>\n'


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


def parse_markdown_file(file_path: Path) -> Tuple[Dict, str, Optional[str]]:
    """
    Parse markdown file and extract frontmatter, content, and title.
    
    Returns:
        Tuple of (frontmatter_dict, markdown_content, extracted_title)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter = {}
    markdown_content = content
    title = None
    
    # Parse frontmatter (between --- markers)
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                markdown_content = parts[2].strip()
            except yaml.YAMLError as e:
                print(f"WARNING: Failed to parse YAML frontmatter: {e}", file=sys.stderr)
    
    # Extract title from frontmatter
    if 'title' in frontmatter:
        title = frontmatter['title']
    
    # Fallback: extract title from first H1 heading
    if not title:
        match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
    
    # Last fallback: use filename
    if not title:
        title = file_path.stem.replace('_', ' ')
    
    return frontmatter, markdown_content, title


def convert_markdown_to_storage(markdown_content: str) -> Tuple[str, List[str]]:
    """
    Convert markdown to Confluence storage format using mistune 3.x.

    For Mermaid/PlantUML diagrams: Convert them to PNG/SVG files BEFORE
    calling this function, then use markdown image syntax: ![alt](path/to/image.png)

    Returns:
        Tuple of (storage_html, attachments_list)
    """
    renderer = ConfluenceStorageRenderer()
    # Enable table plugin
    parser = mistune.create_markdown(renderer=renderer, plugins=['table', 'strikethrough', 'url'])
    storage_html = parser(markdown_content)
    attachments = renderer.attachments
    return storage_html, attachments


def upload_to_confluence(
    confluence: Confluence,
    page_id: Optional[str],
    title: str,
    storage_html: str,
    attachments: List[str],
    space_key: Optional[str] = None,
    parent_id: Optional[str] = None,
    skip_existing_attachments: bool = True
) -> Dict:
    """Upload page content and attachments to Confluence via REST API."""
    
    if page_id:
        # UPDATE MODE
        page_info = confluence.get_page_by_id(page_id, expand='version')
        current_version = page_info['version']['number']
        new_version = current_version + 1
        
        print(f"📄 Updating page {page_id}")
        print(f"   Current version: {current_version} → {new_version}")
        print(f"   Content length: {len(storage_html)} characters")
        print(f"   Attachments: {len(attachments)}")
        
        result = confluence.update_page(
            page_id=page_id,
            title=title,
            body=storage_html,
            parent_id=parent_id,
            type='page',
            representation='storage',
            minor_edit=False,
            version_comment=f"Updated with images (v{current_version} → v{new_version})"
        )
        print(f"✅ Page updated successfully")
        
    else:
        # CREATE MODE
        if not space_key:
            raise ValueError("space_key is required to create new page")
        
        print(f"📄 Creating new page in space {space_key}")
        print(f"   Content length: {len(storage_html)} characters")
        print(f"   Attachments: {len(attachments)}")
        
        result = confluence.create_page(
            space=space_key,
            title=title,
            body=storage_html,
            parent_id=parent_id,
            type='page',
            representation='storage'
        )
        page_id = result['id']
        print(f"✅ Page created (ID: {page_id})")
    
    # Upload attachments
    if attachments:
        print(f"\n📎 Uploading {len(attachments)} attachments...")
        _upload_attachments(confluence, page_id, attachments, skip_existing_attachments)
    
    return {
        'id': result['id'],
        'title': result['title'],
        'version': result.get('version', {}).get('number', 'unknown'),
        'url': confluence.url + result['_links']['webui']
    }


def _upload_attachments(
    confluence: Confluence,
    page_id: str,
    attachments: List[str],
    skip_existing: bool = True
) -> None:
    """Upload attachment files to a Confluence page."""
    
    for i, attachment_path in enumerate(attachments, 1):
        filename = os.path.basename(attachment_path)
        print(f"   {i}. {filename}...", end=' ')
        
        if not os.path.exists(attachment_path):
            print(f"❌ File not found")
            continue
        
        try:
            # Check if attachment already exists
            if skip_existing:
                existing = confluence.get_attachments_from_content(page_id)
                if any(att['title'] == filename for att in existing.get('results', [])):
                    print("(exists, skipping)")
                    continue
            
            # Determine content type
            ext = os.path.splitext(filename)[1].lower()
            content_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.pdf': 'application/pdf'
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            # Upload
            confluence.attach_file(
                filename=attachment_path,
                name=filename,
                content_type=content_type,
                page_id=page_id,
                comment="Uploaded via upload_confluence.py"
            )
            print("✅")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def dry_run_preview(
    title: str,
    content: str,
    space_key: Optional[str],
    page_id: Optional[str],
    parent_id: Optional[str],
    attachments: List[str]
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
    
    print(f"\nContent preview (first 500 chars):")
    print("-" * 70)
    print(content[:500])
    if len(content) > 500:
        print("...")
    print("-" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Upload Markdown to Confluence',
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
        """
    )
    
    parser.add_argument('file', type=str, help='Markdown file to upload')
    parser.add_argument('--id', type=str, help='Page ID (for updates)')
    parser.add_argument('--space', type=str, help='Space key (required for new pages)')
    parser.add_argument('--title', type=str, help='Page title (overrides frontmatter/H1)')
    parser.add_argument('--parent-id', type=str, help='Parent page ID')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    parser.add_argument('--env-file', type=str, help='Path to .env file with credentials')
    parser.add_argument('--force-reupload', action='store_true', 
                        help='Re-upload all attachments even if they exist')
    
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
    
    # Determine parameters (CLI overrides frontmatter)
    title = args.title or extracted_title
    page_id = args.id or frontmatter.get('confluence', {}).get('id')
    space_key = args.space or frontmatter.get('confluence', {}).get('space')
    parent_id = args.parent_id or frontmatter.get('parent', {}).get('id')
    
    # Validate
    if not page_id and not space_key:
        print("ERROR: Either --id (update) or --space (create) required", file=sys.stderr)
        sys.exit(1)
    
    # Convert to storage format
    try:
        print(f"\n🔄 Converting to Confluence storage format...")
        storage_content, attachments = convert_markdown_to_storage(markdown_content)
        print(f"   Storage HTML: {len(storage_content)} characters")
        print(f"   Images found: {len(attachments)}")
        for att in attachments:
            print(f"      - {att}")
    except Exception as e:
        print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Dry-run mode
    if args.dry_run:
        dry_run_preview(title, storage_content, space_key, page_id, parent_id, attachments)
        return
    
    # Get Confluence client
    try:
        confluence = get_confluence_client(env_file=args.env_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Upload
    print(f"\n📤 Uploading to Confluence...")
    print("=" * 70)
    
    try:
        result = upload_to_confluence(
            confluence=confluence,
            page_id=page_id,
            title=title,
            storage_html=storage_content,
            attachments=attachments,
            space_key=space_key,
            parent_id=parent_id,
            skip_existing_attachments=not args.force_reupload
        )
        
        print("=" * 70)
        print("✅ UPLOAD COMPLETE!")
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


if __name__ == '__main__':
    main()
