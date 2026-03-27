"""Shared fixtures for Confluence ADF roundtrip tests."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory so adf_to_markdown / markdown_to_adf can be imported
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "skills" / "confluence" / "scripts"),
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
REAL_FIXTURE = FIXTURES_DIR / "macro_integration_test.json"


@pytest.fixture
def real_adf():
    """Load the 37-element real Confluence page ADF fixture."""
    if not REAL_FIXTURE.exists():
        pytest.skip(f"Fixture not found: {REAL_FIXTURE}. Run capture_fixture.py first.")
    with open(REAL_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def make_adf_doc():
    """Helper to wrap ADF content nodes in a doc envelope."""

    def _make(*content_nodes):
        return {
            "type": "doc",
            "version": 1,
            "content": list(content_nodes),
        }

    return _make
