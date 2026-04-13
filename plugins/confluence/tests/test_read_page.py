"""Tests for read_page.py — REST API page reader."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "skills" / "confluence" / "scripts"),
)

from url_resolver import decode_tiny_url, resolve_confluence_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_page(title: str, version: int = 1, space_id: str = "99") -> dict:
    """Build a minimal fake get_page_adf() response."""
    adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]}
        ],
    }
    return {
        "id": "123456",
        "title": title,
        "version": {"number": version},
        "spaceId": space_id,
        "body": {"atlas_doc_format": {"value": json.dumps(adf)}},
    }


def _run_main(page_id: str, fmt: str = "markdown"):
    """Run read_page.main() with mocked auth and page fetch, return stdout."""
    fake_page = _make_page("Test Page", version=3, space_id="42")

    argv = ["read_page.py", page_id]
    if fmt != "markdown":
        argv += ["--format", fmt]

    with (
        patch(
            "read_page.get_auth",
            return_value=("https://site.atlassian.net", ("u", "t")),
        ),
        patch("read_page.get_page_adf", return_value=fake_page),
        patch("sys.argv", argv),
    ):
        import read_page

        captured = StringIO()
        sys.stdout = captured
        try:
            read_page.main()
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__

    return captured.getvalue()


# ---------------------------------------------------------------------------
# url_resolver integration — the bug we fixed (value not page_id)
# ---------------------------------------------------------------------------


class TestUrlResolution:
    def test_numeric_id_resolves_to_value(self):
        """Bare numeric ID resolves via 'value' key (not 'page_id')."""
        result = resolve_confluence_url("123456789")
        assert result["type"] == "page_id"
        assert result["value"] == "123456789"
        assert "page_id" not in result  # key must not exist

    def test_int_input_resolves_to_value(self):
        result = resolve_confluence_url(123456789)
        assert result["type"] == "page_id"
        assert result["value"] == "123456789"

    def test_full_url_resolves_to_value(self):
        url = "https://site.atlassian.net/wiki/spaces/DEV/pages/987654/Title"
        result = resolve_confluence_url(url)
        assert result["type"] == "page_id"
        assert result["value"] == "987654"

    def test_unknown_url_returns_unknown_type(self):
        result = resolve_confluence_url("https://example.com/not-confluence")
        assert result["type"] == "unknown"

    # Confluence TinyUI short URL decoding — uses swapped URL-safe base64
    # (-→/ and _→+, opposite of RFC 4648) with little-endian byte order.
    def test_tiny_url_underscore_character(self):
        """_ in TinyUI maps to + (value 62), not / (value 63) as in RFC 4648."""
        assert decode_tiny_url("Ew7_jQ") == 2382237203

    def test_tiny_url_dash_character(self):
        """- in TinyUI maps to / (value 63), not + (value 62) as in RFC 4648."""
        assert decode_tiny_url("-4GCcQ") == 1904378367

    def test_short_url_with_underscore_resolves_correctly(self):
        url = "https://trendmicro.atlassian.net/wiki/x/Ew7_jQ"
        result = resolve_confluence_url(url)
        assert result["type"] == "page_id"
        assert result["value"] == "2382237203"

    def test_short_url_with_dash_resolves_correctly(self):
        url = "https://trendmicro.atlassian.net/wiki/x/-4GCcQ"
        result = resolve_confluence_url(url)
        assert result["type"] == "page_id"
        assert result["value"] == "1904378367"


# ---------------------------------------------------------------------------
# Markdown output format
# ---------------------------------------------------------------------------


class TestMarkdownOutput:
    def test_header_contains_title(self):
        output = _run_main("123456")
        assert "Test Page" in output

    def test_header_contains_page_id(self):
        output = _run_main("123456")
        assert "123456" in output

    def test_header_contains_version(self):
        output = _run_main("123456")
        assert "3" in output  # version number

    def test_header_contains_space_id(self):
        output = _run_main("123456")
        assert "42" in output

    def test_separator_line_present(self):
        output = _run_main("123456")
        assert "---" in output

    def test_body_contains_adf_text(self):
        output = _run_main("123456")
        assert "Hello world" in output


# ---------------------------------------------------------------------------
# ADF JSON output format
# ---------------------------------------------------------------------------


class TestAdfOutput:
    def test_valid_json(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_contains_page_id_field(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert parsed["page_id"] == "123456"

    def test_contains_title_field(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert parsed["title"] == "Test Page"

    def test_contains_version_field(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert parsed["version"] == 3

    def test_contains_space_id_field(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert parsed["space_id"] == "42"

    def test_contains_adf_doc_field(self):
        output = _run_main("123456", fmt="adf")
        parsed = json.loads(output)
        assert parsed["adf"]["type"] == "doc"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestErrorPaths:
    def test_missing_credentials_exits_nonzero(self):
        with (
            patch("read_page.get_auth", side_effect=ValueError("missing env")),
            patch("sys.argv", ["read_page.py", "123456"]),
        ):
            import read_page

            with pytest.raises(SystemExit) as exc:
                read_page.main()
            assert exc.value.code != 0

    def test_page_fetch_error_exits_nonzero(self):
        with (
            patch("read_page.get_auth", return_value=("https://site", ("u", "t"))),
            patch("read_page.get_page_adf", side_effect=Exception("404 Not Found")),
            patch("sys.argv", ["read_page.py", "999999"]),
        ):
            import read_page

            with pytest.raises(SystemExit) as exc:
                read_page.main()
            assert exc.value.code != 0
