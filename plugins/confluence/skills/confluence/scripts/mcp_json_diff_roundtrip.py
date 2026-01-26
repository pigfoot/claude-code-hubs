#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
MCP + JSON Diff Roundtrip (Method 6) for Confluence page editing.

This module provides intelligent roundtrip editing that preserves all macros
while allowing Claude to edit text content. Features include:
- Safe Mode (default): Skip macro body content
- Advanced Mode (opt-in): Edit macro body content with user confirmation
- Automatic backup before every edit
- Auto-rollback on failure

Usage:
    # This module is designed to be imported and used by Claude in conversation
    # with MCP tools, not run as a standalone script.

    from mcp_json_diff_roundtrip import MCPJsonDiffRoundtrip, BackupManager
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class TextNode:
    """Represents a text node with its JSON path."""
    path: str  # JSON path like "content.0.content.1.text"
    text: str


@dataclass
class TextChange:
    """Represents a text change to apply."""
    path: str
    old_text: str
    new_text: str


@dataclass
class MacroInfo:
    """Information about a detected macro with editable content."""
    type: str  # e.g., "expand", "panel", "info"
    preview: str  # First 50 chars of content
    text_count: int  # Number of text nodes inside


class ADFTextExtractor:
    """Extracts and patches text nodes from Atlassian Document Format (ADF)."""

    # Node types that represent macros/special structures
    MACRO_NODE_TYPES = {"inlineExtension", "extension", "bodiedExtension", "panel", "expand"}

    def __init__(self, skip_macro_bodies: bool = True):
        """
        Initialize the text extractor.

        Args:
            skip_macro_bodies: If True, skip text inside macros (Safe Mode).
                              If False, include macro body text (Advanced Mode).
        """
        self.skip_macro_bodies = skip_macro_bodies

    def extract_text_nodes(self, adf: dict) -> list[TextNode]:
        """
        Extract all text nodes with their JSON paths from ADF.

        Args:
            adf: ADF JSON structure

        Returns:
            List of TextNode objects with paths and text
        """
        text_nodes = []
        self._extract_recursive(adf, "", text_nodes, inside_macro=False)
        return text_nodes

    def _extract_recursive(
        self,
        node: Any,
        path: str,
        text_nodes: list[TextNode],
        inside_macro: bool
    ) -> None:
        """Recursively extract text nodes from ADF structure."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")
        attrs = node.get("attrs", {})

        # Check if this is a macro node (by type or by special attributes)
        is_macro = (
            node_type in self.MACRO_NODE_TYPES or
            "extensionKey" in attrs or
            "panelType" in attrs  # For panel nodes
        )

        # Decide whether to skip this subtree
        if is_macro and self.skip_macro_bodies:
            # Skip entire macro subtree in Safe Mode
            return

        # If this is a text node, extract it (unless we're inside a macro in Safe Mode)
        if node_type == "text" and not (inside_macro and self.skip_macro_bodies):
            text = node.get("text", "")
            if text.strip():  # Only include non-empty text
                text_path = f"{path}.text" if path else "text"
                text_nodes.append(TextNode(path=text_path, text=text))

        # Recurse into content array
        content = node.get("content")
        if isinstance(content, list):
            for i, child in enumerate(content):
                child_path = f"{path}.content.{i}" if path else f"content.{i}"
                self._extract_recursive(
                    child,
                    child_path,
                    text_nodes,
                    inside_macro=is_macro or inside_macro
                )

    def apply_text_changes(self, adf: dict, changes: list[TextChange]) -> dict:
        """
        Apply text changes to ADF by path.

        Args:
            adf: Original ADF structure
            changes: List of text changes to apply

        Returns:
            Modified ADF structure (original is not mutated)
        """
        # Deep copy to avoid mutating original
        import copy
        result = copy.deepcopy(adf)

        for change in changes:
            self._apply_change(result, change)

        return result

    def _apply_change(self, adf: dict, change: TextChange) -> None:
        """Apply a single text change by navigating the path."""
        path_parts = change.path.split(".")

        # Navigate to parent node
        current = adf
        for part in path_parts[:-1]:
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]

        # Apply change to text field
        last_part = path_parts[-1]
        if last_part == "text":
            current["text"] = change.new_text


class SimpleMarkdownConverter:
    """Converts ADF to Markdown for Claude editing."""

    def convert_to_markdown(self, adf: dict, include_macro_bodies: bool = False) -> str:
        """
        Convert ADF to Markdown.

        Args:
            adf: ADF JSON structure
            include_macro_bodies: If True, include text from macro bodies

        Returns:
            Markdown string
        """
        lines = []
        self._convert_recursive(adf, lines, inside_macro=False, include_macro_bodies=include_macro_bodies)
        return "\n".join(lines)

    def _convert_recursive(
        self,
        node: Any,
        lines: list[str],
        inside_macro: bool,
        include_macro_bodies: bool
    ) -> None:
        """Recursively convert ADF nodes to Markdown."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        # Check if this is a macro
        attrs = node.get("attrs", {})
        is_macro = (
            node_type in ADFTextExtractor.MACRO_NODE_TYPES or
            "extensionKey" in attrs or
            "panelType" in attrs
        )

        if is_macro:
            # Insert placeholder comment with macro identifier
            macro_id = (
                attrs.get("extensionKey") or
                attrs.get("panelType") or
                node_type
            )
            lines.append(f"\n<!-- MACRO: {macro_id} -->\n")

            if not include_macro_bodies:
                # Skip macro content in Safe Mode
                return

        # Convert based on node type
        if node_type == "heading":
            level = node.get("attrs", {}).get("level", 1)
            text = self._extract_text(node)
            lines.append(f"{'#' * level} {text}")

        elif node_type == "paragraph":
            text = self._extract_text(node)
            if text.strip():
                lines.append(text)
                lines.append("")  # Add blank line after paragraph

        elif node_type == "bulletList":
            self._convert_list(node, lines, ordered=False)

        elif node_type == "orderedList":
            self._convert_list(node, lines, ordered=True)

        elif node_type == "codeBlock":
            language = node.get("attrs", {}).get("language", "")
            text = self._extract_text(node)
            lines.append(f"```{language}")
            lines.append(text)
            lines.append("```")
            lines.append("")

        elif node_type == "blockquote":
            text = self._extract_text(node)
            for line in text.split("\n"):
                lines.append(f"> {line}")
            lines.append("")

        elif node_type == "doc":
            # Document root - process content
            content = node.get("content", [])
            for child in content:
                self._convert_recursive(child, lines, inside_macro, include_macro_bodies)

        # For other types, just recurse into content
        elif "content" in node:
            for child in node["content"]:
                self._convert_recursive(child, lines, is_macro or inside_macro, include_macro_bodies)

    def _extract_text(self, node: dict) -> str:
        """Extract all text from a node and its children."""
        if node.get("type") == "text":
            return node.get("text", "")

        content = node.get("content", [])
        texts = [self._extract_text(child) for child in content]
        return "".join(texts)

    def _convert_list(self, node: dict, lines: list[str], ordered: bool) -> None:
        """Convert a list node to Markdown."""
        items = node.get("content", [])
        for i, item in enumerate(items):
            prefix = f"{i + 1}." if ordered else "-"
            text = self._extract_text(item)
            lines.append(f"{prefix} {text}")
        lines.append("")


