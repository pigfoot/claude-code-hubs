"""Tests for search_cql.py — CQL search and Rovo OAuth suggestion flow."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "skills" / "confluence" / "scripts"),
)

from search_cql import format_results, search_cql
from smart_search import SmartSearch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_api_response(titles: list[str], space_key: str = "TST") -> dict:
    """Build a fake Confluence CQL search API response (/wiki/rest/api/search format)."""
    return {
        "results": [
            {
                "title": title,
                "url": f"/wiki/spaces/{space_key}/pages/{1000 + i}/{title.replace(' ', '+')}",
                "content": {
                    "id": str(1000 + i),
                    "type": "page",
                    "space": {"key": space_key, "name": "Test Space"},
                },
            }
            for i, title in enumerate(titles)
        ]
    }


# ---------------------------------------------------------------------------
# search_cql() — HTTP layer
# ---------------------------------------------------------------------------


class TestSearchCql:
    def test_constructs_correct_url(self):
        """search_cql() strips /wiki suffix and appends /wiki/rest/api/search."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = _make_api_response(["Page A"])

        with patch("search_cql.requests.get", return_value=mock_resp) as mock_get:
            search_cql(
                "https://site.atlassian.net/wiki", ("u", "t"), 'title ~ "Page A"'
            )

        call_url = mock_get.call_args[0][0]
        assert call_url == "https://site.atlassian.net/wiki/rest/api/search"

    def test_passes_cql_and_limit(self):
        """search_cql() passes cql and limit as query params."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = _make_api_response([])

        with patch("search_cql.requests.get", return_value=mock_resp) as mock_get:
            search_cql("https://site.atlassian.net", ("u", "t"), "space = DEV", limit=5)

        params = mock_get.call_args[1]["params"]
        assert params["cql"] == "space = DEV"
        assert params["limit"] == 5
        assert "expand" in params

    def test_maps_results_to_expected_fields(self):
        """search_cql() returns list of dicts with title, id, space, url."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = _make_api_response(["My Page"], space_key="DEV")

        with patch("search_cql.requests.get", return_value=mock_resp):
            results = search_cql("https://site.atlassian.net", ("u", "t"), "type=page")

        assert len(results) == 1
        r = results[0]
        assert r["title"] == "My Page"
        assert r["id"] == "1000"
        assert r["space"] == "DEV"
        assert "DEV" in r["url"]
        assert "1000" in r["url"]

    def test_raises_on_http_error(self):
        """search_cql() raises RuntimeError when API returns non-2xx."""
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 400
        mock_resp.text = "CQL error"

        with patch("search_cql.requests.get", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="CQL search failed"):
                search_cql("https://site.atlassian.net", ("u", "t"), "bad cql")

    def test_empty_results(self):
        """search_cql() returns empty list when API returns no results."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"results": []}

        with patch("search_cql.requests.get", return_value=mock_resp):
            results = search_cql("https://site.atlassian.net", ("u", "t"), "type=page")

        assert results == []


# ---------------------------------------------------------------------------
# format_results()
# ---------------------------------------------------------------------------


class TestFormatResults:
    def test_empty_results(self):
        assert format_results([], "type=page") == "No results found."

    def test_single_result_contains_title(self):
        results = [
            {
                "title": "API Docs",
                "id": "42",
                "space": "DEV",
                "space_name": "Dev Space",
                "url": "https://site/wiki/spaces/DEV/pages/42",
            }
        ]
        output = format_results(results, 'title ~ "API"')
        assert "API Docs" in output
        assert "42" in output
        assert "DEV" in output

    def test_multiple_results_numbered(self):
        results = [
            {
                "title": "Page One",
                "id": "1",
                "space": "A",
                "space_name": "A Space",
                "url": "https://site/1",
            },
            {
                "title": "Page Two",
                "id": "2",
                "space": "B",
                "space_name": "B Space",
                "url": "https://site/2",
            },
        ]
        output = format_results(results, "type=page")
        assert "1." in output
        assert "2." in output
        assert "Found 2 result(s)" in output


# ---------------------------------------------------------------------------
# SmartSearch — Rovo OAuth suggestion
# ---------------------------------------------------------------------------


class TestRovoSuggestion:
    def setup_method(self):
        self.searcher = SmartSearch()

    def test_low_confidence_triggers_suggestion(self):
        """When confidence < 0.6, should_suggest_cql is True."""
        # 0 title matches → confidence = 0.3
        results = [{"title": "Unrelated Page", "id": "1"}] * 5
        analysis = self.searcher.analyze_results("my specific query", results)
        assert analysis.should_suggest_cql is True
        assert analysis.confidence < 0.6

    def test_high_confidence_no_suggestion(self):
        """When 3+ title matches, confidence >= 0.9 and no suggestion."""
        results = [
            {"title": "my specific query overview", "id": "1"},
            {"title": "my specific query guide", "id": "2"},
            {"title": "my specific query reference", "id": "3"},
        ]
        analysis = self.searcher.analyze_results("my specific query", results)
        assert analysis.should_suggest_cql is False
        assert analysis.suggestion is None

    def test_suggestion_mentions_rovo(self):
        """Low-confidence suggestion text mentions Rovo AI search."""
        results = [{"title": "Unrelated", "id": "1"}] * 3
        analysis = self.searcher.analyze_results("needle", results)
        assert analysis.suggestion is not None
        assert "Rovo" in analysis.suggestion

    def test_suggestion_mentions_authenticate_tool(self):
        """Suggestion explicitly names mcp__claude_ai_Atlassian__authenticate."""
        results = [{"title": "Unrelated", "id": "1"}] * 3
        analysis = self.searcher.analyze_results("needle", results)
        assert "mcp__claude_ai_Atlassian__authenticate" in analysis.suggestion

    def test_suggestion_mentions_search_tool(self):
        """Suggestion names mcp__claude_ai_Atlassian_Rovo__searchAtlassian for follow-up."""
        results = [{"title": "Unrelated", "id": "1"}] * 3
        analysis = self.searcher.analyze_results("needle", results)
        assert "mcp__claude_ai_Atlassian_Rovo__searchAtlassian" in analysis.suggestion

    def test_suggestion_includes_original_query(self):
        """Suggestion embeds the original query so Claude can reuse it."""
        results = [{"title": "Unrelated", "id": "1"}] * 3
        analysis = self.searcher.analyze_results("my search term", results)
        assert "my search term" in analysis.suggestion

    def test_no_suggestion_text_for_empty_results(self):
        """No suggestion text when results are empty (nothing to upgrade from)."""
        analysis = self.searcher.analyze_results("needle", [])
        # Flag may be True (0.0 < 0.6) but suggestion text must be None
        # because there are no results to suggest upgrading from.
        assert analysis.suggestion is None

    def test_zero_confidence_no_suggestion(self):
        """Zero results → confidence 0.0 → should_suggest_cql False."""
        analysis = self.searcher.analyze_results("query", [])
        assert analysis.confidence == 0.0
        assert analysis.confidence_level == "zero"

    def test_confidence_score_in_suggestion(self):
        """Suggestion shows the confidence percentage."""
        results = [{"title": "Unrelated", "id": str(i)} for i in range(3)]
        analysis = self.searcher.analyze_results("term", results)
        # confidence should be formatted as a percentage in the suggestion
        assert "%" in analysis.suggestion


# ---------------------------------------------------------------------------
# main() — Rovo suggestion appears in stdout when confidence is low
# ---------------------------------------------------------------------------


class TestSearchCqlMainRovoFlow:
    """Integration tests for main() Rovo suggestion output path."""

    def _run_main(
        self, results: list[dict], cql: str = "type=page", extra_args: list = None
    ):
        """Run main() with mocked auth and HTTP, capture stdout."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = _make_api_response([r["title"] for r in results])

        argv = ["search_cql.py", cql] + (extra_args or [])
        with (
            patch(
                "search_cql.get_auth",
                return_value=("https://site.atlassian.net", ("u", "t")),
            ),
            patch("search_cql.requests.get", return_value=mock_resp),
            patch("sys.argv", argv),
        ):
            import search_cql as sc

            captured = StringIO()
            sys.stdout = captured
            try:
                sc.main()
            except SystemExit:
                pass
            finally:
                sys.stdout = sys.__stdout__

        return captured.getvalue()

    def test_rovo_suggestion_printed_when_low_confidence(self):
        """main() prints Rovo suggestion to stdout when confidence < 0.6."""
        # 5 unrelated results → 0 title matches → confidence 0.3 → suggestion shown
        low_results = [{"title": "Unrelated Page", "id": str(i)} for i in range(5)]
        output = self._run_main(low_results, cql="needle")
        assert "mcp__claude_ai_Atlassian__authenticate" in output

    def test_no_rovo_suggestion_when_high_confidence(self):
        """main() omits Rovo suggestion when confidence >= 0.6."""
        high_results = [
            {"title": "needle overview", "id": "1"},
            {"title": "needle guide", "id": "2"},
            {"title": "needle reference", "id": "3"},
        ]
        output = self._run_main(high_results, cql="needle")
        assert "mcp__claude_ai_Atlassian__authenticate" not in output

    def test_rovo_suggestion_not_shown_in_json_format(self):
        """In --format json mode, only JSON is output (no Rovo suggestion)."""
        low_results = [{"title": "Unrelated", "id": str(i)} for i in range(5)]
        output = self._run_main(
            low_results, cql="needle", extra_args=["--format", "json"]
        )
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert "mcp__claude_ai_Atlassian__authenticate" not in output

    def test_query_flag_overrides_cql_in_rovo_suggestion(self):
        """--query text appears in the Rovo searchAtlassian call, not the CQL string."""
        low_results = [{"title": "Unrelated Page", "id": str(i)} for i in range(5)]
        output = self._run_main(
            low_results,
            cql='text ~ "companion"',
            extra_args=["--query", "what is companion"],
        )
        # Rovo suggestion should reference the natural language query
        assert 'searchAtlassian(query="what is companion")' in output
        # Rovo suggestion should NOT reference the CQL syntax
        assert "searchAtlassian(query='text ~ \"companion\"')" not in output

    def test_query_flag_improves_confidence_scoring(self):
        """--query matching result titles raises confidence and suppresses Rovo suggestion."""
        # Titles contain "companion" — with --query "companion" confidence will be high
        high_results = [
            {"title": "companion overview", "id": "1"},
            {"title": "companion guide", "id": "2"},
            {"title": "companion reference", "id": "3"},
        ]
        output = self._run_main(
            high_results,
            cql='text ~ "companion"',
            extra_args=["--query", "companion"],
        )
        assert "mcp__claude_ai_Atlassian__authenticate" not in output

    def test_without_query_flag_cql_used_for_analysis(self):
        """Without --query, CQL string is used for confidence (may be low for CQL syntax)."""
        low_results = [{"title": "Unrelated", "id": str(i)} for i in range(5)]
        # CQL 'text ~ "companion"' won't match title "Unrelated" → low confidence
        output = self._run_main(low_results, cql='text ~ "companion"')
        assert "mcp__claude_ai_Atlassian__authenticate" in output
