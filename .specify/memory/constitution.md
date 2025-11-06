<!--
Sync Impact Report:
- Version: 0.0.0 → 1.0.0
- Initial constitution creation for Claude Code Marketplace project
- Principles defined:
  1. Plugin-First Architecture
  2. Standards-Based Resources
  3. Documentation-Driven Development
  4. Test-First (NON-NEGOTIABLE)
  5. Quality & Simplicity
- Templates status:
  ✅ plan-template.md - reviewed, aligned with constitution
  ✅ spec-template.md - reviewed, aligned with constitution
  ✅ tasks-template.md - reviewed, aligned with constitution
- Follow-up: README.md and CLAUDE.md to be created
-->

# Claude Code Marketplace Constitution

## Core Principles

### I. Plugin-First Architecture

Every contribution to this marketplace MUST be a standalone, reusable resource:

- **Plugins**: Self-contained units with clear metadata (`plugin.json`)
- **Skills**: Documented workflows in individual skill directories with SKILL.md
- **Config Templates**: Reusable configuration files (.CLAUDE.md, settings templates)
- Clear purpose required - no organizational-only resources
- Each resource must be independently installable and testable

**Rationale**: A plugin-first architecture ensures users can pick and choose only the functionality they need, reducing bloat and maintaining clarity of purpose. Self-contained resources are easier to maintain, test, and distribute.

### II. Standards-Based Resources

All marketplace resources MUST follow established standards:

- **Plugin metadata**: Valid JSON conforming to Claude Code plugin schema
- **Skills**: YAML frontmatter + Markdown format with name, description, version
- **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Naming**: Lowercase with hyphens (kebab-case) for directories and plugins
- **Documentation**: English for all docs, code, comments, README files
- **Licensing**: Clear license declaration in each plugin

**Rationale**: Standards ensure interoperability across different Claude Code installations and make it easy for users to understand and integrate resources. Consistent naming and documentation patterns reduce cognitive load.

### III. Documentation-Driven Development

Documentation is first-class and MUST precede implementation:

- Every plugin requires README.md with: purpose, installation, usage, examples
- Every skill requires SKILL.md with: when to use, process, examples, troubleshooting
- Config templates require inline comments explaining each section
- Breaking changes require migration guides
- All documentation in English regardless of author's language

**Rationale**: Users discover and evaluate resources through documentation first. Poor documentation means the resource won't be adopted, regardless of technical quality. Documentation-first forces clarity of thought before implementation.

### IV. Test-First (NON-NEGOTIABLE)

All executable code MUST follow Test-Driven Development:

- Write test FIRST → Ensure it FAILS → Then implement
- RED-GREEN-REFACTOR cycle strictly enforced
- Integration tests for plugin contracts and interactions
- Skills must include example sessions demonstrating usage
- No commits with failing tests

**Rationale**: Marketplace resources are used by many users in diverse environments. Bugs affect everyone. TDD ensures code actually works before distribution and prevents regressions.

### V. Quality & Simplicity

Resources MUST be simple, focused, and high-quality:

- One plugin = one clear purpose (no "Swiss Army knife" plugins)
- Prefer boring, proven approaches over clever solutions
- No unnecessary dependencies - minimize external requirements
- Skills should be <500 lines; split if longer
- Config templates should be <300 lines with clear sections
- Code must be readable without deep domain knowledge

**Rationale**: Marketplace resources are maintained by contributors and used by diverse users. Simplicity ensures long-term maintainability. Focused scope prevents feature creep and keeps resources understandable.

## Distribution & Marketplace Standards

### Marketplace Structure

The marketplace MUST maintain this structure:

```
.claude-plugin/
  marketplace.json          # Marketplace metadata and plugin registry

plugins/
  {plugin-name}/
    .claude-plugin/
      plugin.json           # Plugin metadata
    skills/{skill-name}/
      SKILL.md              # Skill documentation
    README.md               # Plugin documentation
    LICENSE                 # License file

templates/
  .CLAUDE.md                # Global configuration template
  .clauderc                 # CLI configuration template
  [other-templates]         # Additional reusable configs
```

### Plugin Requirements

Every plugin MUST include:

- Valid `plugin.json` with: name, version, description, author
- `README.md` with installation and usage instructions
- `LICENSE` file (prefer MIT, Apache-2.0, or BSD-3-Clause)
- Version number following semantic versioning
- Clear description of when and how to use the plugin

### Skill Requirements

Every skill MUST include:

- YAML frontmatter: name, description, version, allowed-tools
- "When to Use" section with specific trigger conditions
- "Process" section with step-by-step workflow
- "Examples" section with real usage scenarios
- "Critical Rules" section with NEVER/ALWAYS guidelines

### Configuration Templates

Configuration templates MUST:

- Include comprehensive inline comments
- Provide sensible defaults
- Document all configuration options
- Include examples for common use cases
- Specify when to override defaults

## Development Workflow

### Before Adding New Resources

1. **Check existing resources**: Avoid duplication
2. **Define clear purpose**: One sentence description
3. **Verify standards compliance**: Naming, structure, metadata
4. **Plan documentation**: README/SKILL.md outline before code

### Resource Development Process

1. **Document first**: Write README.md or SKILL.md
2. **Test scenarios**: Define test cases (for code resources)
3. **Implement**: Follow TDD for any executable code
4. **Validate**: Test installation and usage from scratch
5. **Review**: Ensure quality and simplicity standards

### Quality Gates

Before merging any resource:

- ✅ Documentation complete and clear
- ✅ Tests written and passing (if applicable)
- ✅ No security vulnerabilities
- ✅ Follows naming conventions
- ✅ Valid metadata (plugin.json, SKILL.md frontmatter)
- ✅ License declared
- ✅ Installation tested from clean environment

## Governance

### Constitutional Authority

This constitution supersedes all other project practices. All contributions, reviews, and marketplace additions must verify compliance with these principles.

### Amendment Process

Constitution changes require:

1. Documented rationale for the change
2. Review of impact on existing resources
3. Migration plan for affected resources
4. Version bump following semantic versioning rules

### Complexity Justification

Any deviation from simplicity principles (new dependencies, complex architectures, multi-purpose plugins) MUST be justified:

- Document the specific problem requiring complexity
- Explain why simpler alternatives were rejected
- Get approval before implementation

### Compliance Reviews

All pull requests and resource additions must:

- Pass automated validation (linting, JSON schema validation)
- Include peer review verifying constitutional compliance
- Demonstrate working installation and usage
- Include test results (for code resources)

### Runtime Development Guidance

For day-to-day development guidance beyond constitutional principles, contributors should reference:

- `.CLAUDE.md` - Project-specific development guidelines
- `README.md` - Project overview and contribution guidelines
- Individual plugin README files for plugin-specific conventions

**Version**: 1.0.0 | **Ratified**: 2025-11-06 | **Last Amended**: 2025-11-06