class TextDiffer:
    """Computes text changes between original and edited content."""

    def __init__(self, overlap_threshold: float = 0.3):
        """
        Initialize the differ.

        Args:
            overlap_threshold: Minimum word overlap to consider texts matching
        """
        self.overlap_threshold = overlap_threshold

    def compute_changes(
        self,
        original_nodes: list[TextNode],
        edited_markdown: str
    ) -> list[TextChange]:
        """
        Compute text changes by comparing original nodes with edited markdown.

        Args:
            original_nodes: Original text nodes from ADF
            edited_markdown: Markdown edited by Claude

        Returns:
            List of TextChange objects
        """
        # Extract text lines from markdown (ignore markdown syntax)
        edited_texts = self._extract_text_from_markdown(edited_markdown)

        changes = []
        used_edited = set()

        # Match each original text node with edited text
        for node in original_nodes:
            best_match = None
            best_overlap = 0.0

            for i, edited_text in enumerate(edited_texts):
                if i in used_edited:
                    continue

                overlap = self._compute_word_overlap(node.text, edited_text)
                if overlap > best_overlap and overlap >= self.overlap_threshold:
                    best_overlap = overlap
                    best_match = (i, edited_text)

            if best_match and best_match[1] != node.text:
                # Text changed
                changes.append(TextChange(
                    path=node.path,
                    old_text=node.text,
                    new_text=best_match[1]
                ))
                used_edited.add(best_match[0])

        return changes

    def _extract_text_from_markdown(self, markdown: str) -> list[str]:
        """Extract plain text lines from markdown (strip formatting)."""
        texts = []

        for line in markdown.split("\n"):
            line = line.strip()

            # Skip empty lines and macro comments
            if not line or line.startswith("<!--"):
                continue

            # Strip markdown formatting
            # Remove headers
            line = re.sub(r"^#{1,6}\s+", "", line)
            # Remove list markers
            line = re.sub(r"^[-*+]\s+", "", line)
            line = re.sub(r"^\d+\.\s+", "", line)
            # Remove blockquote markers
            line = re.sub(r"^>\s+", "", line)
            # Remove code block markers
            if line.startswith("```"):
                continue

            # Remove inline formatting (bold, italic, code)
            line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
            line = re.sub(r"\*(.+?)\*", r"\1", line)
            line = re.sub(r"`(.+?)`", r"\1", line)

            if line:
                texts.append(line)

        return texts

    def _compute_word_overlap(self, text1: str, text2: str) -> float:
        """Compute word overlap ratio between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        total = len(words1 | words2)

        return overlap / total if total > 0 else 0.0


class MacroBodyDetector:
    """Detects and analyzes macros with editable content."""

    # Map of macro identifiers to friendly names
    MACRO_TYPES = {
        "expand": "Expand Panel",
        "panel": "Panel",
        "info": "Info Panel",
        "note": "Note Panel",
        "warning": "Warning Panel",
        "tip": "Tip Panel",
        "success": "Success Panel",
        "error": "Error Panel",
    }

    # ADF node types that represent macros
    MACRO_NODE_TYPES = {"panel", "expand", "inlineExtension", "extension", "bodiedExtension"}

    def detect_macros_with_content(self, adf: dict) -> list[MacroInfo]:
        """
        Detect macros that contain editable text content.

        Args:
            adf: ADF JSON structure

        Returns:
            List of MacroInfo objects
        """
        macros = []
        self._detect_recursive(adf, macros)
        return macros

    def _detect_recursive(self, node: Any, macros: list[MacroInfo]) -> None:
        """Recursively detect macros with content."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        # Check if this is a macro node
        is_macro = node_type in self.MACRO_NODE_TYPES

        if is_macro:
            # Get macro identifier
            attrs = node.get("attrs", {})

            # Try different ways to identify macro type
            macro_identifier = (
                attrs.get("extensionKey") or  # For extension nodes
                attrs.get("panelType") or      # For panel nodes
                node_type                       # Fallback to node type
            )

            # Count text nodes inside
            text_count = self._count_text_nodes(node)

            if text_count > 0:
                # Extract preview
                preview = self._extract_preview(node)

                # Get friendly name
                macro_type = self.MACRO_TYPES.get(macro_identifier, macro_identifier.title())

                macros.append(MacroInfo(
                    type=macro_type,
                    preview=preview,
                    text_count=text_count
                ))

        # Recurse into content (don't recurse if we already processed this macro)
        if not is_macro:
            content = node.get("content", [])
            if isinstance(content, list):
                for child in content:
                    self._detect_recursive(child, macros)

    def _count_text_nodes(self, node: Any) -> int:
        """Count text nodes inside a macro."""
        if not isinstance(node, dict):
            return 0

        count = 0

        if node.get("type") == "text":
            text = node.get("text", "")
            if text.strip():
                count += 1

        content = node.get("content", [])
        if isinstance(content, list):
            for child in content:
                count += self._count_text_nodes(child)

        return count

    def _extract_preview(self, node: dict, max_chars: int = 50) -> str:
        """Extract preview text (first N chars) from macro body."""
        text = self._extract_all_text(node)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def _extract_all_text(self, node: Any) -> str:
        """Extract all text from a node."""
        if not isinstance(node, dict):
            return ""

        if node.get("type") == "text":
            return node.get("text", "")

        content = node.get("content", [])
        if isinstance(content, list):
            texts = [self._extract_all_text(child) for child in content]
            return " ".join(t for t in texts if t)

        return ""


