#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Helper functions for Method 6 roundtrip editing in Claude Code environment.

This module is designed to be used by Claude in conversation, not as a standalone script.
Claude will call MCP tools directly and use these classes for processing.

Usage:
    uv run roundtrip_helper.py  # Will show usage message
"""

import sys
from pathlib import Path

# Import core classes
from mcp_json_diff_roundtrip import (
    ADFTextExtractor,
    SimpleMarkdownConverter,
    TextDiffer,
    BackupManager,
    MacroBodyDetector,
    ADFValidator,
    TextChange
)


def process_confluence_edit(
    page_adf: dict,
    page_id: str,
    page_title: str,
    page_version: int,
    space_id: str,
    edit_instruction: str,
    advanced_mode: bool = False
) -> dict:
    """
    Process a Confluence page edit using Method 6.

    This is a helper function for Claude to use in conversation.
    Claude should:
    1. Call MCP to get page (ADF format)
    2. Call this function to process the edit
    3. Call MCP to write back the result

    Args:
        page_adf: ADF content from getConfluencePage
        page_id: Confluence page ID
        page_title: Page title
        page_version: Current version number
        space_id: Space ID
        edit_instruction: What to edit (for Claude to understand)
        advanced_mode: Whether to allow macro body editing

    Returns:
        dict with:
        - status: "success", "no_changes", or "error"
        - patched_adf: Modified ADF (if success)
        - changes: List of changes made
        - markdown: Markdown for Claude to edit
        - backup_file: Path to backup
        - macros: List of detected macros (if any)
    """
    result = {
        "status": "pending",
        "page_id": page_id,
        "page_title": page_title
    }

    # Step 1: Validate ADF
    validator = ADFValidator()
    errors = validator.validate_adf(page_adf)
    if errors:
        result["status"] = "error"
        result["error"] = "Invalid ADF format"
        result["validation_errors"] = errors
        return result

    # Step 2: Detect macros
    detector = MacroBodyDetector()
    macros = detector.detect_macros_with_content(page_adf)
    result["macros"] = [
        {
            "type": m.type,
            "preview": m.preview,
            "text_count": m.text_count
        }
        for m in macros
    ]

    # Step 3: Create backup
    backup_manager = BackupManager()
    try:
        backup_file = backup_manager.create_backup(
            page_id=page_id,
            adf_content=page_adf,
            version=page_version,
            title=page_title,
            space_id=space_id
        )
        result["backup_file"] = str(backup_file)
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Backup failed: {e}"
        return result

    # Step 4: Determine mode
    include_macro_bodies = False
    if advanced_mode and macros:
        # User should be prompted before this function is called
        include_macro_bodies = True

    # Step 5: Extract text and convert to Markdown
    extractor = ADFTextExtractor(skip_macro_bodies=not include_macro_bodies)
    original_nodes = extractor.extract_text_nodes(page_adf)

    converter = SimpleMarkdownConverter()
    markdown = converter.convert_to_markdown(page_adf, include_macro_bodies)

    result["markdown"] = markdown
    result["original_text_nodes"] = len(original_nodes)
    result["mode"] = "advanced" if include_macro_bodies else "safe"

    # Step 6: Return for Claude to edit
    # Claude will edit the markdown and call compute_changes_and_patch
    result["status"] = "ready_for_edit"
    result["edit_instruction"] = edit_instruction

    return result


def compute_changes_and_patch(
    original_adf: dict,
    original_nodes_data: list,  # Can be reconstructed if needed
    edited_markdown: str,
    include_macro_bodies: bool = False
) -> dict:
    """
    Compute changes between original and edited markdown, then patch ADF.

    This is called after Claude has edited the markdown.

    Args:
        original_adf: Original ADF structure
        original_nodes_data: Original text nodes (from process_confluence_edit)
        edited_markdown: Markdown edited by Claude
        include_macro_bodies: Whether macro bodies were included

    Returns:
        dict with:
        - status: "success" or "no_changes"
        - patched_adf: Modified ADF (if changes found)
        - changes: List of changes
        - change_count: Number of changes
    """
    # Re-extract text nodes (to ensure consistency)
    extractor = ADFTextExtractor(skip_macro_bodies=not include_macro_bodies)
    original_nodes = extractor.extract_text_nodes(original_adf)

    # Compute diff
    differ = TextDiffer()
    changes = differ.compute_changes(original_nodes, edited_markdown)

    if not changes:
        return {
            "status": "no_changes",
            "message": "No changes detected between original and edited content"
        }

    # Apply changes
    patched_adf = extractor.apply_text_changes(original_adf, changes)

    return {
        "status": "success",
        "patched_adf": patched_adf,
        "changes": [
            {
                "path": c.path,
                "old_text": c.old_text,
                "new_text": c.new_text
            }
            for c in changes
        ],
        "change_count": len(changes)
    }


def list_backups_for_page(page_id: str) -> list[dict]:
    """
    List available backups for a page.

    Args:
        page_id: Confluence page ID

    Returns:
        List of backup info dicts
    """
    backup_manager = BackupManager()
    return backup_manager.list_backups(page_id)


def load_backup_for_rollback(page_id: str, timestamp: str | None = None) -> dict:
    """
    Load a backup for rollback.

    Args:
        page_id: Confluence page ID
        timestamp: Backup timestamp (or None for latest)

    Returns:
        Backup data with adf_content
    """
    backup_manager = BackupManager()
    return backup_manager.load_backup(page_id, timestamp)


if __name__ == "__main__":
    print("This module is designed to be used by Claude in conversation.")
    print("Use process_confluence_edit() to start editing a page.")
