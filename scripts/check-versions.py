#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Check version consistency across plugin files."""

import json
import re
import sys
from pathlib import Path


def extract_skill_version(skill_md_path: Path) -> str | None:
    """Extract version from SKILL.md metadata."""
    if not skill_md_path.exists():
        return None
    content = skill_md_path.read_text()
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    version_match = re.search(r'version:\s*["\']?([0-9.]+)["\']?', parts[1])
    if version_match:
        return version_match.group(1)
    return None


def check_plugin_versions():
    """Check version consistency for all plugins."""
    errors = []
    plugins_dir = Path("plugins")

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        plugin_name = plugin_dir.name
        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not plugin_json_path.exists():
            continue

        with open(plugin_json_path) as f:
            plugin_version = json.load(f).get("version")

        skill_md_path = plugin_dir / "skills" / plugin_name / "SKILL.md"
        skill_version = extract_skill_version(skill_md_path)

        if skill_version and skill_version != plugin_version:
            errors.append(
                f"{plugin_name}: plugin.json={plugin_version} != SKILL.md={skill_version}"
            )

    if errors:
        print("\n❌ Version consistency check failed:\n", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    print("✅ All plugin versions are consistent")


if __name__ == "__main__":
    check_plugin_versions()
