#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""Validate SKILL.md frontmatter format."""

import sys
from pathlib import Path
import yaml


def validate_skill_file(skill_path: Path) -> list[str]:
    """Validate a single SKILL.md file."""
    errors = []
    content = skill_path.read_text()

    if not content.startswith("---"):
        return ["Missing YAML frontmatter"]

    parts = content.split("---", 2)
    if len(parts) < 3:
        return ["Invalid frontmatter format"]

    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]

    if "name" not in metadata:
        errors.append("Missing 'name' field")
    if "description" not in metadata:
        errors.append("Missing 'description' field")

    return errors


def validate_all_skills():
    """Validate all SKILL.md files."""
    plugins_dir = Path("plugins")
    all_errors = {}

    for skill_path in sorted(plugins_dir.rglob("*/skills/*/SKILL.md")):
        try:
            relative_path = skill_path.relative_to(plugins_dir.parent)
        except ValueError:
            relative_path = skill_path
        errors = validate_skill_file(skill_path)
        if errors:
            all_errors[str(relative_path)] = errors

    if all_errors:
        print("❌ SKILL.md validation failed:\n", file=sys.stderr)
        for file_path, errors in all_errors.items():
            print(f"\n{file_path}:", file=sys.stderr)
            for error in errors:
                print(f"  • {error}", file=sys.stderr)
        sys.exit(1)

    print("✅ All SKILL.md files are valid")


if __name__ == "__main__":
    validate_all_skills()
