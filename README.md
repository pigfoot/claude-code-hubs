# Claude Code Marketplace

A curated collection of high-quality plugins, skills, and configuration templates for [Claude Code](https://docs.claude.com/en/docs/claude-code).

## What's Inside

This marketplace provides three types of resources:

### 🔌 Plugins

Standalone extensions that add new capabilities to Claude Code:

- **[git-commit](./plugins/git-commit/)** - Smart commit message generation with conventional commits, emoji prefixes, and GPG signing support
- **[context7](./plugins/context7/)** - Access up-to-date documentation and code examples for any library or framework

### 🎯 Skills

Reusable workflow patterns and automation:

- Located within each plugin's `skills/` directory
- Follow standardized format with clear triggers and processes
- Include practical examples and troubleshooting guides

### ⚙️ Configuration Templates

Ready-to-use configuration files for Claude Code:

- **[.CLAUDE.md](./.CLAUDE.md)** - Comprehensive development guidelines template
- Includes language detection, workflow patterns, and best practices
- Customizable for project-specific needs

## Quick Start

### Installing Individual Plugins

1. Browse the `plugins/` directory to find a plugin you need
2. Follow the installation instructions in each plugin's README.md
3. Configure as needed per plugin documentation

### Using Configuration Templates

```bash
# Copy the template to your project
cp .CLAUDE.md /path/to/your/project/CLAUDE.md

# Or use it globally
cp .CLAUDE.md ~/.claude/CLAUDE.md

# Customize for your project's needs
```

### Using Skills

Skills are automatically available when you install their parent plugin. Refer to each skill's SKILL.md for usage instructions.

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [git-commit](./plugins/git-commit/) | Conventional commits with emoji and GPG signing | 0.0.1 |
| [context7](./plugins/context7/) | Library documentation via Context7 MCP server | 0.0.1 |

## Project Structure

```
claude-code-hubs/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace registry
├── plugins/
│   ├── git-commit/           # Git commit automation plugin
│   └── context7/             # Documentation plugin
├── .CLAUDE.md                # Global configuration template
├── .specify/                 # Spec-kit templates and memory
└── README.md                 # This file
```

## Contributing

We welcome high-quality contributions! Before submitting:

### 1. Read the Constitution

Review [.specify/memory/constitution.md](./.specify/memory/constitution.md) for our core principles:

- Plugin-First Architecture
- Standards-Based Resources
- Documentation-Driven Development
- Test-First (NON-NEGOTIABLE)
- Quality & Simplicity

### 2. Follow Development Guidelines

Check [CLAUDE.md](./CLAUDE.md) for project-specific development patterns.

### 3. Quality Standards

Your contribution must include:

- ✅ Complete documentation (README.md for plugins, SKILL.md for skills)
- ✅ Valid metadata (plugin.json, YAML frontmatter)
- ✅ Tests for executable code
- ✅ LICENSE file (MIT, Apache-2.0, or BSD-3-Clause preferred)
- ✅ Semantic versioning
- ✅ English documentation, code, and comments

### 4. Submission Process

1. Fork this repository
2. Create a feature branch
3. Add your plugin/skill/template following existing patterns
4. Test installation from scratch
5. Submit a pull request with clear description

## Plugin Development Guide

### Creating a New Plugin

```bash
# Create plugin directory structure
mkdir -p plugins/my-plugin/.claude-plugin
mkdir -p plugins/my-plugin/skills/my-skill

# Create required files
touch plugins/my-plugin/.claude-plugin/plugin.json
touch plugins/my-plugin/README.md
touch plugins/my-plugin/LICENSE
touch plugins/my-plugin/skills/my-skill/SKILL.md
```

### Plugin Metadata (plugin.json)

```json
{
  "name": "my-plugin",
  "description": "Brief description of what this plugin does",
  "version": "0.0.1",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

### Skill Format (SKILL.md)

```markdown
---
name: my-skill
description: Brief description
version: 1.0.0
allowed-tools: "Bash(git *)"
---

# Skill Name

## When to Use
[Trigger conditions]

## Process
[Step-by-step workflow]

## Examples
[Real usage scenarios]

## Critical Rules
[NEVER/ALWAYS guidelines]
```

## Skill Development Guide

### Skill Best Practices

1. **Clear Triggers**: Define specific conditions when the skill should activate
2. **Step-by-Step**: Break down complex workflows into numbered steps
3. **Examples First**: Show real-world usage before explaining theory
4. **Critical Rules**: Use NEVER/ALWAYS format for important guidelines
5. **Keep It Focused**: One skill = one workflow (split if >500 lines)

### Testing Skills

Skills should include example sessions demonstrating:

- Successful execution flow
- Error handling
- Edge cases
- Integration with other tools

## Configuration Template Guide

### Creating Config Templates

When adding new configuration templates:

1. **Comprehensive Comments**: Explain every section and option
2. **Sensible Defaults**: Provide working defaults out of the box
3. **Examples Included**: Show common customization patterns
4. **Override Guidance**: Explain when and why to change defaults
5. **Size Limit**: Keep templates under 300 lines

### Template Structure

```markdown
# Template Name

## Section 1: Core Configuration
[Settings with inline comments]

## Section 2: Optional Customizations
[Settings with default values and examples]

## Section 3: Advanced Options
[Power-user settings with warnings]
```

## Marketplace Standards

### Naming Conventions

- **Plugins**: `kebab-case` (e.g., `git-commit`, `context7`)
- **Skills**: `kebab-case` matching their function
- **Files**: Follow Claude Code conventions
  - `plugin.json` for plugin metadata
  - `SKILL.md` for skill documentation
  - `README.md` for plugin documentation

### Versioning

All resources follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes or incompatible updates
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, documentation updates

### Documentation Requirements

Every resource must have:

- **Purpose**: One-sentence description of what it does
- **Installation**: Step-by-step setup instructions
- **Usage**: Common usage patterns with examples
- **Configuration**: Available options and their effects
- **Troubleshooting**: Common issues and solutions

## License

This project is licensed under the MIT License - see individual plugin LICENSE files for specific terms.

## Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Ask questions or share ideas in GitHub Discussions
- **Documentation**: See [Claude Code docs](https://docs.claude.com/en/docs/claude-code)

## Acknowledgments

- **Maintainer**: Chih-Chia Chen (pigfoot)
- **Contributors**: See individual plugin author information
- **Built for**: [Claude Code](https://docs.claude.com/en/docs/claude-code) by Anthropic

## Related Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Spec-Kit Templates](./.specify/templates/)
- [Plugin Development Guide](https://docs.claude.com/en/docs/claude-code/plugins)

---

**Version**: 0.0.1 | **Last Updated**: 2025-11-06