class BackupManager:
    """Manages backups and rollbacks for Confluence pages."""

    def __init__(self, backup_dir: Path | None = None, retention_limit: int = 10):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory for backups (default: .confluence_backups)
            retention_limit: Max backups per page (default: 10)
        """
        self.backup_dir = backup_dir or Path(".confluence_backups")
        self.retention_limit = retention_limit

    def create_backup(
        self,
        page_id: str,
        adf_content: dict,
        version: int,
        title: str,
        space_id: str
    ) -> Path:
        """
        Create a backup of page content.

        Args:
            page_id: Confluence page ID
            adf_content: ADF JSON content
            version: Page version number
            title: Page title
            space_id: Confluence space ID

        Returns:
            Path to created backup file
        """
        # Create page backup directory
        page_backup_dir = self.backup_dir / page_id
        page_backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp filename (include microseconds to avoid collisions)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
        backup_file = page_backup_dir / f"{timestamp}.json"

        # Create backup data
        backup_data = {
            "page_id": page_id,
            "title": title,
            "space_id": space_id,
            "version": version,
            "timestamp": timestamp,
            "adf_content": adf_content
        }

        # Write backup
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        # Cleanup old backups
        self._cleanup_old_backups(page_id)

        return backup_file

    def load_backup(self, page_id: str, timestamp: str | None = None) -> dict:
        """
        Load a backup by timestamp (or latest if timestamp is None).

        Args:
            page_id: Confluence page ID
            timestamp: Backup timestamp (or None for latest)

        Returns:
            Backup data dict
        """
        page_backup_dir = self.backup_dir / page_id

        if not page_backup_dir.exists():
            raise FileNotFoundError(f"No backups found for page {page_id}")

        if timestamp:
            backup_file = page_backup_dir / f"{timestamp}.json"
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup not found: {timestamp}")
        else:
            # Get latest backup
            backups = sorted(page_backup_dir.glob("*.json"), reverse=True)
            if not backups:
                raise FileNotFoundError(f"No backups found for page {page_id}")
            backup_file = backups[0]

        with open(backup_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_backups(self, page_id: str) -> list[dict]:
        """
        List all backups for a page.

        Args:
            page_id: Confluence page ID

        Returns:
            List of backup info dicts (timestamp, title, version)
        """
        page_backup_dir = self.backup_dir / page_id

        if not page_backup_dir.exists():
            return []

        backups = []
        for backup_file in sorted(page_backup_dir.glob("*.json"), reverse=True):
            with open(backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                backups.append({
                    "timestamp": data["timestamp"],
                    "title": data["title"],
                    "version": data["version"]
                })

        return backups

    def _cleanup_old_backups(self, page_id: str) -> None:
        """Remove old backups exceeding retention limit."""
        page_backup_dir = self.backup_dir / page_id
        backups = sorted(page_backup_dir.glob("*.json"), reverse=True)

        # Delete backups exceeding limit
        for backup_file in backups[self.retention_limit:]:
            backup_file.unlink()


class ADFValidator:
    """Validates ADF structure and content."""

    @staticmethod
    def validate_adf(adf: dict) -> list[str]:
        """
        Validate ADF structure.

        Args:
            adf: ADF JSON structure to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not isinstance(adf, dict):
            errors.append("ADF must be a dictionary")
            return errors

        if "type" not in adf:
            errors.append("ADF missing required 'type' field")

        if adf.get("type") != "doc":
            errors.append(f"ADF root type must be 'doc', got '{adf.get('type')}'")

        if "content" not in adf:
            errors.append("ADF missing required 'content' field")
        elif not isinstance(adf.get("content"), list):
            errors.append("ADF 'content' must be a list")

        # Validate text nodes
        errors.extend(ADFValidator._validate_nodes_recursive(adf))

        return errors

    @staticmethod
    def _validate_nodes_recursive(node: Any, path: str = "") -> list[str]:
        """Recursively validate nodes."""
        errors = []

        if not isinstance(node, dict):
            return errors

        node_type = node.get("type")

        # Validate text nodes
        if node_type == "text":
            if "text" not in node:
                errors.append(f"Text node at {path} missing 'text' field")
            elif not isinstance(node.get("text"), str):
                errors.append(f"Text node at {path} 'text' must be string")

        # Validate macro nodes
        if node_type in ADFTextExtractor.MACRO_NODE_TYPES:
            if "attrs" not in node:
                errors.append(f"Macro node at {path} missing 'attrs' field")

        # Recurse into content
        content = node.get("content")
        if isinstance(content, list):
            for i, child in enumerate(content):
                child_path = f"{path}.content[{i}]" if path else f"content[{i}]"
                errors.extend(ADFValidator._validate_nodes_recursive(child, child_path))

        return errors


