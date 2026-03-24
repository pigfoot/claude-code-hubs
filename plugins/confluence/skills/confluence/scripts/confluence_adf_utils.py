#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Shared utility library: Direct REST API operations on Confluence ADF format.

Provides fast structural modification capabilities, avoiding MCP + AI tool invocation delays.

Usage:
    from confluence_adf_utils import get_auth, get_page_adf, update_page_adf
"""

import json
import os
import sys
from typing import Optional, Tuple, List, Dict, Any
import requests
from dotenv import load_dotenv


def get_auth() -> Tuple[str, Tuple[str, str]]:
    """
    Get Confluence authentication credentials from environment variables.

    Returns:
        Tuple of (base_url, (username, api_token))

    Raises:
        ValueError: If required environment variables are missing

    Environment Variables:
        CONFLUENCE_URL - Confluence base URL (e.g., https://company.atlassian.net/wiki)
        CONFLUENCE_USER - Your email address
        CONFLUENCE_API_TOKEN - API token from https://id.atlassian.com/manage-profile/security/api-tokens
    """
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

    return url, (username, api_token)


def get_page_adf(base_url: str, auth: Tuple[str, str], page_id: str) -> Dict[str, Any]:
    """
    Get page content in ADF format via REST API v2.

    Args:
        base_url: Confluence base URL
        auth: Tuple of (username, api_token)
        page_id: Confluence page ID

    Returns:
        Full page object containing title, version, and body (ADF)

    Raises:
        requests.HTTPError: If API request fails
    """
    # Remove /wiki/ suffix if present and ensure no double slashes
    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/api/v2/pages/{page_id}?body-format=atlas_doc_format"

    response = requests.get(url, auth=auth)
    response.raise_for_status()

    return response.json()


def update_page_adf(
    base_url: str,
    auth: Tuple[str, str],
    page_id: str,
    title: str,
    body: Dict[str, Any],
    version: int,
    version_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update page content in ADF format via REST API v2.

    Args:
        base_url: Confluence base URL
        auth: Tuple of (username, api_token)
        page_id: Confluence page ID
        title: Page title (must provide existing title, cannot be empty)
        body: Page content in ADF format (dict)
        version: Current version number
        version_message: Version update message (optional)

    Returns:
        Updated page object

    Raises:
        requests.HTTPError: If API request fails
    """
    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/api/v2/pages/{page_id}"

    payload = {
        "id": page_id,
        "status": "current",
        "title": title,  # Must provide existing title
        "body": {"representation": "atlas_doc_format", "value": json.dumps(body)},
        "version": {
            "number": version + 1,
            "message": version_message or "Updated via Python REST API",
        },
    }

    response = requests.put(url, auth=auth, json=payload)

    if not response.ok:
        print(f"❌ API Error Response: {response.text}", file=sys.stderr)

    response.raise_for_status()

    return response.json()


def find_heading_index(content: List[Dict], heading_text: str) -> Optional[int]:
    """
    Find a heading containing the specified text in ADF content array (top-level only).

    Args:
        content: ADF document's content array
        heading_text: Heading text to search for (supports partial matching)

    Returns:
        Index of the found heading, or None if not found
    """
    for i, node in enumerate(content):
        if node.get("type") == "heading":
            heading_full_text = ""
            for text_node in node.get("content", []):
                if text_node.get("type") == "text":
                    heading_full_text += text_node.get("text", "")

            if heading_text in heading_full_text:
                return i

    return None


def find_node_recursive(node, node_type: str, search_fn=None):
    """
    Recursively find a node of specified type in ADF document.

    Args:
        node: ADF node to search in
        node_type: Type of node to find (e.g., "table", "bulletList", "panel")
        search_fn: Optional function to test if node matches (receives node, returns bool)

    Returns:
        Found node or None
    """
    if isinstance(node, dict):
        # Check if this node matches
        if node.get("type") == node_type:
            if search_fn is None or search_fn(node):
                return node

        # Recursively search in nested structures
        for value in node.values():
            result = find_node_recursive(value, node_type, search_fn)
            if result is not None:
                return result

    elif isinstance(node, list):
        for item in node:
            result = find_node_recursive(item, node_type, search_fn)
            if result is not None:
                return result

    return None


def find_table_recursive(
    adf: Dict[str, Any], heading_text: str = None
) -> Optional[Dict]:
    """
    Recursively find a table in the entire document.

    Args:
        adf: ADF document
        heading_text: Optional heading text to find table after

    Returns:
        Table node or None
    """
    if heading_text:
        # Find heading first, then table after it (top-level search)
        content = adf.get("content", [])
        heading_idx = find_heading_index(content, heading_text)
        if heading_idx is None:
            return None

        # Search for table after heading
        for i in range(heading_idx + 1, len(content)):
            if content[i].get("type") == "table":
                return content[i]
            # Also check inside expand/panel macros after the heading
            table = find_node_recursive(content[i], "table")
            if table:
                return table
        return None
    else:
        # Just find any table recursively
        return find_node_recursive(adf, "table")


def find_list_recursive(
    adf: Dict[str, Any], heading_text: str = None, list_type: str = "bulletList"
) -> Optional[Dict]:
    """
    Recursively find a bullet/ordered list in the entire document.

    Args:
        adf: ADF document
        heading_text: Optional heading text to find list after
        list_type: "bulletList" or "orderedList"

    Returns:
        List node or None
    """
    if heading_text:
        # Find heading first, then list after it (top-level search)
        content = adf.get("content", [])
        heading_idx = find_heading_index(content, heading_text)
        if heading_idx is None:
            return None

        # Search for list after heading
        for i in range(heading_idx + 1, len(content)):
            if content[i].get("type") == list_type:
                return content[i]
            # Also check inside expand/panel macros after the heading
            lst = find_node_recursive(content[i], list_type)
            if lst:
                return lst
        return None
    else:
        # Just find any list recursively
        return find_node_recursive(adf, list_type)


def find_table_after_heading(
    content: List[Dict], heading_text: str
) -> Optional[Tuple[int, Dict]]:
    """
    Find the first table after a specified heading.

    Args:
        content: ADF document's content array
        heading_text: Heading text

    Returns:
        Tuple of (table_index, table_node) or None
    """
    heading_index = find_heading_index(content, heading_text)

    if heading_index is None:
        return None

    # Find the table (should be after heading)
    for i in range(heading_index + 1, len(content)):
        if content[i].get("type") == "table":
            return i, content[i]

    return None


def find_row_containing_text(table_node: Dict, search_text: str) -> Optional[int]:
    """
    Find the first row in a table whose first cell contains the specified text.

    Args:
        table_node: ADF table node
        search_text: Text to search for in the first cell

    Returns:
        Row index, or None if not found
    """
    table_content = table_node.get("content", [])

    for row_idx, row in enumerate(table_content):
        if row.get("type") != "tableRow":
            continue

        # Get first cell text
        first_cell = row.get("content", [])[0] if row.get("content") else None
        if not first_cell:
            continue

        cell_text = ""
        for para in first_cell.get("content", []):
            for text_node in para.get("content", []):
                if text_node.get("type") == "text":
                    cell_text += text_node.get("text", "")

        if search_text in cell_text:
            return row_idx

    return None


def create_table_row(cells: List[str]) -> Dict[str, Any]:
    """
    Create a new ADF table row.

    Args:
        cells: Text content for each cell

    Returns:
        ADF tableRow node
    """
    import os

    new_row = {
        "type": "tableRow",
        "attrs": {"localId": f"added-{os.urandom(4).hex()}"},
        "content": [],
    }

    # Add cells
    for i, cell_text in enumerate(cells):
        cell = {
            "type": "tableCell",
            "attrs": {
                "colspan": 1,
                "rowspan": 1,
                "localId": f"cell-{i}-{os.urandom(4).hex()}",
            },
            "content": [
                {
                    "type": "paragraph",
                    "attrs": {"localId": f"para-{i}-{os.urandom(4).hex()}"},
                    "content": [{"type": "text", "text": cell_text}],
                }
            ],
        }
        new_row["content"].append(cell)

    return new_row


def insert_table_row(
    adf: Dict[str, Any],
    table_heading: str,
    after_row_containing: str,
    new_row_cells: List[str],
) -> bool:
    """
    Insert a new row into a specified table (supports recursive search in macros).

    Args:
        adf: Complete ADF document
        table_heading: Heading text before the table
        after_row_containing: Text in the first cell of the row to insert after
        new_row_cells: Cell contents for the new row

    Returns:
        True if successful, False otherwise
    """
    # Find table using recursive search (supports tables in expand/panel macros)
    table_node = find_table_recursive(adf, table_heading)

    if table_node is None:
        print(f"❌ Could not find table after heading: {table_heading}")
        return False

    # Find row
    insert_after_index = find_row_containing_text(table_node, after_row_containing)
    if insert_after_index is None:
        print(f"❌ Could not find row containing: {after_row_containing}")
        return False

    # Create and insert new row
    new_row = create_table_row(new_row_cells)
    table_node["content"].insert(insert_after_index + 1, new_row)

    print(f"✅ Inserted new row after index {insert_after_index}")
    return True


# Convenience function for the most common workflow
def quick_update_page(
    page_id: str, modify_fn, version_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function: Read page → Modify → Write back.

    Args:
        page_id: Confluence page ID
        modify_fn: Function that accepts (adf, page_data) and returns True/False
        version_message: Version update message

    Returns:
        Updated page data

    Example:
        def add_row(adf, page_data):
            return insert_table_row(adf, "My Table", "GitHub", ["col1", "col2"])

        result = quick_update_page("123456", add_row, "Added new row")
    """
    # Get authentication
    base_url, auth = get_auth()

    # Get page
    page_data = get_page_adf(base_url, auth, page_id)
    title = page_data.get("title", "")
    version = page_data.get("version", {}).get("number", 1)

    # Parse ADF body
    body_value = page_data.get("body", {}).get("atlas_doc_format", {}).get("value")
    if isinstance(body_value, str):
        adf = json.loads(body_value)
    else:
        adf = body_value

    # Modify
    success = modify_fn(adf, page_data)

    if not success:
        raise ValueError("Modification function returned False")

    # Update page
    result = update_page_adf(
        base_url, auth, page_id, title, adf, version, version_message
    )

    return result


# ============================================================================
# High-level helper functions to reduce boilerplate in modification scripts
# ============================================================================


def load_page_for_modification(
    page_id: str,
) -> Tuple[str, Tuple[str, str], Dict[str, Any], str, int]:
    """
    Load a Confluence page for modification (standard workflow).

    Args:
        page_id: Confluence page ID

    Returns:
        Tuple of (base_url, auth, adf, title, version)

    Raises:
        Exception: If authentication or page load fails
    """
    # Get authentication
    print("🔐 Authenticating...")
    base_url, auth = get_auth()

    # Get page
    print(f"📖 Reading page {page_id}...")
    page_data = get_page_adf(base_url, auth, page_id)

    title = page_data.get("title", "")
    version = page_data.get("version", {}).get("number", 1)
    print(f"   Title: {title}")
    print(f"   Current version: {version}")

    # Parse ADF body
    body_value = page_data.get("body", {}).get("atlas_doc_format", {}).get("value")
    adf = json.loads(body_value) if isinstance(body_value, str) else body_value

    return base_url, auth, adf, title, version


def save_modified_page(
    base_url: str,
    auth: Tuple[str, str],
    page_id: str,
    title: str,
    adf: Dict[str, Any],
    version: int,
    message: str = "Updated via Python REST API",
) -> Dict[str, Any]:
    """
    Save modified page and print success message (standard workflow).

    Args:
        base_url: Confluence base URL
        auth: Authentication tuple
        page_id: Confluence page ID
        title: Page title
        adf: Modified ADF document
        version: Current version number
        message: Version update message

    Returns:
        Updated page data

    Raises:
        requests.HTTPError: If API request fails
    """
    print("📝 Updating page...")
    result = update_page_adf(base_url, auth, page_id, title, adf, version, message)

    new_version = result.get("version", {}).get("number")
    print("✅ Page updated successfully!")
    print(f"   New version: {new_version}")
    print(f"   URL: {base_url}/pages/{page_id}")

    return result


# ============================================================================
# Attachment upload utilities
# ============================================================================

# Content-type detection map
CONTENT_TYPE_MAP = {
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # Data / text
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".md": "text/markdown",
    # Archives
    ".zip": "application/zip",
    ".gz": "application/gzip",
    ".tar": "application/x-tar",
    # Media
    ".mp4": "video/mp4",
    ".mp3": "audio/mpeg",
}

IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/svg+xml",
    "image/webp",
    "image/bmp",
    "image/x-icon",
}


def detect_content_type(filename: str) -> str:
    """Detect MIME content type from file extension."""
    ext = os.path.splitext(filename)[1].lower()
    return CONTENT_TYPE_MAP.get(ext, "application/octet-stream")


def is_image_file(filename: str) -> bool:
    """Check if a file is an image based on its extension."""
    return detect_content_type(filename) in IMAGE_CONTENT_TYPES


def upload_attachment_file(
    base_url: str,
    auth: Tuple[str, str],
    page_id: str,
    file_path: str,
) -> Optional[Dict[str, str]]:
    """
    Upload a file as attachment to a Confluence page via v1 REST API.

    Extracts fileId and collectionName from the response for correct ADF
    media node construction. See docs/plans/007-confluence-attachment-upload/research.md.

    Args:
        base_url: Confluence base URL
        auth: Authentication tuple (username, api_token)
        page_id: Confluence page ID
        file_path: Path to the file to upload

    Returns:
        Dict with keys: fileId, collectionName, attachmentId, filename, mediaType
        or None if upload failed
    """
    from pathlib import Path

    filename = Path(file_path).name
    content_type = detect_content_type(filename)

    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/rest/api/content/{page_id}/child/attachment"

    with open(file_path, "rb") as f:
        files = {"file": (filename, f, content_type)}
        response = requests.post(
            url, auth=auth, files=files, headers={"X-Atlassian-Token": "no-check"}
        )

    if not response.ok:
        print(
            f"   ⚠️ Upload failed: {response.status_code} - {response.text}",
            file=sys.stderr,
        )
        return None

    result = response.json()
    if "results" not in result or len(result["results"]) == 0:
        print("   ⚠️ Upload response missing results", file=sys.stderr)
        return None

    att = result["results"][0]
    attachment_id = att["id"]
    extensions = att.get("extensions", {})

    # Extract fileId from v1 response extensions
    file_id = extensions.get("fileId")
    collection_name = extensions.get("collectionName", f"contentId-{page_id}")
    media_type = extensions.get("mediaType", content_type)

    # Fallback: query v2 API if fileId missing from v1 response
    if not file_id:
        print("   ⚠️ fileId missing from v1 response, falling back to v2 API...")
        v2_url = f"{api_base}/wiki/api/v2/attachments/{attachment_id}"
        v2_resp = requests.get(v2_url, auth=auth)
        if v2_resp.ok:
            file_id = v2_resp.json().get("fileId")
        if not file_id:
            print(f"   ❌ Could not obtain fileId for {filename}", file=sys.stderr)
            return None

    print(f"   ✅ Uploaded: {filename} (fileId: {file_id})")

    return {
        "fileId": file_id,
        "collectionName": collection_name,
        "attachmentId": attachment_id,
        "filename": filename,
        "mediaType": media_type,
    }


def execute_modification(
    page_id: str,
    modify_fn,
    dry_run: bool = False,
    dry_run_description: Optional[str] = None,
    version_message: str = "Updated via Python REST API",
):
    """
    Execute the complete modification workflow: load → modify → save.

    This is the standard workflow for all modification scripts, reducing boilerplate.

    Args:
        page_id: Confluence page ID
        modify_fn: Function that modifies ADF (receives adf dict, returns True/False)
        dry_run: If True, show what would be done without updating
        dry_run_description: Description to show in dry-run mode
        version_message: Version update message

    Raises:
        SystemExit: If modification fails or dry-run is enabled

    Example:
        def modify(adf):
            return add_rule(adf, "Overview")

        execute_modification(
            "123456",
            modify,
            dry_run=args.dry_run,
            dry_run_description="Add rule after 'Overview'",
            version_message="Added horizontal rule"
        )
    """
    try:
        # Load page
        base_url, auth, adf, title, version = load_page_for_modification(page_id)

        # Modify
        success = modify_fn(adf)

        if not success:
            sys.exit(1)

        # Dry run check
        if dry_run:
            print("\n🔍 Dry run - would do:")
            if dry_run_description:
                print(f"   {dry_run_description}")
            print("\n✅ Dry run complete (no changes made)")
            sys.exit(0)

        # Save
        save_modified_page(
            base_url, auth, page_id, title, adf, version, version_message
        )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
