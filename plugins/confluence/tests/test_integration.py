"""
Integration tests: upload Markdown → Confluence → download → compare.

These tests require Confluence API credentials and create real pages.
Pages are created under a designated parent and deleted after each test.

Skip conditions:
    - Missing CONFLUENCE_URL, CONFLUENCE_USER, or CONFLUENCE_API_TOKEN env vars

Parent page: https://trendmicro.atlassian.net/wiki/x/glWyAg
    Page ID: 45241730, Space ID: 22217757
"""

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

# Import conversion modules (sys.path set up by conftest.py)
from markdown_to_adf import markdown_to_adf, has_custom_markers
from adf_to_markdown import adf_to_markdown
from confluence_adf_utils import (
    get_auth,
    get_page_adf,
    create_page_adf,
    update_page_adf,
)

# ── Constants ──────────────────────────────────────────────────────────

PARENT_PAGE_ID = "45241730"
SPACE_ID = "22217757"

# ── Fixtures ───────────────────────────────────────────────────────────


def _has_credentials() -> bool:
    """Check if Confluence API credentials are available."""
    return all(
        os.getenv(k)
        for k in ("CONFLUENCE_URL", "CONFLUENCE_USER", "CONFLUENCE_API_TOKEN")
    )


pytestmark = pytest.mark.skipif(
    not _has_credentials(),
    reason="CONFLUENCE_URL / CONFLUENCE_USER / CONFLUENCE_API_TOKEN not set",
)


@pytest.fixture
def confluence_auth():
    """Provide (base_url, auth) tuple."""
    return get_auth()


