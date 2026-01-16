# Project Context

## Purpose
[Describe your project's purpose and goals]

## Tech Stack
- [List your primary technologies]
- [e.g., TypeScript, React, Node.js]

## Project Conventions

### OpenSpec Change Naming

All change proposals MUST follow the `NNN-feature-name` format where:
- `NNN` is a zero-padded 3-digit sequential number (001, 002, 003, etc.)
- `feature-name` is a kebab-case description of the change

**When creating a new change:**
1. Find the highest existing change number in `openspec/changes/` directory
2. Increment by 1 for the new change
3. Use zero-padded 3-digit format: `001`, `002`, `003`, etc.

**Examples:**
- First change: `001-initial-setup`
- Second change: `002-add-authentication`
- Third change: `003-implement-dashboard`
- If highest is `003`, next change: `004-batch-generation`

**Finding the next number:**
```bash
# List all change directories and find the highest number
ls openspec/changes/ | grep -o '^[0-9]\+' | sort -n | tail -1
# If output is 3, your next change is 004-your-feature-name
```

**Creating new changes:**
```bash
# If the highest existing change is 003
openspec proposal 004-my-new-feature
```

This convention ensures:
- Sequential tracking of all changes
- Easy sorting and reference
- Clear project evolution history

### Skill Development: Progressive Disclosure Strategy

When developing, modifying, or fixing Claude Code skills, follow the **progressive disclosure pattern** to minimize token consumption while maintaining functionality.

**Core Principle:** SKILL.md should contain decision-making information, NOT complete code examples.

#### What Goes in SKILL.md

**✅ Include (Decision-Making Information):**
- Critical rules and warnings (e.g., which API to use, what NOT to do)
- Quick reference tables (comparisons, options)
- Decision trees and selection logic
- **References to detailed documentation** (e.g., "See `references/api-guide.md`")
- Essential code snippets for decision points (5-15 lines max)

**❌ Exclude (Move to references/):**
- Complete code examples (heredocs, full scripts)
- Detailed workflows (multi-step processes)
- Long lists of options or patterns
- Brand guidelines and style specifications
- Extensive troubleshooting guides

#### What Goes in references/

Create focused reference documents for detailed content:
- `references/api-guide.md` - Complete API usage examples with code
- `references/workflow.md` - Step-by-step processes
- `references/patterns.md` - Comprehensive pattern libraries
- `references/styles.md` - Style guides and specifications
- `references/troubleshooting.md` - Debugging and error handling

#### Critical: Enable Claude to Find References

**❌ BAD - Causes Claude to Guess:**
```markdown
<!-- SKILL.md without references -->
Use the Python API to generate images.
```
Result: Claude will guess the API, usually incorrectly.

**✅ GOOD - Explicit Reference:**
```markdown
<!-- SKILL.md with clear reference -->
Use the Python API to generate images. For complete code examples, see `references/api-guide.md`.
```
Result: Claude will Read the reference file and use correct API.

#### Reference nano-banana Skill

See `/plugins/nano-banana/skills/nano-banana/SKILL.md` for a production example:
- **SKILL.md**: 387 lines (critical rules, quick reference, pointers to references/)
- **references/gemini-api.md**: Complete Gemini API code examples
- **references/imagen-api.md**: Complete Imagen API code examples
- **references/guide.md**: 16+ prompting techniques
- **references/slide-deck-styles.md**: Multi-slide generation workflows

**Key pattern in nano-banana:**
```markdown
### Complete Code Examples

For full working examples, see:
- **Gemini API:** `references/gemini-api.md`
- **Imagen API:** `references/imagen-api.md`
```

#### Benefits

1. **Token Efficiency**: Load only decision-making info by default
2. **Functionality**: Claude can Read references/ when needed for complete code
3. **Maintainability**: Update detailed examples without bloating SKILL.md
4. **Accuracy**: Reduces guessing by providing explicit paths to correct implementations

#### Target Metrics

- **SKILL.md**: <500 lines (aim for 350-400)
- **Total references/**: No limit (typically 50-200 lines per file)
- **References per skill**: 3-6 focused documents

### Code Style
[Describe your code style preferences, formatting rules, and naming conventions]

### Architecture Patterns
[Document your architectural decisions and patterns]

### Testing Strategy
[Explain your testing approach and requirements]

### Git Workflow
[Describe your branching strategy and commit conventions]

## Domain Context
[Add domain-specific knowledge that AI assistants need to understand]

## Important Constraints
[List any technical, business, or regulatory constraints]

## External Dependencies
[Document key external services, APIs, or systems]
