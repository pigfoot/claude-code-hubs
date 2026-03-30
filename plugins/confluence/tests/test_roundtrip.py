"""Integration tests for ADF -> Markdown -> ADF roundtrip fidelity."""

from collections import Counter

import pytest

from adf_to_markdown import adf_to_markdown
from markdown_to_adf import has_custom_markers, markdown_to_adf

# Fields that are non-deterministic or injected during conversion
IGNORE_ATTRS = {"localId", "style", "accessLevel", "collection", "width"}


def normalize_adf(node):
    """Strip non-deterministic fields for structural comparison.

    - localId: generated fresh via uuid.uuid4() in markdown_to_adf
    - style: injected as "bold" on status nodes
    - accessLevel: injected as "" on mention nodes
    - collection: media attachment UUID, cannot survive markdown roundtrip
    - width: table layout width, not always preserved
    """
    if isinstance(node, dict):
        result = {}
        for k, v in sorted(node.items()):
            if k == "attrs" and isinstance(v, dict):
                attrs = {
                    ak: normalize_adf(av)
                    for ak, av in sorted(v.items())
                    if ak not in IGNORE_ATTRS
                }
                if attrs:
                    result[k] = attrs
            else:
                result[k] = normalize_adf(v)
        return result
    elif isinstance(node, list):
        return [normalize_adf(item) for item in node]
    else:
        return node


def collect_types(node, types=None):
    """Recursively collect all node types in an ADF tree."""
    if types is None:
        types = []
    if isinstance(node, dict):
        if "type" in node:
            types.append(node["type"])
        for v in node.values():
            collect_types(v, types)
    elif isinstance(node, list):
        for item in node:
            collect_types(item, types)
    return types


def roundtrip(adf_doc):
    """ADF -> Markdown -> ADF roundtrip."""
    md = adf_to_markdown(adf_doc)
    return markdown_to_adf(md), md


# ── Synthetic roundtrip tests ───────────────────────────────────────


class TestRoundtripParagraph:
    def test_simple_text(self, make_adf_doc):
        original = make_adf_doc(
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}
        )
        result, _ = roundtrip(original)
        assert normalize_adf(result) == normalize_adf(original)


class TestRoundtripHeading:
    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_heading_level(self, make_adf_doc, level):
        original = make_adf_doc(
            {
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": "Title"}],
            }
        )
        result, _ = roundtrip(original)
        result_norm = normalize_adf(result)
        # Check heading preserved with correct level
        headings = [n for n in result_norm["content"] if n.get("type") == "heading"]
        assert len(headings) == 1
        assert headings[0]["attrs"]["level"] == level


class TestRoundtripCodeBlock:
    def test_with_language(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "codeBlock",
                "attrs": {"language": "typescript"},
                "content": [{"type": "text", "text": "const x = 1;"}],
            }
        )
        result, _ = roundtrip(original)
        code_blocks = [n for n in result["content"] if n.get("type") == "codeBlock"]
        assert len(code_blocks) == 1
        assert code_blocks[0]["attrs"].get("language") == "typescript"
        assert code_blocks[0]["content"][0]["text"] == "const x = 1;"


class TestRoundtripExpand:
    def test_expand_with_content(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "expand",
                "attrs": {"title": "Details"},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hidden"}],
                    }
                ],
            }
        )
        result, _ = roundtrip(original)
        expands = [n for n in result["content"] if n.get("type") == "expand"]
        assert len(expands) == 1
        assert expands[0]["attrs"]["title"] == "Details"
        # Content should be preserved
        para = expands[0]["content"][0]
        assert para["type"] == "paragraph"
        assert para["content"][0]["text"] == "Hidden"


class TestRoundtripPanel:
    @pytest.mark.parametrize("panel_type", ["info", "note", "warning", "success"])
    def test_panel_types(self, make_adf_doc, panel_type):
        original = make_adf_doc(
            {
                "type": "panel",
                "attrs": {"panelType": panel_type},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Panel content"}],
                    }
                ],
            }
        )
        result, _ = roundtrip(original)
        panels = [n for n in result["content"] if n.get("type") == "panel"]
        assert len(panels) == 1
        assert panels[0]["attrs"]["panelType"] == panel_type


class TestRoundtripStatus:
    def test_status_inline(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "status",
                        "attrs": {"text": "DONE", "color": "green"},
                    }
                ],
            }
        )
        result, _ = roundtrip(original)
        types = collect_types(result)
        assert "status" in types

        # Find the status node
        def find_status(node):
            if isinstance(node, dict):
                if node.get("type") == "status":
                    return node
                for v in node.values():
                    r = find_status(v)
                    if r:
                        return r
            elif isinstance(node, list):
                for item in node:
                    r = find_status(item)
                    if r:
                        return r
            return None

        status = find_status(result)
        assert status is not None
        assert status["attrs"]["text"] == "DONE"
        assert status["attrs"]["color"] == "green"


class TestRoundtripEmoji:
    def test_emoji_inline(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "emoji", "attrs": {"shortName": ":thumbsup:"}},
                ],
            }
        )
        result, _ = roundtrip(original)
        types = collect_types(result)
        assert "emoji" in types


