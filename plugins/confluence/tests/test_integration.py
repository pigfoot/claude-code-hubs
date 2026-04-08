"""
Integration tests: upload Markdown → Confluence → download → compare.

These tests require Confluence API credentials and create real pages.
Pages are created under a designated parent and deleted after each test.

Skip conditions:
    - Missing CONFLUENCE_URL, CONFLUENCE_USER, or CONFLUENCE_API_TOKEN env vars
    - CQL tests additionally skip when the /wiki/rest/api/search endpoint
      returns a 4xx or network error

Parent page: https://trendmicro.atlassian.net/wiki/x/glWyAg
    Page ID: 45241730, Space ID: 22217757
"""

import json
import os
import shutil
import tempfile
import time
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
from search_cql import search_cql
from smart_search import SmartSearch

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


def _wait_for_cql_result(
    base_url: str,
    auth: tuple,
    cql: str,
    expected_id: str,
    timeout: int = 30,
    interval: int = 3,
) -> list:
    """
    Poll CQL search until expected_id appears in results or timeout expires.

    Confluence's search index is eventually consistent — newly created pages
    may not appear immediately. This helper retries with a fixed interval to
    accommodate indexing latency.

    Returns the final result list (empty if timed out).
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        results = search_cql(base_url, auth, cql, limit=10)
        if any(r["id"] == expected_id for r in results):
            return results
        time.sleep(interval)
    # Final attempt
    return search_cql(base_url, auth, cql, limit=10)


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


# ── CQL availability guard ─────────────────────────────────────────────


def _cql_available(auth) -> bool:
    """Return True if the CQL search endpoint is reachable."""
    import requests as req

    base_url, http_auth = auth
    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/rest/api/search"
    try:
        r = req.get(
            url, auth=http_auth, params={"cql": "type=page", "limit": 1}, timeout=10
        )
        return r.ok
    except Exception:
        return False


@pytest.fixture(scope="session")
def cql_auth():
    """Provide auth and skip the whole session if CQL is unavailable."""
    auth = get_auth()
    if not _cql_available(auth):
        pytest.skip(
            "CQL search endpoint unavailable (Hystrix circuit open or network error)"
        )
    return auth


# ── read_page.py integration ───────────────────────────────────────────


class TestReadPageIntegration:
    """Integration tests for read_page.py functions against live Confluence."""

    def test_read_created_page_returns_correct_title(
        self, confluence_auth, create_child_page
    ):
        """get_page_adf() returns the title we set when creating the page."""
        base_url, auth = confluence_auth
        title = _unique_title("read-page-title")
        adf_body = markdown_to_adf("# Hello\n\nContent here.\n")
        page = create_child_page(title, adf_body)

        fetched = get_page_adf(base_url, auth, page["id"])
        assert fetched["title"] == title

    def test_read_created_page_returns_adf_body(
        self, confluence_auth, create_child_page
    ):
        """get_page_adf() response contains a parseable ADF doc body."""
        base_url, auth = confluence_auth
        unique_phrase = f"unique-{uuid.uuid4().hex[:8]}"
        adf_body = markdown_to_adf(f"# Title\n\n{unique_phrase}\n")
        page = create_child_page(_unique_title("read-page-adf"), adf_body)

        fetched = get_page_adf(base_url, auth, page["id"])
        adf = _extract_adf_from_page(fetched)

        assert adf.get("type") == "doc"
        text = _extract_all_text(adf)
        assert unique_phrase in text

    def test_read_page_adf_output_shape(self, confluence_auth, create_child_page):
        """
        Verify get_page_adf() response has the fields read_page.py depends on:
        title, version.number, spaceId, body.atlas_doc_format.value.
        """
        base_url, auth = confluence_auth
        adf_body = markdown_to_adf("# Shape Test\n\nBody.\n")
        page = create_child_page(_unique_title("read-page-shape"), adf_body)

        fetched = get_page_adf(base_url, auth, page["id"])

        assert "title" in fetched
        assert "version" in fetched and "number" in fetched["version"]
        assert "spaceId" in fetched
        body_value = fetched.get("body", {}).get("atlas_doc_format", {}).get("value")
        assert body_value is not None
        adf = json.loads(body_value) if isinstance(body_value, str) else body_value
        assert adf.get("type") == "doc"

    def test_read_page_markdown_conversion(self, confluence_auth, create_child_page):
        """ADF fetched from Confluence converts back to readable Markdown."""
        base_url, auth = confluence_auth
        sentinel = f"sentinel-{uuid.uuid4().hex[:8]}"
        md_source = f"# Read Page Test\n\n**Bold text** and {sentinel}.\n"
        adf_body = markdown_to_adf(md_source)
        page = create_child_page(_unique_title("read-page-md"), adf_body)

        fetched = get_page_adf(base_url, auth, page["id"])
        adf = _extract_adf_from_page(fetched)
        md_output = adf_to_markdown(adf)

        assert sentinel in md_output
        assert "Read Page Test" in md_output


# ── search_cql.py integration ──────────────────────────────────────────


class TestSearchCqlIntegration:
    """
    Integration tests for search_cql() and SmartSearch against live Confluence.

    All tests skip automatically when the CQL endpoint is circuit-broken
    (via the cql_auth fixture).
    """

    def test_search_finds_created_page_by_exact_title(
        self, cql_auth, create_child_page
    ):
        """A page created with a unique title is found by CQL title search."""
        base_url, auth = cql_auth
        unique_title = _unique_title("cql-exact-title")
        adf_body = markdown_to_adf("# CQL Test\n\nSearchable content.\n")
        page = create_child_page(unique_title, adf_body)

        # Poll until indexed (Confluence index is eventually consistent)
        results = _wait_for_cql_result(
            base_url, auth, f'title = "{unique_title}"', page["id"]
        )
        ids = [r["id"] for r in results]
        assert page["id"] in ids, f"Expected page {page['id']} in results {ids}"

    def test_search_result_has_expected_fields(self, cql_auth, create_child_page):
        """search_cql() results include title, id, space, url."""
        base_url, auth = cql_auth
        unique_title = _unique_title("cql-fields")
        adf_body = markdown_to_adf("# Fields Test\n\nBody.\n")
        page = create_child_page(unique_title, adf_body)

        results = _wait_for_cql_result(
            base_url, auth, f'title = "{unique_title}"', page["id"]
        )
        assert len(results) >= 1
        r = results[0]
        assert "title" in r
        assert "id" in r
        assert "space" in r
        assert "url" in r
        assert r["id"] == page["id"]

    def test_high_confidence_exact_title_match(self, cql_auth, create_child_page):
        """
        Searching by exact title yields high confidence (no Rovo suggestion).
        When the title matches, SmartSearch should NOT suggest Rovo OAuth.
        """
        base_url, auth = cql_auth
        label = f"cql-confidence-{uuid.uuid4().hex[:8]}"
        unique_title = f"[TEST] {label}"
        adf_body = markdown_to_adf(f"# {label}\n\nBody.\n")
        page = create_child_page(unique_title, adf_body)

        results = _wait_for_cql_result(
            base_url, auth, f'title = "{unique_title}"', page["id"]
        )
        assert len(results) >= 1

        searcher = SmartSearch()
        analysis = searcher.analyze_results(label, results)

        # At least 1 title match → confidence >= 0.7, no Rovo suggestion
        assert analysis.confidence >= 0.6, (
            f"Expected confidence >= 0.6 for exact title match, got {analysis.confidence}"
        )
        assert analysis.should_suggest_cql is False
        assert analysis.suggestion is None

    def test_low_confidence_generic_search_triggers_rovo_suggestion(self, cql_auth):
        """
        A generic CQL query returning many unrelated pages yields low confidence
        and produces a Rovo OAuth suggestion containing mcp__claude_ai_Atlassian__authenticate.
        """
        base_url, auth = cql_auth

        # Search for a very common term to get many unrelated results
        results = search_cql(base_url, auth, "type = page", limit=50)

        if len(results) < 5:
            pytest.skip("Not enough results to test low-confidence scenario")

        searcher = SmartSearch()
        # Use a very specific needle that won't appear in generic page titles
        analysis = searcher.analyze_results("xyzzy-nonexistent-needle-12345", results)

        assert analysis.should_suggest_cql is True
        assert analysis.suggestion is not None
        assert "mcp__claude_ai_Atlassian__authenticate" in analysis.suggestion
        assert "mcp__claude_ai_Atlassian__searchAtlassian" in analysis.suggestion

    def test_search_empty_results_no_rovo_suggestion(self, cql_auth):
        """
        A search that returns 0 results should NOT produce a Rovo suggestion
        (there's nothing to upgrade from).
        """
        base_url, auth = cql_auth
        impossible_title = f"impossible-{uuid.uuid4().hex}-does-not-exist"
        results = search_cql(base_url, auth, f'title = "{impossible_title}"', limit=5)

        assert results == []

        searcher = SmartSearch()
        analysis = searcher.analyze_results(impossible_title, results)
        assert analysis.suggestion is None
