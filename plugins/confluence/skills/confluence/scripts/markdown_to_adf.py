#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["mistune>=3.0.0"]
# ///
"""
Convert Markdown with custom markers to Atlassian Document Format (ADF) JSON.

Parses custom markers (EXPAND, PANEL, MENTION, CARD, emoji, STATUS, DATE)
back into ADF nodes for round-trip fidelity with Confluence v2 API.

Usage:
    from markdown_to_adf import markdown_to_adf, has_custom_markers

    adf_json = markdown_to_adf(markdown_string)
    if has_custom_markers(markdown_string):
        # Use v2 ADF upload path
        ...
"""

import json
import re
import uuid
from typing import Any, Optional, Tuple

import mistune


def markdown_to_adf(markdown: str) -> dict:
    """
    Convert Markdown (with optional custom markers) to ADF JSON.

    Args:
        markdown: Markdown string, optionally containing custom markers
            from adf_to_markdown round-trip

    Returns:
        ADF document dict with type "doc" and "content" array
    """
    converter = _MarkdownToADFConverter()
    return converter.convert(markdown)


def has_custom_markers(markdown: str) -> bool:
    """
    Detect whether markdown contains custom roundtrip markers.

    Returns True if the markdown was likely produced by adf_to_markdown
    and contains markers for Confluence-specific elements.
    """
    marker_patterns = [
        r"<!-- EXPAND:",
        r"<!-- PANEL:",
        r"<!-- MENTION:",
        r"<!-- CARD:",
        r"<!-- STATUS:",
        r"<!-- DATE:",
        r"<!-- ADF:",
    ]
    return any(re.search(p, markdown) for p in marker_patterns)


def _gen_local_id() -> str:
    """Generate unique localId for ADF nodes that require it."""
    return str(uuid.uuid4())


_EMOJI_PREFIXES = (
    "✅",
    "❌",
    "⚠️",
    "⚠",
    "🔴",
    "🟢",
    "🟡",
    "🔵",
    "⭐",
    "🚀",
    "💡",
    "🎯",
    "📌",
    "📝",
    "🔥",
    "✨",
    "💥",
    "🏆",
    "🎉",
    "⛔",
    "🛑",
)


def _preprocess_markdown(markdown: str) -> str:
    """Normalize markdown patterns that cause rendering issues when uploaded.

    Fixes:
    - Consecutive lines starting with emoji (✅/❌/…) that aren't list items:
      joined into one paragraph by standard Markdown. Convert to ``- ✅ …``.
    - ``[ ]``/``[x]`` lines without ``- `` prefix: convert to task list items.
    """
    lines = markdown.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        # Lines starting with emoji but NOT already a list item
        if any(
            stripped.startswith(e) for e in _EMOJI_PREFIXES
        ) and not stripped.startswith("- "):
            out.append(f"- {stripped}")
        # Bare checkbox lines:  [ ] foo  or  [x] bar  (not already list items)
        elif re.match(r"^\[[ xX]\]\s", stripped) and not stripped.startswith("- "):
            out.append(f"- {stripped}")
        else:
            out.append(line)
    return "\n".join(out)