class TestRoundtripTable:
    def test_simple_table(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableHeader",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "Col1"}],
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "Val1"}],
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        )
        result, _ = roundtrip(original)
        tables = [n for n in result["content"] if n.get("type") == "table"]
        assert len(tables) == 1
        assert len(tables[0]["content"]) == 2  # header + data row


class TestRoundtripList:
    def test_bullet_list(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "A"}],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "B"}],
                            }
                        ],
                    },
                ],
            }
        )
        result, _ = roundtrip(original)
        lists = [n for n in result["content"] if n.get("type") == "bulletList"]
        assert len(lists) == 1
        assert len(lists[0]["content"]) == 2


class TestRoundtripMultipleStatusOnOneLine:
    """Regression test: multiple STATUS markers on one line must not merge."""

    def test_five_status_nodes_preserved(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "status", "attrs": {"text": "VERIFIED", "color": "green"}},
                    {"type": "text", "text": " "},
                    {
                        "type": "status",
                        "attrs": {"text": "IN PROGRESS", "color": "yellow"},
                    },
                    {"type": "text", "text": " "},
                    {"type": "status", "attrs": {"text": "BLOCKED", "color": "red"}},
                ],
            }
        )
        result, md = roundtrip(original)
        status_nodes = [n for n in collect_types(result) if n == "status"]
        assert len(status_nodes) == 3, (
            f"Expected 3 status nodes, got {len(status_nodes)}. Markdown was: {md!r}"
        )

    def test_status_text_not_corrupted(self, make_adf_doc):
        original = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "status", "attrs": {"text": "OK", "color": "green"}},
                    {"type": "text", "text": " "},
                    {"type": "status", "attrs": {"text": "FAIL", "color": "red"}},
                ],
            }
        )
        result, _ = roundtrip(original)

        def find_all(node, target_type):
            found = []
            if isinstance(node, dict):
                if node.get("type") == target_type:
                    found.append(node)
                for v in node.values():
                    found.extend(find_all(v, target_type))
            elif isinstance(node, list):
                for item in node:
                    found.extend(find_all(item, target_type))
            return found

        statuses = find_all(result, "status")
        texts = {s["attrs"]["text"] for s in statuses}
        assert "OK" in texts
        assert "FAIL" in texts