class MCPJsonDiffRoundtrip:
    """Main controller for MCP + JSON Diff roundtrip editing."""

    def __init__(
        self,
        mcp_client: Any,
        backup_manager: BackupManager | None = None
    ):
        """
        Initialize the roundtrip controller.

        Args:
            mcp_client: MCP client for Confluence operations
            backup_manager: Backup manager (creates default if None)
        """
        self.mcp_client = mcp_client
        self.backup_manager = backup_manager or BackupManager()
        self.validator = ADFValidator()

    def edit_page(
        self,
        cloud_id: str,
        page_id: str,
        edit_instruction: str,
        advanced_mode: bool = False
    ) -> dict:
        """
        Edit a Confluence page using intelligent roundtrip editing.

        Args:
            cloud_id: Atlassian cloud ID
            page_id: Confluence page ID
            edit_instruction: Instruction for Claude on how to edit
            advanced_mode: If True, allow macro body editing with confirmation

        Returns:
            Result dict with status and details
        """
        try:
            # Step 1: Read page via MCP
            print(f"📖 Reading page {page_id}...")
            try:
                page_data = self._read_page(cloud_id, page_id)
            except Exception as e:
                error_msg = str(e).lower()
                if "auth" in error_msg or "unauthorized" in error_msg:
                    print("❌ Authentication failed.")
                    print("💡 Tip: Try re-running /mcp to refresh your credentials.")
                    return {"status": "error", "error": "Authentication failed"}
                elif "not found" in error_msg:
                    print(f"❌ Page {page_id} not found.")
                    print("💡 Tip: Verify the page ID from the Confluence URL.")
                    return {"status": "error", "error": f"Page {page_id} not found"}
                else:
                    raise

            adf_content = page_data["body"]["adf"]
            version = page_data["version"]
            title = page_data["title"]
            space_id = page_data["spaceId"]

            # Step 1.5: Validate ADF
            validation_errors = self.validator.validate_adf(adf_content)
            if validation_errors:
                print("❌ Invalid ADF format:")
                for error in validation_errors:
                    print(f"   - {error}")
                return {
                    "status": "error",
                    "error": "Invalid ADF format",
                    "details": validation_errors
                }

            # Step 2: Detect macros (if advanced mode requested)
            include_macro_bodies = False
            if advanced_mode:
                detector = MacroBodyDetector()
                macros = detector.detect_macros_with_content(adf_content)

                if macros:
                    print(f"\n🔍 Found {len(macros)} macro(s) with editable content:")
                    for macro in macros:
                        print(f"   - {macro.type}: \"{macro.preview}\" ({macro.text_count} text nodes)")

                    # Ask user for confirmation
                    print("\n⚙️  Choose editing mode:")
                    print("[1] Safe Mode (default) - Edit text outside macros")
                    print("[2] Advanced Mode - Edit macro body content too")
                    choice = input("Your choice [1]: ").strip() or "1"

                    include_macro_bodies = (choice == "2")
                    if include_macro_bodies:
                        print("⚠️  Advanced Mode: Macro bodies will be editable. Backup will be created.")
                else:
                    print("✅ No macros with editable content detected. Proceeding normally.")

            # Step 3: Create backup
            print(f"💾 Creating backup...")
            try:
                backup_file = self.backup_manager.create_backup(
                    page_id=page_id,
                    adf_content=adf_content,
                    version=version,
                    title=title,
                    space_id=space_id
                )
                print(f"   Backup saved: {backup_file}")
            except Exception as e:
                print(f"⚠️  Warning: Backup creation failed: {e}")
                print("   Proceeding without backup (not recommended for Advanced Mode)")
                if advanced_mode and include_macro_bodies:
                    print("❌ Cannot proceed with Advanced Mode without backup.")
                    return {"status": "error", "error": "Backup creation failed"}
                backup_file = None

            # Step 4: Extract text nodes
            extractor = ADFTextExtractor(skip_macro_bodies=not include_macro_bodies)
            original_nodes = extractor.extract_text_nodes(adf_content)

            # Step 5: Convert to Markdown
            converter = SimpleMarkdownConverter()
            markdown = converter.convert_to_markdown(adf_content, include_macro_bodies)

            # Step 6: Let Claude edit (simulated for now)
            # TODO: Integrate with Claude API
            print(f"\n🤖 Claude would edit based on: {edit_instruction}")
            print(f"   (Simulated edit - returning original for now)")
            edited_markdown = markdown  # Placeholder

            # Step 7: Compute diff
            differ = TextDiffer()
            changes = differ.compute_changes(original_nodes, edited_markdown)

            if not changes:
                print("ℹ️  No changes detected. Skipping write operation.")
                return {"status": "no_changes", "backup": str(backup_file)}

            print(f"🔄 Found {len(changes)} text change(s)")

            # Step 8: Apply changes to ADF
            patched_adf = extractor.apply_text_changes(adf_content, changes)

            # Step 9: Write back via MCP
            print(f"📝 Writing changes back to Confluence...")
            self._write_page(cloud_id, page_id, patched_adf)

            print("✅ Page updated successfully!")

            return {
                "status": "success",
                "changes": len(changes),
                "backup": str(backup_file)
            }

        except Exception as e:
            print(f"❌ Error during edit: {e}")
            print(f"🔄 Attempting auto-rollback...")

            try:
                backup_data = self.backup_manager.load_backup(page_id)
                self._write_page(cloud_id, page_id, backup_data["adf_content"])
                print("✅ Rollback successful!")
                return {"status": "rolled_back", "error": str(e)}
            except Exception as rollback_error:
                print(f"❌ Rollback failed: {rollback_error}")
                print(f"⚠️  Manual restoration required from: {backup_file}")
                return {
                    "status": "rollback_failed",
                    "error": str(e),
                    "rollback_error": str(rollback_error),
                    "backup": str(backup_file)
                }

    def rollback_page(
        self,
        cloud_id: str,
        page_id: str,
        timestamp: str | None = None
    ) -> dict:
        """
        Manually rollback a page to a previous backup.

        Args:
            cloud_id: Atlassian cloud ID
            page_id: Confluence page ID
            timestamp: Backup timestamp (or None for latest)

        Returns:
            Result dict with status
        """
        try:
            # List backups if no timestamp provided
            if not timestamp:
                backups = self.backup_manager.list_backups(page_id)
                if not backups:
                    return {"status": "error", "message": "No backups found"}

                print("\n📋 Available backups:")
                for i, backup in enumerate(backups, 1):
                    print(f"[{i}] {backup['timestamp']} - {backup['title']} (v{backup['version']})")

                choice = input("\nSelect backup number: ").strip()
                try:
                    idx = int(choice) - 1
                    timestamp = backups[idx]["timestamp"]
                except (ValueError, IndexError):
                    return {"status": "error", "message": "Invalid selection"}

            # Load and restore backup
            print(f"🔄 Loading backup {timestamp}...")
            backup_data = self.backup_manager.load_backup(page_id, timestamp)

            print(f"📝 Restoring page...")
            self._write_page(cloud_id, page_id, backup_data["adf_content"])

            print("✅ Rollback successful!")
            return {"status": "success", "timestamp": timestamp}

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return {"status": "error", "message": str(e)}

    def _read_page(self, cloud_id: str, page_id: str) -> dict:
        """
        Read page via MCP.

        Note: This method expects to be called from Claude Code environment
        where MCP tools are available. When using this module standalone,
        you need to provide a mock mcp_client with get_page method.
        """
        if hasattr(self.mcp_client, 'get_page'):
            # Using mock client (for testing)
            return self.mcp_client.get_page(cloud_id, page_id, content_format="adf")
        else:
            # This will be replaced by actual MCP tool call when invoked by Claude
            raise NotImplementedError(
                "This method must be called from Claude Code environment with MCP tools. "
                "The actual implementation should use: "
                "mcp__plugin_confluence_atlassian__getConfluencePage(cloudId=..., pageId=..., contentFormat='adf')"
            )

    def _write_page(self, cloud_id: str, page_id: str, adf_content: dict) -> None:
        """
        Write page via MCP.

        Note: This method expects to be called from Claude Code environment
        where MCP tools are available. When using this module standalone,
        you need to provide a mock mcp_client with update_page method.
        """
        if hasattr(self.mcp_client, 'update_page'):
            # Using mock client (for testing)
            self.mcp_client.update_page(
                cloud_id=cloud_id,
                page_id=page_id,
                body=json.dumps(adf_content),
                content_format="adf"
            )
        else:
            # This will be replaced by actual MCP tool call when invoked by Claude
            raise NotImplementedError(
                "This method must be called from Claude Code environment with MCP tools. "
                "The actual implementation should use: "
                "mcp__plugin_confluence_atlassian__updateConfluencePage(cloudId=..., pageId=..., body=json.dumps(adf_content), contentFormat='adf')"
            )


if __name__ == "__main__":
    # Example usage (requires actual MCP client)
    print("MCP + JSON Diff Roundtrip (Method 6)")
    print("This module is intended to be imported and used by the Confluence skill.")
