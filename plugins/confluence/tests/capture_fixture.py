#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "requests>=2.31.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""
One-time script to capture ADF fixture from the real Confluence test page.

Downloads page 2354807244 ("Macro Integration Test — Safe Layer (37 Elements)")
and saves the ADF JSON to fixtures/macro_integration_test.json.

Usage:
    uv run plugins/confluence/tests/capture_fixture.py

Requires environment variables:
    CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_API_TOKEN
"""

import json
import sys
from collections import Counter
from pathlib import Path

# Add scripts directory to sys.path for imports
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "skills" / "confluence" / "scripts"),
)

from confluence_adf_utils import get_auth, get_page_adf

PAGE_ID = "2354807244"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURE_PATH = FIXTURE_DIR / "macro_integration_test.json"


def main():
    print(f"Fetching page {PAGE_ID} ...")
    base_url, auth = get_auth()
    page = get_page_adf(base_url, auth, PAGE_ID)

    title = page.get("title", "(untitled)")
    print(f"Title: {title}")

    # Extract ADF body
    adf_value = page["body"]["atlas_doc_format"]["value"]
    if isinstance(adf_value, str):
        adf = json.loads(adf_value)
    else:
        adf = adf_value

    # Print summary
    content = adf.get("content", [])
    type_counts = Counter(node.get("type", "unknown") for node in content)
    print(f"Top-level nodes: {len(content)}")
    for node_type, count in type_counts.most_common():
        print(f"  {node_type}: {count}")

    # Save fixture
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(adf, f, indent=2, ensure_ascii=False)

    size_kb = FIXTURE_PATH.stat().st_size / 1024
    print(f"\nSaved to {FIXTURE_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