class _MarkdownToADFConverter:
    """Converts Markdown (via mistune AST) to ADF JSON nodes."""

    def convert(self, markdown: str) -> dict:
        markdown = _preprocess_markdown(markdown)
        md = mistune.create_markdown(
            renderer="ast", plugins=["table", "strikethrough", "task_lists"]
        )
        tokens = md(markdown)
        content = self._convert_tokens(tokens)

        if not content:
            content = [{"type": "paragraph", "content": []}]

        return {"version": 1, "type": "doc", "content": content}

    # ── Block-level token conversion ─────────────────────────────

    def _convert_tokens(self, tokens: list) -> list:
        """Convert mistune tokens to ADF block nodes.

        Handles block markers (EXPAND, PANEL, ADF:type) by collecting
        tokens between matching open/close HTML comment markers.
        """
        result = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            t = token.get("type", "")

            if t == "blank_line":
                i += 1
                continue

            if t == "block_html":
                node, skip = self._handle_block_html(tokens, i)
                if node is not None:
                    if isinstance(node, list):
                        result.extend(node)
                    else:
                        result.append(node)
                i += skip
                continue

            node = self._convert_token(token)
            if node is not None:
                if isinstance(node, list):
                    result.extend(node)
                else:
                    result.append(node)
            i += 1

        return result

    def _handle_block_html(self, tokens: list, idx: int) -> Tuple[Any, int]:
        """Handle block_html tokens including marker open/close pairs.

        Returns (adf_node_or_None, number_of_tokens_to_advance).
        """
        raw = tokens[idx].get("raw", "").strip()

        # EXPAND marker
        m = re.match(r"^<!-- EXPAND: (.+?) -->$", raw)
        if m:
            inner, end_i = self._collect_block(tokens, idx + 1, "EXPAND")
            if inner is not None:
                return (
                    self._build_expand(m.group(1), inner),
                    end_i - idx + 1,
                )
            return None, 1

        # PANEL marker
        m = re.match(r"^<!-- PANEL: (\w+) -->$", raw)
        if m:
            inner, end_i = self._collect_block(tokens, idx + 1, "PANEL")
            if inner is not None:
                return (
                    self._build_panel(m.group(1), inner),
                    end_i - idx + 1,
                )
            return None, 1

        # ADF:type marker (block with content, or leaf)
        m = re.match(r"^<!-- ADF:(\w+) (.+?) -->$", raw)
        if m:
            node_type = m.group(1)
            attrs_str = m.group(2)
            close_tag = f"ADF:{node_type}"
            inner, end_i = self._collect_block(tokens, idx + 1, close_tag)
            if inner is not None:
                return (
                    self._build_unknown_block(node_type, attrs_str, inner),
                    end_i - idx + 1,
                )
            # Leaf node (no closing tag found)
            return self._build_unknown_leaf(node_type, attrs_str), 1

        # Standalone inline marker on its own line
        # e.g. <!-- MENTION: ... --> as block_html
        node = self._try_inline_marker_as_block(raw)
        if node is not None:
            return {"type": "paragraph", "content": [node]}, 1

        # Multiple inline markers on one line
        # e.g. <!-- STATUS: "A" green --> <!-- STATUS: "B" red -->
        nodes = self._try_multiple_inline_markers_as_block(raw)
        if nodes:
            return {"type": "paragraph", "content": nodes}, 1

        return None, 1

    def _collect_block(
        self, tokens: list, start: int, tag: str
    ) -> Tuple[Optional[list], int]:
        """Collect tokens between matching open/close markers.

        Returns (inner_tokens, end_index) or (None, -1) if no close found.
        Handles nesting of same-type markers.
        """
        close_str = f"<!-- /{tag} -->"
        open_re = re.compile(r"^<!-- " + re.escape(tag) + r"[: ] .+? -->$")

        inner = []
        depth = 1
        i = start
        while i < len(tokens):
            t = tokens[i]
            if t.get("type") == "block_html":
                raw = t.get("raw", "").strip()
                if raw == close_str:
                    depth -= 1
                    if depth == 0:
                        return inner, i
                if open_re.match(raw):
                    depth += 1
            inner.append(t)
            i += 1
        return None, -1

    # ── Individual token converters ──────────────────────────────

    def _convert_token(self, token: dict) -> Any:
        t = token.get("type", "")
        handler = getattr(self, f"_tok_{t}", None)
        if handler:
            return handler(token)
        return None

    def _tok_paragraph(self, token: dict) -> Optional[dict]:
        children = token.get("children", [])
        inline = self._convert_inline(children)
        if not inline:
            return None
        return {"type": "paragraph", "content": inline}

    def _tok_heading(self, token: dict) -> dict:
        level = token.get("attrs", {}).get("level", 1)
        children = token.get("children", [])
        inline = self._convert_inline(children)
        node = {"type": "heading", "attrs": {"level": level}}
        if inline:
            node["content"] = inline
        return node

    def _tok_block_code(self, token: dict) -> dict:
        raw = token.get("raw", "").rstrip("\n")
        info = token.get("attrs", {}).get("info", "")
        node = {"type": "codeBlock", "attrs": {}}
        if info:
            node["attrs"]["language"] = info
        if raw:
            node["content"] = [{"type": "text", "text": raw}]
        return node

    def _tok_block_quote(self, token: dict) -> dict:
        children = token.get("children", [])
        content = self._convert_tokens(children)
        return {"type": "blockquote", "content": content}

    def _tok_thematic_break(self, token: dict) -> dict:
        return {"type": "rule"}

    def _tok_list(self, token: dict) -> dict:
        attrs = token.get("attrs", {})
        ordered = attrs.get("ordered", False)
        items = token.get("children", [])

        # Detect task list: all children are task_list_item AND none have
        # nested lists (ADF taskItem only supports inline content).
        is_task = all(c.get("type") == "task_list_item" for c in items) and not any(
            any(gc.get("type") == "list" for gc in c.get("children", [])) for c in items
        )
        if is_task and items:
            content = [self._convert_task_list_item(item) for item in items]
            return {
                "type": "taskList",
                "attrs": {"localId": _gen_local_id()},
                "content": content,
            }

        content = [self._convert_list_item(item) for item in items]
        return {
            "type": "orderedList" if ordered else "bulletList",
            "content": content,
        }

    def _convert_task_list_item(self, token: dict) -> dict:
        """Convert a mistune task_list_item token to an ADF taskItem node."""
        checked = token.get("attrs", {}).get("checked", False)
        state = "DONE" if checked else "TODO"
        children = token.get("children", [])
        content = []
        for child in children:
            ct = child.get("type", "")
            if ct == "block_text":
                inline = self._convert_inline(child.get("children", []))
                if inline:
                    content.extend(inline)
            elif ct == "paragraph":
                inline = self._convert_inline(child.get("children", []))
                if inline:
                    content.extend(inline)
            else:
                node = self._convert_token(child)
                if node is not None:
                    if isinstance(node, list):
                        content.extend(node)
                    else:
                        content.append(node)
        return {
            "type": "taskItem",
            "attrs": {"localId": _gen_local_id(), "state": state},
            "content": content,
        }

    def _convert_list_item(self, token: dict) -> dict:
        children = token.get("children", [])
        content = []
        for child in children:
            ct = child.get("type", "")
            if ct == "block_text":
                # block_text is mistune's inline container inside list items
                inline = self._convert_inline(child.get("children", []))
                if inline:
                    content.append({"type": "paragraph", "content": inline})
            elif ct == "list":
                content.append(self._tok_list(child))
            elif ct == "paragraph":
                node = self._tok_paragraph(child)
                if node:
                    content.append(node)
            else:
                node = self._convert_token(child)
                if node is not None:
                    if isinstance(node, list):
                        content.extend(node)
                    else:
                        content.append(node)
        if not content:
            content.append({"type": "paragraph", "content": []})
        return {"type": "listItem", "content": content}

    def _tok_table(self, token: dict) -> dict:
        children = token.get("children", [])
        rows = []
        for child in children:
            ct = child.get("type", "")
            if ct == "table_head":
                row_cells = [
                    self._convert_table_cell(cell, is_header=True)
                    for cell in child.get("children", [])
                ]
                rows.append({"type": "tableRow", "content": row_cells})
            elif ct == "table_body":
                for row in child.get("children", []):
                    row_cells = [
                        self._convert_table_cell(cell, is_header=False)
                        for cell in row.get("children", [])
                    ]
                    rows.append({"type": "tableRow", "content": row_cells})
        return {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": rows,
        }

    def _convert_table_cell(self, cell: dict, is_header: bool) -> dict:
        children = cell.get("children", [])
        inline = self._convert_inline(children)
        cell_type = "tableHeader" if is_header else "tableCell"
        para = (
            {"type": "paragraph", "content": inline}
            if inline
            else {"type": "paragraph", "content": []}
        )
        return {"type": cell_type, "attrs": {}, "content": [para]}

    # ── Block marker builders ────────────────────────────────────

    def _build_expand(self, attrs_str: str, inner_tokens: list) -> dict:
        """Build ADF expand node from marker attributes and inner tokens."""
        # Parse: "title" breakout="wide" width="1800"
        title_m = re.match(r'"(.+?)"(.*)', attrs_str.strip())
        title = title_m.group(1) if title_m else attrs_str.strip().strip('"')
        rest = title_m.group(2) if title_m else ""

        content = self._convert_tokens(inner_tokens)
        if not content:
            content = [{"type": "paragraph", "content": []}]

        node = {
            "type": "expand",
            "attrs": {"title": title},
            "content": content,
        }

        # Restore breakout marks
        breakout_m = re.search(r'breakout="(\w+)"', rest)
        if breakout_m:
            mark_attrs = {"mode": breakout_m.group(1)}
            width_m = re.search(r'width="(\d+)"', rest)
            if width_m:
                mark_attrs["width"] = int(width_m.group(1))
            node["marks"] = [{"type": "breakout", "attrs": mark_attrs}]

        return node

    def _build_panel(self, panel_type: str, inner_tokens: list) -> dict:
        """Build ADF panel node."""
        content = self._convert_tokens(inner_tokens)
        if not content:
            content = [{"type": "paragraph", "content": []}]
        return {
            "type": "panel",
            "attrs": {"panelType": panel_type},
            "content": content,
        }

    def _build_unknown_block(
        self, node_type: str, attrs_str: str, inner_tokens: list
    ) -> dict:
        """Restore unknown ADF block node from pass-through marker."""
        try:
            attrs = json.loads(attrs_str)
        except json.JSONDecodeError:
            attrs = {}
        content = self._convert_tokens(inner_tokens)
        node = {"type": node_type, "attrs": attrs}
        if content:
            node["content"] = content
        return node

    def _build_unknown_leaf(self, node_type: str, attrs_str: str) -> dict:
        """Restore unknown ADF leaf node from pass-through marker."""
        try:
            attrs = json.loads(attrs_str)
        except json.JSONDecodeError:
            attrs = {}
        return {"type": node_type, "attrs": attrs}

    # ── Inline token conversion ──────────────────────────────────

    def _convert_inline(self, tokens: list) -> list:
        """Convert inline tokens to ADF inline content.

        Handles HTML tag merging for <u>, <sub>, <sup> and
        custom marker detection for MENTION, CARD, STATUS, DATE.
        """
        merged = self._merge_html_tags(tokens)

        result = []
        for token in merged:
            nodes = self._convert_inline_token(token)
            if nodes is not None:
                if isinstance(nodes, list):
                    result.extend(nodes)
                else:
                    result.append(nodes)
        return result

    def _merge_html_tags(self, tokens: list) -> list:
        """Merge <u>text</u>, <sub>text</sub>, <sup>text</sup> sequences.

        Mistune splits these into separate inline_html tokens for the
        opening/closing tags. We merge them into synthetic tokens that
        carry the inner content as children.
        """
        result = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.get("type") == "inline_html":
                raw = token.get("raw", "").strip()
                tag_m = re.match(r"^<(u|sub|sup)>$", raw)
                if tag_m:
                    tag = tag_m.group(1)
                    close_tag = f"</{tag}>"
                    inner = []
                    j = i + 1
                    found = False
                    while j < len(tokens):
                        if (
                            tokens[j].get("type") == "inline_html"
                            and tokens[j].get("raw", "").strip() == close_tag
                        ):
                            found = True
                            break
                        inner.append(tokens[j])
                        j += 1
                    if found:
                        result.append({"type": f"_html_{tag}", "children": inner})
                        i = j + 1
                        continue
            result.append(token)
            i += 1
        return result

    def _convert_inline_token(
        self, token: dict, extra_marks: Optional[list] = None
    ) -> Any:
        """Convert a single inline token to ADF inline node(s).

        extra_marks: marks inherited from parent formatting (bold, italic, etc.)
        """
        t = token.get("type", "")

        if t == "text":
            return self._process_text(token.get("raw", ""), extra_marks)

        if t == "emphasis":
            return self._wrap_marks(token, {"type": "em"}, extra_marks)

        if t == "strong":
            return self._wrap_marks(token, {"type": "strong"}, extra_marks)

        if t == "strikethrough":
            return self._wrap_marks(token, {"type": "strike"}, extra_marks)

        if t == "codespan":
            raw = token.get("raw", "")
            marks = [{"type": "code"}]
            if extra_marks:
                marks.extend(extra_marks)
            return {"type": "text", "text": raw, "marks": marks}

        if t == "link":
            children = token.get("children", [])
            text = self._get_inline_text(children)
            href = token.get("attrs", {}).get("url", "")
            marks = [{"type": "link", "attrs": {"href": href}}]
            if extra_marks:
                marks.extend(extra_marks)
            return {"type": "text", "text": text, "marks": marks}

        if t == "image":
            attrs = token.get("attrs", {})
            alt_children = token.get("children", [])
            alt = self._get_inline_text(alt_children)
            src = attrs.get("url", "")
            return {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "file",
                            "collection": "",
                            "id": "",
                            "__fileName": src.lstrip("./"),
                            "alt": alt,
                        },
                    }
                ],
            }

        if t == "linebreak":
            return {"type": "hardBreak"}

        if t == "softbreak":
            return None

        if t == "inline_html":
            return self._process_inline_html(token.get("raw", "").strip())

        # Synthetic tokens from _merge_html_tags
        if t == "_html_u":
            return self._wrap_marks(token, {"type": "underline"}, extra_marks)

        if t == "_html_sub":
            return self._wrap_marks(
                token,
                {"type": "subsup", "attrs": {"type": "sub"}},
                extra_marks,
            )

        if t == "_html_sup":
            return self._wrap_marks(
                token,
                {"type": "subsup", "attrs": {"type": "sup"}},
                extra_marks,
            )

        return None

    def _process_text(self, text: str, marks: Optional[list] = None) -> Any:
        """Process text, splitting :emoji: patterns into separate nodes."""
        if not text:
            return None

        emoji_re = re.compile(r"(:[a-zA-Z0-9_+\-]+:)")
        parts = emoji_re.split(text)

        if len(parts) == 1:
            node = {"type": "text", "text": text}
            if marks:
                node["marks"] = marks
            return node

        nodes = []
        for part in parts:
            if not part:
                continue
            if emoji_re.match(part):
                nodes.append({"type": "emoji", "attrs": {"shortName": part}})
            else:
                node = {"type": "text", "text": part}
                if marks:
                    node["marks"] = marks
                nodes.append(node)

        if not nodes:
            return None
        return nodes if len(nodes) != 1 else nodes[0]

    def _wrap_marks(
        self,
        token: dict,
        mark: dict,
        extra_marks: Optional[list] = None,
    ) -> Any:
        """Apply a mark to all text children of a token."""
        children = token.get("children", [])
        all_marks = [mark]
        if extra_marks:
            all_marks.extend(extra_marks)

        result = []
        for child in children:
            nodes = self._convert_inline_token(child, all_marks)
            if nodes is not None:
                if isinstance(nodes, list):
                    result.extend(nodes)
                else:
                    result.append(nodes)

        if not result:
            return None
        return result if len(result) != 1 else result[0]

    def _process_inline_html(self, html: str) -> Any:
        """Parse inline HTML for custom markers."""
        # <!-- MENTION: id "text" -->
        m = re.match(r'^<!-- MENTION: (\S+) "(.+?)" -->$', html)
        if m:
            return {
                "type": "mention",
                "attrs": {
                    "id": m.group(1),
                    "text": m.group(2),
                    "accessLevel": "",
                },
            }

        # <!-- CARD: url -->
        m = re.match(r"^<!-- CARD: (.+?) -->$", html)
        if m:
            return {"type": "inlineCard", "attrs": {"url": m.group(1)}}

        # <!-- STATUS: "text" color -->
        m = re.match(r'^<!-- STATUS: "([^"]+)" (\w+) -->$', html)
        if m:
            return {
                "type": "status",
                "attrs": {
                    "text": m.group(1),
                    "color": m.group(2),
                    "localId": _gen_local_id(),
                    "style": "bold",
                },
            }

        # <!-- DATE: timestamp -->
        m = re.match(r"^<!-- DATE: (\d+) -->$", html)
        if m:
            return {"type": "date", "attrs": {"timestamp": m.group(1)}}

        # <!-- ADF:type {...} --> (inline leaf)
        m = re.match(r"^<!-- ADF:(\w+) ({.+}) -->$", html)
        if m:
            try:
                attrs = json.loads(m.group(2))
            except json.JSONDecodeError:
                attrs = {}
            return {"type": m.group(1), "attrs": attrs}

        # Unknown inline HTML — preserve as text
        return {"type": "text", "text": html}

    def _try_inline_marker_as_block(self, html: str) -> Any:
        """Try to parse a block_html token as a standalone inline marker.

        When markers like <!-- MENTION: ... --> appear on their own line,
        mistune treats them as block_html. We wrap them in a paragraph.
        """
        node = self._process_inline_html(html)
        if node and node.get("type") != "text":
            return node
        return None

    def _try_multiple_inline_markers_as_block(self, html: str) -> Optional[list]:
        """Parse block_html containing multiple inline markers.

        When a paragraph contains only inline markers (e.g., several STATUS
        nodes), mistune emits the entire line as one block_html token.
        We split it into individual <!-- ... --> markers and process each.
        """
        parts = re.findall(r"<!--.*?-->", html)
        if len(parts) < 2:
            return None

        nodes = []
        for part in parts:
            node = self._process_inline_html(part.strip())
            if node is None:
                continue
            if nodes and node.get("type") != "text":
                nodes.append({"type": "text", "text": " "})
            nodes.append(node)

        if any(n.get("type") != "text" for n in nodes):
            return nodes
        return None

    # ── Helpers ──────────────────────────────────────────────────

    def _get_inline_text(self, tokens: list) -> str:
        """Extract plain text from inline tokens."""
        parts = []
        for token in tokens:
            t = token.get("type", "")
            if t == "text":
                parts.append(token.get("raw", ""))
            elif t in ("emphasis", "strong", "strikethrough"):
                parts.append(self._get_inline_text(token.get("children", [])))
            elif t == "codespan":
                parts.append(token.get("raw", ""))
        return "".join(parts)
