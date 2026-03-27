#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Convert Atlassian Document Format (ADF) JSON to Markdown with custom markers.

Preserves Confluence-specific elements (expand, emoji, mention, inlineCard,
panel, status, date) as HTML comment markers for round-trip fidelity.

Usage:
    from adf_to_markdown import adf_to_markdown

    markdown = adf_to_markdown(adf_json_dict)
"""

import json
from typing import Optional


def adf_to_markdown(adf: dict) -> str:
    """
    Convert ADF JSON document to Markdown with custom markers.

    Args:
        adf: ADF document dict (must have type "doc" and "content" array)

    Returns:
        Markdown string with custom markers for Confluence elements
    """
    converter = _ADFConverter()
    return converter.convert(adf)


class _ADFConverter:
    """Recursive ADF tree walker that produces Markdown output."""

    def convert(self, adf: dict) -> str:
        if adf.get("type") != "doc":
            return ""
        lines = []
        for node in adf.get("content", []):
            result = self._convert_node(node, depth=0)
            if result is not None:
                lines.append(result)
        return "\n".join(lines).strip() + "\n"

    def _convert_node(self, node: dict, depth: int = 0) -> Optional[str]:
        if not isinstance(node, dict):
            return None

        node_type = node.get("type", "")
        handler = getattr(self, f"_convert_{node_type}", None)
        if handler:
            return handler(node, depth)

        # Unknown node type: pass-through marker
        return self._convert_unknown(node, depth)

    # ── Block elements ──────────────────────────────────────────────

    def _convert_paragraph(self, node: dict, depth: int) -> str:
        text = self._convert_inline_content(node.get("content", []))
        return text + "\n"

    def _convert_heading(self, node: dict, depth: int) -> str:
        level = node.get("attrs", {}).get("level", 1)
        text = self._convert_inline_content(node.get("content", []))
        return f"{'#' * level} {text}\n"

    def _convert_bulletList(self, node: dict, depth: int) -> str:
        items = []
        for item in node.get("content", []):
            items.append(self._convert_listItem(item, depth, ordered=False))
        return "\n".join(items) + "\n"

    def _convert_orderedList(self, node: dict, depth: int) -> str:
        items = []
        for i, item in enumerate(node.get("content", []), 1):
            items.append(self._convert_listItem(item, depth, ordered=True, index=i))
        return "\n".join(items) + "\n"

    def _convert_listItem(
        self, node: dict, depth: int, ordered: bool = False, index: int = 1
    ) -> str:
        indent = "  " * depth
        prefix = f"{index}." if ordered else "-"
        parts = []
        for child in node.get("content", []):
            child_type = child.get("type", "")
            if child_type == "paragraph":
                text = self._convert_inline_content(child.get("content", []))
                parts.append(f"{indent}{prefix} {text}")
            elif child_type == "bulletList":
                # Nested list
                for sub_item in child.get("content", []):
                    parts.append(
                        self._convert_listItem(sub_item, depth + 1, ordered=False)
                    )
            elif child_type == "orderedList":
                for j, sub_item in enumerate(child.get("content", []), 1):
                    parts.append(
                        self._convert_listItem(
                            sub_item, depth + 1, ordered=True, index=j
                        )
                    )
            else:
                result = self._convert_node(child, depth + 1)
                if result is not None:
                    parts.append(f"{indent}  {result.strip()}")
        return "\n".join(parts)

    def _convert_codeBlock(self, node: dict, depth: int) -> str:
        lang = node.get("attrs", {}).get("language", "")
        text = self._get_plain_text(node)
        return f"```{lang}\n{text}\n```\n"

    def _convert_blockquote(self, node: dict, depth: int) -> str:
        lines = []
        for child in node.get("content", []):
            result = self._convert_node(child, depth)
            if result is not None:
                for line in result.strip().split("\n"):
                    lines.append(f"> {line}")
        return "\n".join(lines) + "\n"

    def _convert_rule(self, node: dict, depth: int) -> str:
        return "---\n"

    def _convert_table(self, node: dict, depth: int) -> str:
        rows = node.get("content", [])
        if not rows:
            return ""

        md_rows = []
        for row in rows:
            cells = []
            for cell in row.get("content", []):
                cell_text = self._convert_inline_content_from_block(cell)
                cells.append(cell_text.replace("|", "\\|"))
            md_rows.append("| " + " | ".join(cells) + " |")

        if len(md_rows) >= 1:
            # Add separator after header row
            num_cols = md_rows[0].count("|") - 1
            separator = "| " + " | ".join(["---"] * num_cols) + " |"
            result = [md_rows[0], separator] + md_rows[1:]
            return "\n".join(result) + "\n"

        return "\n".join(md_rows) + "\n"

    def _convert_hardBreak(self, node: dict, depth: int) -> str:
        return "\n"

    # ── Media ───────────────────────────────────────────────────────

    def _convert_mediaSingle(self, node: dict, depth: int) -> str:
        for child in node.get("content", []):
            if child.get("type") == "media":
                return self._convert_media(child, depth)
        return ""

    def _convert_media(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        alt = attrs.get("alt", "")
        # For attachments, use filename from the __fileName attribute
        filename = attrs.get("__fileName", "")
        if not filename:
            filename = attrs.get("id", "image")
        return f"![{alt}](./{filename})\n"

    def _convert_mediaGroup(self, node: dict, depth: int) -> str:
        parts = []
        for child in node.get("content", []):
            if child.get("type") == "media":
                parts.append(self._convert_media(child, depth).strip())
        return "\n".join(parts) + "\n"

    # ── Confluence-specific elements (markers) ──────────────────────

    def _convert_expand(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        title = attrs.get("title", "")
        marks = node.get("marks", [])

        # Build marker with optional breakout attributes
        marker_parts = [f'<!-- EXPAND: "{title}"']
        for mark in marks:
            if mark.get("type") == "breakout":
                mark_attrs = mark.get("attrs", {})
                mode = mark_attrs.get("mode", "")
                width = mark_attrs.get("width", "")
                if mode:
                    marker_parts.append(f'breakout="{mode}"')
                if width:
                    marker_parts.append(f'width="{width}"')
        marker = " ".join(marker_parts) + " -->"

        # Convert children
        children_md = []
        for child in node.get("content", []):
            result = self._convert_node(child, depth)
            if result is not None:
                children_md.append(result)

        content = "\n".join(children_md).strip()
        return f"{marker}\n{content}\n<!-- /EXPAND -->\n"

    def _convert_panel(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        panel_type = attrs.get("panelType", "info")

        children_md = []
        for child in node.get("content", []):
            result = self._convert_node(child, depth)
            if result is not None:
                children_md.append(result)

        content = "\n".join(children_md).strip()
        return f"<!-- PANEL: {panel_type} -->\n{content}\n<!-- /PANEL -->\n"

    def _convert_emoji(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        short_name = attrs.get("shortName", "")
        return short_name

    def _convert_mention(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        user_id = attrs.get("id", "")
        text = attrs.get("text", "")
        return f'<!-- MENTION: {user_id} "{text}" -->'

    def _convert_inlineCard(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        url = attrs.get("url", "")
        return f"<!-- CARD: {url} -->"

    def _convert_status(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        text = attrs.get("text", "")
        color = attrs.get("color", "neutral")
        return f'<!-- STATUS: "{text}" {color} -->'

    def _convert_date(self, node: dict, depth: int) -> str:
        attrs = node.get("attrs", {})
        timestamp = attrs.get("timestamp", "")
        return f"<!-- DATE: {timestamp} -->"

    # ── Unknown node pass-through ───────────────────────────────────

    def _convert_unknown(self, node: dict, depth: int) -> str:
        node_type = node.get("type", "unknown")
        attrs = node.get("attrs", {})

        # If it has content children, try to convert them
        children = node.get("content", [])
        if children:
            children_md = []
            for child in children:
                result = self._convert_node(child, depth)
                if result is not None:
                    children_md.append(result)
            content = "\n".join(children_md).strip()
            attrs_json = json.dumps(attrs) if attrs else "{}"
            return f"<!-- ADF:{node_type} {attrs_json} -->\n{content}\n<!-- /ADF:{node_type} -->\n"

        # Leaf node with no children
        attrs_json = json.dumps(attrs) if attrs else "{}"
        return f"<!-- ADF:{node_type} {attrs_json} -->"

    # ── Inline content handling ─────────────────────────────────────

    def _convert_inline_content(self, content: list) -> str:
        """Convert a list of inline ADF nodes to markdown text."""
        parts = []
        for node in content:
            node_type = node.get("type", "")
            if node_type == "text":
                parts.append(self._convert_text(node))
            elif node_type == "emoji":
                parts.append(self._convert_emoji(node, 0))
            elif node_type == "mention":
                parts.append(self._convert_mention(node, 0))
            elif node_type == "inlineCard":
                parts.append(self._convert_inlineCard(node, 0))
            elif node_type == "status":
                parts.append(self._convert_status(node, 0))
            elif node_type == "date":
                parts.append(self._convert_date(node, 0))
            elif node_type == "hardBreak":
                parts.append("\n")
            else:
                # Unknown inline element
                attrs = node.get("attrs", {})
                attrs_json = json.dumps(attrs) if attrs else "{}"
                parts.append(f"<!-- ADF:{node_type} {attrs_json} -->")
        return "".join(parts)

    def _convert_text(self, node: dict, depth: int = 0) -> str:
        """Convert a text node with marks to markdown inline formatting."""
        text = node.get("text", "")
        marks = node.get("marks", [])

        for mark in marks:
            mark_type = mark.get("type", "")
            attrs = mark.get("attrs", {})

            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "em":
                text = f"*{text}*"
            elif mark_type == "code":
                text = f"`{text}`"
            elif mark_type == "strike":
                text = f"~~{text}~~"
            elif mark_type == "underline":
                text = f"<u>{text}</u>"
            elif mark_type == "link":
                href = attrs.get("href", "")
                text = f"[{text}]({href})"
            elif mark_type == "subsup":
                sub_type = attrs.get("type", "sub")
                text = f"<{sub_type}>{text}</{sub_type}>"

        return text

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_plain_text(self, node: dict) -> str:
        """Extract plain text from a node, ignoring marks."""
        if node.get("type") == "text":
            return node.get("text", "")
        parts = []
        for child in node.get("content", []):
            parts.append(self._get_plain_text(child))
        return "".join(parts)

    def _convert_inline_content_from_block(self, cell_node: dict) -> str:
        """Convert block-level cell content to inline text for table cells."""
        parts = []
        for child in cell_node.get("content", []):
            child_type = child.get("type", "")
            if child_type == "paragraph":
                parts.append(self._convert_inline_content(child.get("content", [])))
            else:
                text = self._get_plain_text(child)
                if text:
                    parts.append(text)
        return " ".join(parts)

    # ── Table sub-elements (handled by _convert_table) ──────────────

    def _convert_tableRow(self, node: dict, depth: int) -> Optional[str]:
        return None  # Handled by _convert_table

    def _convert_tableHeader(self, node: dict, depth: int) -> Optional[str]:
        return None  # Handled by _convert_table

    def _convert_tableCell(self, node: dict, depth: int) -> Optional[str]:
        return None  # Handled by _convert_table
