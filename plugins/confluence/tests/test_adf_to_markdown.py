"""Unit tests for adf_to_markdown conversion."""

import pytest

from adf_to_markdown import adf_to_markdown


# ── Block elements ──────────────────────────────────────────────────


class TestParagraph:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]}
        )
        md = adf_to_markdown(doc)
        assert "Hello world" in md

    def test_empty(self, make_adf_doc):
        doc = make_adf_doc({"type": "paragraph", "content": []})
        md = adf_to_markdown(doc)
        assert md.strip() == ""


class TestHeading:
    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
    def test_levels(self, make_adf_doc, level):
        doc = make_adf_doc(
            {
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": "Title"}],
            }
        )
        md = adf_to_markdown(doc)
        assert f"{'#' * level} Title" in md

    def test_default_level(self, make_adf_doc):
        doc = make_adf_doc(
            {"type": "heading", "content": [{"type": "text", "text": "No level"}]}
        )
        md = adf_to_markdown(doc)
        assert "# No level" in md


class TestBulletList:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Item A"}],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Item B"}],
                            }
                        ],
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "- Item A" in md
        assert "- Item B" in md


class TestOrderedList:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "orderedList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "First"}],
                            }
                        ],
                    },
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Second"}],
                            }
                        ],
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "1. First" in md
        assert "2. Second" in md


class TestNestedList:
    def test_bullet_inside_bullet(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Top"}],
                            },
                            {
                                "type": "bulletList",
                                "content": [
                                    {
                                        "type": "listItem",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {"type": "text", "text": "Nested"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "- Top" in md
        assert "  - Nested" in md


class TestCodeBlock:
    def test_with_language(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": "print('hello')"}],
            }
        )
        md = adf_to_markdown(doc)
        assert "```python" in md
        assert "print('hello')" in md
        assert "```" in md

    def test_without_language(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "codeBlock",
                "attrs": {},
                "content": [{"type": "text", "text": "raw code"}],
            }
        )
        md = adf_to_markdown(doc)
        assert "```\nraw code\n```" in md


class TestBlockquote:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "blockquote",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Quoted text"}],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "> Quoted text" in md


class TestRule:
    def test_horizontal_rule(self, make_adf_doc):
        doc = make_adf_doc({"type": "rule"})
        md = adf_to_markdown(doc)
        assert "---" in md


class TestTable:
    def test_simple_table(self, make_adf_doc):
        doc = make_adf_doc(
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
                                        "content": [{"type": "text", "text": "Name"}],
                                    }
                                ],
                            },
                            {
                                "type": "tableHeader",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "Value"}],
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
                                        "content": [{"type": "text", "text": "A"}],
                                    }
                                ],
                            },
                            {
                                "type": "tableCell",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "1"}],
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "| Name | Value |" in md
        assert "| --- | --- |" in md
        assert "| A | 1 |" in md

    def test_pipe_escaping(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "table",
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": "a|b"}],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "a\\|b" in md


# ── Confluence-specific markers ─────────────────────────────────────


class TestExpand:
    def test_basic(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "expand",
                "attrs": {"title": "Click me"},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hidden content"}],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert '<!-- EXPAND: "Click me" -->' in md
        assert "Hidden content" in md
        assert "<!-- /EXPAND -->" in md

    def test_with_breakout(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "expand",
                "attrs": {"title": "Wide"},
                "marks": [
                    {
                        "type": "breakout",
                        "attrs": {"mode": "wide", "width": 1800},
                    }
                ],
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": "W"}]}
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert 'breakout="wide"' in md
        assert 'width="1800"' in md


class TestPanel:
    @pytest.mark.parametrize("panel_type", ["info", "note", "warning", "success"])
    def test_panel_types(self, make_adf_doc, panel_type):
        doc = make_adf_doc(
            {
                "type": "panel",
                "attrs": {"panelType": panel_type},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Panel text"}],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert f"<!-- PANEL: {panel_type} -->" in md
        assert "Panel text" in md
        assert "<!-- /PANEL -->" in md


class TestEmoji:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "emoji", "attrs": {"shortName": ":thumbsup:"}},
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert ":thumbsup:" in md


class TestMention:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "mention",
                        "attrs": {"id": "abc123", "text": "@Alice"},
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert '<!-- MENTION: abc123 "@Alice" -->' in md


class TestInlineCard:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "inlineCard",
                        "attrs": {"url": "https://example.com"},
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "<!-- CARD: https://example.com -->" in md


class TestStatus:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "status",
                        "attrs": {"text": "DONE", "color": "green"},
                    },
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert '<!-- STATUS: "DONE" green -->' in md


class TestDate:
    def test_simple(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "date", "attrs": {"timestamp": "1711497600000"}},
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "<!-- DATE: 1711497600000 -->" in md


# ── Text marks ──────────────────────────────────────────────────────


class TestTextMarks:
    def test_strong(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "bold",
                        "marks": [{"type": "strong"}],
                    }
                ],
            }
        )
        assert "**bold**" in adf_to_markdown(doc)

    def test_em(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "italic", "marks": [{"type": "em"}]}
                ],
            }
        )
        assert "*italic*" in adf_to_markdown(doc)

    def test_code(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "fn()", "marks": [{"type": "code"}]}
                ],
            }
        )
        assert "`fn()`" in adf_to_markdown(doc)

    def test_strike(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "removed",
                        "marks": [{"type": "strike"}],
                    }
                ],
            }
        )
        assert "~~removed~~" in adf_to_markdown(doc)

    def test_underline(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "underlined",
                        "marks": [{"type": "underline"}],
                    }
                ],
            }
        )
        assert "<u>underlined</u>" in adf_to_markdown(doc)

    def test_link(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "click",
                        "marks": [
                            {
                                "type": "link",
                                "attrs": {"href": "https://example.com"},
                            }
                        ],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "[click](https://example.com)" in md

    def test_subsup(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "2",
                        "marks": [{"type": "subsup", "attrs": {"type": "sup"}}],
                    }
                ],
            }
        )
        assert "<sup>2</sup>" in adf_to_markdown(doc)