@pytest.fixture
def tmp_output_dir():
    """Provide a temporary directory, cleaned up after test."""
    d = Path(tempfile.mkdtemp(prefix="confluence_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def create_child_page(confluence_auth):
    """
    Factory fixture: create a child page under the parent, track for cleanup.

    Usage:
        page = create_child_page(title, adf_body)
        # page["id"], page["title"], page["version"]

    All created pages are deleted in teardown (even if test fails).
    """
    import requests

    base_url, auth = confluence_auth
    api_base = base_url.rstrip("/").replace("/wiki", "")
    created_ids = []

    def _create(title: str, adf_body: dict, full_width: bool = True) -> dict:
        result = create_page_adf(
            base_url=base_url,
            auth=auth,
            space_id=SPACE_ID,
            title=title,
            body=adf_body,
            parent_id=PARENT_PAGE_ID,
            full_width=full_width,
        )
        created_ids.append(result["id"])
        return result

    yield _create

    # Teardown: delete all created pages (reverse order for safety)
    for page_id in reversed(created_ids):
        try:
            url = f"{api_base}/wiki/api/v2/pages/{page_id}"
            r = requests.delete(url, auth=auth)
            if r.ok:
                print(f"  Cleaned up page {page_id}")
            else:
                print(f"  WARNING: Failed to delete page {page_id}: {r.status_code}")
        except Exception as e:
            print(f"  WARNING: Error deleting page {page_id}: {e}")


def _unique_title(label: str) -> str:
    """Generate a unique page title to avoid collisions."""
    short_id = uuid.uuid4().hex[:8]
    return f"[TEST] {label} ({short_id})"


# ── Helpers ────────────────────────────────────────────────────────────


def _extract_adf_from_page(page_data: dict) -> dict:
    """Extract ADF dict from v2 page response."""
    body_value = (
        page_data.get("body", {}).get("atlas_doc_format", {}).get("value", "{}")
    )
    if isinstance(body_value, str):
        return json.loads(body_value)
    return body_value


def _extract_all_text(adf: dict) -> str:
    """Recursively extract all text content from an ADF document."""
    texts = []

    def _walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return " ".join(texts)


def _count_node_types(adf: dict) -> dict:
    """Count all node types recursively in an ADF document."""
    from collections import Counter

    counts = Counter()

    def _walk(node):
        if isinstance(node, dict):
            if "type" in node:
                counts[node["type"]] += 1
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return dict(counts)


# ── Tests ──────────────────────────────────────────────────────────────


class TestUploadDownloadRoundtrip:
    """Upload Markdown → Confluence (ADF v2) → download → compare."""

    def test_plain_markdown(self, confluence_auth, create_child_page):
        """Plain markdown (no custom markers) should upload and download correctly."""
        base_url, auth = confluence_auth

        # 1. Convert plain markdown to ADF
        md_source = (
            "# Integration Test\n\n"
            "This is a **bold** and *italic* paragraph.\n\n"
            "## Section Two\n\n"
            "- Item one\n"
            "- Item two\n"
            "- Item three\n\n"
            "```python\nprint('hello world')\n```\n\n"
            "> A blockquote for good measure.\n\n"
            "---\n\n"
            "Final paragraph with `inline code`.\n"
        )
        adf_body = markdown_to_adf(md_source)

        # 2. Upload
        title = _unique_title("plain-md")
        page = create_child_page(title, adf_body)
        page_id = page["id"]

        # 3. Download via v2 API
        downloaded = get_page_adf(base_url, auth, page_id)
        downloaded_adf = _extract_adf_from_page(downloaded)

        # 4. Compare: key structural elements survived
        uploaded_types = _count_node_types(adf_body)
        downloaded_types = _count_node_types(downloaded_adf)

        assert downloaded_types.get("heading", 0) >= uploaded_types.get("heading", 0)
        assert downloaded_types.get("bulletList", 0) >= uploaded_types.get(
            "bulletList", 0
        )
        assert downloaded_types.get("codeBlock", 0) >= uploaded_types.get(
            "codeBlock", 0
        )
        assert downloaded_types.get("blockquote", 0) >= uploaded_types.get(
            "blockquote", 0
        )
        assert downloaded_types.get("rule", 0) >= uploaded_types.get("rule", 0)

        # 5. Compare: text content survived
        downloaded_text = _extract_all_text(downloaded_adf)
        assert "Integration Test" in downloaded_text
        assert "hello world" in downloaded_text
        assert "blockquote" in downloaded_text

    def test_markdown_with_markers(self, confluence_auth, create_child_page):
        """Markdown with custom markers should roundtrip Confluence-specific elements."""
        base_url, auth = confluence_auth

        md_source = (
            "# Marker Test\n\n"
            'Status: <!-- STATUS: "ACTIVE" green -->\n\n'
            '<!-- EXPAND: "Click to expand" -->\n'
            "Expanded content here.\n"
            "<!-- /EXPAND -->\n\n"
            "<!-- PANEL: info -->\n"
            "This is an info panel.\n"
            "<!-- /PANEL -->\n\n"
            "Date: <!-- DATE: 1711929600000 -->\n"
        )
        assert has_custom_markers(md_source)
        adf_body = markdown_to_adf(md_source)

        title = _unique_title("markers")
        page = create_child_page(title, adf_body)
        page_id = page["id"]

        downloaded = get_page_adf(base_url, auth, page_id)
        downloaded_adf = _extract_adf_from_page(downloaded)

        # Check Confluence-specific node types survived
        downloaded_types = _count_node_types(downloaded_adf)
        assert downloaded_types.get("status", 0) >= 1, "status node missing"
        assert downloaded_types.get("expand", 0) >= 1, "expand node missing"
        assert downloaded_types.get("panel", 0) >= 1, "panel node missing"
        assert downloaded_types.get("date", 0) >= 1, "date node missing"

    def test_table_roundtrip(self, confluence_auth, create_child_page):
        """Tables should survive upload/download."""
        base_url, auth = confluence_auth

        md_source = (
            "# Table Test\n\n"
            "| Name | Score | Grade |\n"
            "|------|-------|-------|\n"
            "| Alice | 95 | A |\n"
            "| Bob | 82 | B |\n"
            "| Carol | 78 | C |\n"
        )
        adf_body = markdown_to_adf(md_source)

        title = _unique_title("table")
        page = create_child_page(title, adf_body)
        page_id = page["id"]

        downloaded = get_page_adf(base_url, auth, page_id)
        downloaded_adf = _extract_adf_from_page(downloaded)

        downloaded_types = _count_node_types(downloaded_adf)
        assert downloaded_types.get("table", 0) >= 1
        assert downloaded_types.get("tableRow", 0) >= 4  # header + 3 data rows
        assert (
            downloaded_types.get("tableCell", 0)
            + downloaded_types.get("tableHeader", 0)
            >= 12
        )

        # Check text content
        text = _extract_all_text(downloaded_adf)
        assert "Alice" in text
        assert "95" in text

    def test_adf_to_md_roundtrip_fidelity(self, confluence_auth, create_child_page):
        """Upload → download ADF → convert to Markdown → convert back to ADF → compare."""
        base_url, auth = confluence_auth

        md_source = (
            "# Fidelity Test\n\n"
            "Paragraph with **bold** text.\n\n"
            "- List item\n\n"
            "```bash\necho test\n```\n"
        )
        adf_body = markdown_to_adf(md_source)

        title = _unique_title("fidelity")
        page = create_child_page(title, adf_body)
        page_id = page["id"]

        # Download ADF
        downloaded = get_page_adf(base_url, auth, page_id)
        downloaded_adf = _extract_adf_from_page(downloaded)

        # ADF → Markdown → ADF (full roundtrip through markdown)
        md_from_download = adf_to_markdown(downloaded_adf)
        re_converted_adf = markdown_to_adf(md_from_download)

        # Compare node types (should be structurally similar)
        orig_types = _count_node_types(downloaded_adf)
        rt_types = _count_node_types(re_converted_adf)

        for key_type in ["heading", "paragraph", "bulletList", "codeBlock"]:
            assert rt_types.get(key_type, 0) >= orig_types.get(key_type, 0), (
                f"{key_type}: downloaded={orig_types.get(key_type, 0)}, "
                f"roundtripped={rt_types.get(key_type, 0)}"
            )

        # Text content should match
        rt_text = _extract_all_text(re_converted_adf)
        assert "Fidelity Test" in rt_text
        assert "echo test" in rt_text


class TestUpdateExistingPage:
    """Test updating an existing page (not just creating new ones)."""

    def test_update_page_content(self, confluence_auth, create_child_page):
        """Create a page, update its content, verify the update took effect."""
        base_url, auth = confluence_auth

        # Create initial page
        initial_md = "# Before Update\n\nOriginal content.\n"
        initial_adf = markdown_to_adf(initial_md)

        title = _unique_title("update")
        page = create_child_page(title, initial_adf)
        page_id = page["id"]

        # Read back to get version
        page_data = get_page_adf(base_url, auth, page_id)
        version = page_data["version"]["number"]

        # Update with new content
        updated_md = "# After Update\n\nModified content with **new text**.\n"
        updated_adf = markdown_to_adf(updated_md)

        update_page_adf(
            base_url,
            auth,
            page_id,
            title,
            updated_adf,
            version,
            version_message="Integration test update",
        )

        # Download and verify
        final = get_page_adf(base_url, auth, page_id)
        final_adf = _extract_adf_from_page(final)
        final_text = _extract_all_text(final_adf)

        assert "After Update" in final_text
        assert "new text" in final_text
        assert final["version"]["number"] == version + 1