class TestParseInlineMarks:
    """Test parse_inline_marks converts markdown inline syntax to ADF marks."""

    def test_plain_text(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("just plain text")
        assert result == [{"type": "text", "text": "just plain text"}]

    def test_code_mark(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("Use `--flag` here")
        assert len(result) == 3
        assert result[0] == {"type": "text", "text": "Use "}
        assert result[1] == {
            "type": "text",
            "text": "--flag",
            "marks": [{"type": "code"}],
        }
        assert result[2] == {"type": "text", "text": " here"}

    def test_bold_mark(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("This is **important** text")
        assert len(result) == 3
        assert result[1] == {
            "type": "text",
            "text": "important",
            "marks": [{"type": "strong"}],
        }

    def test_mixed_marks(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("`code` - **REQUIRED** for *all*")
        assert len(result) == 5
        assert result[0]["marks"] == [{"type": "code"}]
        assert result[2]["marks"] == [{"type": "strong"}]
        assert result[4]["marks"] == [{"type": "em"}]

    def test_strikethrough(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("~~removed~~")
        assert result == [
            {"type": "text", "text": "removed", "marks": [{"type": "strike"}]}
        ]

    def test_no_marks_no_empty_marks_array(self):
        from confluence_adf_utils import parse_inline_marks

        result = parse_inline_marks("no marks here")
        assert "marks" not in result[0]


class TestPreprocessor:
    """Test _preprocess_markdown normalizes emoji lines and bare checkboxes."""

    def test_emoji_lines_become_list(self):
        md = "✅ First\n✅ Second\n✅ Third\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "bulletList" in types
        # Should be 3 separate list items, not 1 merged paragraph
        bl = next(n for n in result["content"] if n["type"] == "bulletList")
        assert len(bl["content"]) == 3

    def test_emoji_lines_mixed_symbols(self):
        md = "✅ Good\n❌ Bad\n⚠️ Warn\n"
        result = markdown_to_adf(md)
        bl = next(n for n in result["content"] if n["type"] == "bulletList")
        assert len(bl["content"]) == 3

    def test_emoji_already_list_items_unchanged(self):
        md = "- ✅ Already a list\n- ❌ Also a list\n"
        result = markdown_to_adf(md)
        bl = next(n for n in result["content"] if n["type"] == "bulletList")
        assert len(bl["content"]) == 2

    def test_task_list_checkbox(self):
        md = "- [ ] Unchecked\n- [x] Checked\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "taskList" in types
        tl = next(n for n in result["content"] if n["type"] == "taskList")
        items = tl["content"]
        assert len(items) == 2
        assert items[0]["attrs"]["state"] == "TODO"
        assert items[1]["attrs"]["state"] == "DONE"

    def test_bare_checkbox_converted(self):
        """Bare [ ] lines (no - prefix) should be converted to task list."""
        md = "[ ] First\n[x] Second\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "taskList" in types

    def test_no_false_positive_on_normal_text(self):
        """Normal text should not be affected by preprocessor."""
        md = "# Title\n\nJust a paragraph.\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "heading" in types
        assert "paragraph" in types
        assert "bulletList" not in types


class TestMarkerFreeMarkdown:
    """Task 7.3: Verify markdown_to_adf works for marker-free markdown (no Storage fallback)."""

    def test_plain_headings_and_paragraphs(self):
        md = "# Hello World\n\nThis is a plain paragraph.\n\n## Section Two\n\nMore text here.\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "heading" in types
        assert "paragraph" in types

    def test_code_block_no_markers(self):
        md = "```python\nprint('hello')\n```\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "codeBlock" in types

    def test_table_no_markers(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "table" in types

    def test_mixed_content_no_markers(self):
        md = (
            "# Title\n\n"
            "Some **bold** and *italic* text.\n\n"
            "- item 1\n- item 2\n\n"
            "> A quote\n\n"
            "---\n\n"
            "Final paragraph.\n"
        )
        result = markdown_to_adf(md)
        types = [n["type"] for n in result["content"]]
        assert "heading" in types
        assert "bulletList" in types
        assert "blockquote" in types
        assert "rule" in types
        assert not has_custom_markers(md)


class TestHasCustomMarkers:
    def test_with_markers(self):
        md = '<!-- EXPAND: "title" -->\ncontent\n<!-- /EXPAND -->'
        assert has_custom_markers(md)

    def test_without_markers(self):
        md = "# Hello\n\nJust plain markdown."
        assert not has_custom_markers(md)

    def test_panel_marker(self):
        assert has_custom_markers("<!-- PANEL: info -->")

    def test_status_marker(self):
        assert has_custom_markers('<!-- STATUS: "OK" green -->')

    def test_adf_marker(self):
        assert has_custom_markers('<!-- ADF:extension {"key": "toc"} -->')


# ── Real fixture roundtrip ──────────────────────────────────────────


class TestRealFixtureRoundtrip:
    def test_all_top_level_types_preserved(self, real_adf):
        """Every top-level node type in the original should exist in the result."""
        result, md = roundtrip(real_adf)

        original_types = set(n["type"] for n in real_adf["content"])
        result_types = set(n["type"] for n in result["content"])

        missing = original_types - result_types
        assert not missing, f"Node types lost in roundtrip: {missing}"

    def test_node_type_counts(self, real_adf):
        """Top-level node type counts should be close to original.

        Some variation is acceptable because markers may restructure
        the document slightly (e.g., standalone inline markers become
        paragraphs).
        """
        result, _ = roundtrip(real_adf)

        orig_counts = Counter(n["type"] for n in real_adf["content"])
        result_counts = Counter(n["type"] for n in result["content"])

        # Key element types should not be lost
        for key_type in [
            "heading",
            "panel",
            "expand",
            "codeBlock",
            "blockquote",
            "rule",
            "table",
        ]:
            if key_type in orig_counts:
                assert result_counts.get(key_type, 0) >= orig_counts[key_type], (
                    f"{key_type}: original={orig_counts[key_type]}, "
                    f"result={result_counts.get(key_type, 0)}"
                )

    def test_markdown_has_markers(self, real_adf):
        """Converted markdown should be detected as having custom markers."""
        md = adf_to_markdown(real_adf)
        assert has_custom_markers(md)

    def test_key_text_preserved(self, real_adf):
        """Key text content from the page should survive roundtrip."""
        result, _ = roundtrip(real_adf)
        all_text = []

        def extract_text(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    all_text.append(node.get("text", ""))
                for v in node.values():
                    extract_text(v)
            elif isinstance(node, list):
                for item in node:
                    extract_text(item)

        extract_text(result)
        full_text = " ".join(all_text)

        # These texts should survive the roundtrip
        assert "Code Block" in full_text
        assert "Info Panel" in full_text or "Info panel" in full_text
        assert "Blockquote" in full_text

    def test_extension_nodes_preserved(self, real_adf):
        """Extension (macro) nodes should roundtrip via ADF pass-through markers."""
        result, _ = roundtrip(real_adf)
        result_types = collect_types(result)
        assert "extension" in result_types
        assert "bodiedExtension" in result_types

    def test_status_nodes_preserved(self, real_adf):
        """Status inline nodes should survive roundtrip."""
        result, _ = roundtrip(real_adf)
        result_types = collect_types(result)
        assert "status" in result_types

    def test_panel_nodes_preserved(self, real_adf):
        """All panel nodes should survive roundtrip."""
        original_panels = [n for n in real_adf["content"] if n.get("type") == "panel"]
        result, _ = roundtrip(real_adf)
        result_panels = [n for n in result["content"] if n.get("type") == "panel"]
        assert len(result_panels) == len(original_panels)
