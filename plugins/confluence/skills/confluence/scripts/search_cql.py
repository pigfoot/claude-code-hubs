#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
Search Confluence using CQL (Confluence Query Language) via REST API v1.

Replaces MCP searchConfluenceUsingCql for the Confluence skill.
Runs confidence analysis on results and suggests Rovo AI search when precision is low.

Usage:
    uv run --managed-python scripts/search_cql.py 'title ~ "API docs"'
    uv run --managed-python scripts/search_cql.py 'space = "DEV" AND text ~ "API"' --limit 20
    uv run --managed-python scripts/search_cql.py 'label = "api"' --format json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).parent))
from confluence_adf_utils import get_auth
from smart_search import SmartSearch


def search_cql(
    base_url: str,
    auth: tuple,
    cql: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Execute a CQL search via Confluence REST API v1.

    Args:
        base_url: Confluence base URL
        auth: (username, api_token) tuple
        cql: CQL query string
        limit: Maximum number of results

    Returns:
        List of result dicts with title, id, space, url fields
    """
    api_base = base_url.rstrip("/").replace("/wiki", "")
    url = f"{api_base}/wiki/rest/api/search"
    params = {
        "cql": cql,
        "limit": limit,
        "expand": "content.space,content.version",
    }

    response = requests.get(url, auth=auth, params=params)

    if not response.ok:
        raise RuntimeError(
            f"CQL search failed ({response.status_code}): {response.text}"
        )

    data = response.json()
    results = []
    site_base = api_base
    for item in data.get("results", []):
        content = item.get("content", {})
        space = content.get("space", {})
        space_key = space.get("key", "")
        space_name = space.get("name", "")
        page_id = content.get("id", "")
        title = item.get("title", "")
        # Use relative URL from response, prepend site base
        rel_url = item.get("url", "")
        page_url = (
            f"{site_base}/wiki{rel_url}"
            if rel_url
            else f"{site_base}/wiki/spaces/{space_key}/pages/{page_id}"
        )
        results.append(
            {
                "title": title,
                "id": page_id,
                "space": space_key,
                "space_name": space_name,
                "url": page_url,
                "type": content.get("type", ""),
            }
        )

    return results


def format_results(results: list[dict], cql: str) -> str:
    """Format results as human-readable table."""
    if not results:
        return "No results found."

    lines = [f"Found {len(results)} result(s) for: {cql}", ""]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   ID: {r['id']} | Space: {r['space']} ({r['space_name']})")
        lines.append(f"   {r['url']}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(
        description="Search Confluence using CQL via REST API"
    )
    parser.add_argument("cql", help="CQL query string")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: 'table' (default, human-readable) or 'json'",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Original natural language query for Rovo suggestion "
        "(default: uses CQL string). Use this when the CQL was derived "
        "from a natural language question, so the Rovo suggestion "
        "references the original intent rather than the CQL syntax.",
    )
    args = parser.parse_args()

    # Get credentials
    try:
        base_url, auth = get_auth()
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    # Execute search
    try:
        results = search_cql(base_url, auth, args.cql, args.limit)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print(format_results(results, args.cql))

    # Confidence analysis — suggest Rovo when quality is low
    if results:
        searcher = SmartSearch()
        query_for_analysis = args.query if args.query else args.cql
        analysis = searcher.analyze_results(query_for_analysis, results)
        if analysis.should_suggest_cql and analysis.suggestion:
            print()
            print(analysis.suggestion)


if __name__ == "__main__":
    main()