# ── Unknown node pass-through ───────────────────────────────────────


class TestUnknownNode:
    def test_leaf_node(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "extension",
                "attrs": {
                    "extensionType": "com.atlassian.confluence.macro.core",
                    "extensionKey": "toc",
                },
            }
        )
        md = adf_to_markdown(doc)
        assert "<!-- ADF:extension" in md
        assert "toc" in md

    def test_block_with_children(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "bodiedExtension",
                "attrs": {"extensionType": "com.test", "extensionKey": "myMacro"},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Inside macro"}],
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "<!-- ADF:bodiedExtension" in md
        assert "Inside macro" in md
        assert "<!-- /ADF:bodiedExtension -->" in md


# ── Media ───────────────────────────────────────────────────────────


class TestMedia:
    def test_media_single(self, make_adf_doc):
        doc = make_adf_doc(
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "file",
                            "id": "abc-123",
                            "collection": "coll",
                            "__fileName": "photo.png",
                            "alt": "A photo",
                        },
                    }
                ],
            }
        )
        md = adf_to_markdown(doc)
        assert "![A photo](./photo.png)" in md


# ── Real fixture integration ────────────────────────────────────────


class TestRealPageCoverage:
    def test_all_marker_types_present(self, real_adf):
        """Verify the real 37-element page converts and contains expected markers."""
        md = adf_to_markdown(real_adf)

        # Standard markdown elements
        assert "## " in md  # headings
        assert "```" in md  # code blocks
        assert "> " in md  # blockquote
        assert "---" in md  # rule
        assert "| " in md  # table

        # List markers
        assert "- " in md  # bullet list

        # Confluence-specific markers
        assert "<!-- EXPAND:" in md  # expand
        assert "<!-- PANEL:" in md  # panels
        assert "<!-- STATUS:" in md  # status labels

        # Unknown node pass-through (extensions/macros)
        assert "<!-- ADF:extension" in md  # extension macros (TOC, etc.)
        assert "<!-- ADF:bodiedExtension" in md  # bodied macros

    def test_panel_types_present(self, real_adf):
        """Panel types present in the fixture.

        ADF panelType mapping differs from UI labels:
        - "Info Panel" heading -> panelType: info
        - "Note Panel" heading -> panelType: warning
        - "Warning Panel" heading -> panelType: error
        - "Tip Panel" heading -> panelType: success
        """
        md = adf_to_markdown(real_adf)
        assert "<!-- PANEL: info -->" in md
        assert "<!-- PANEL: warning -->" in md
        assert "<!-- PANEL: error -->" in md
        assert "<!-- PANEL: success -->" in md

    def test_status_labels_present(self, real_adf):
        """Multiple status labels with colors should be present."""
        md = adf_to_markdown(real_adf)
        assert '<!-- STATUS: "VERIFIED"' in md
        assert '<!-- STATUS: "IN PROGRESS"' in md
        assert '<!-- STATUS: "BLOCKED"' in md

    def test_no_empty_output(self, real_adf):
        md = adf_to_markdown(real_adf)
        assert len(md.strip()) > 100
