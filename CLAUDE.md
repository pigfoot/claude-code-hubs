<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

## Plugin Version Management

When updating plugin versions, ALWAYS update ALL of these locations:

### For each plugin (e.g., nano-banana):

1. **Plugin metadata** (REQUIRED):
   - `plugins/{plugin-name}/.claude-plugin/plugin.json` - `version` field

2. **Plugin documentation** (REQUIRED):
   - `plugins/{plugin-name}/README.md` - Recent Improvements section
   - `plugins/{plugin-name}/skills/{skill-name}/SKILL.md` - metadata version field

3. **Marketplace version table** (REQUIRED):
   - `/README.md` - "Available Plugins" table (line ~705)

### Checklist Template

When bumping plugin version from X.Y.Z to X.Y.(Z+1):

```bash
# 1. Update plugin.json
plugins/{name}/.claude-plugin/plugin.json → version: "X.Y.(Z+1)"

# 2. Update README.md - Add new section at top
plugins/{name}/README.md → "## ✨ Recent Improvements (vX.Y.(Z+1))"

# 3. Update SKILL.md metadata
plugins/{name}/skills/{name}/SKILL.md → metadata.version: "X.Y.(Z+1)"

# 4. Update marketplace table
README.md → Available Plugins table → update version column

# 5. Verify no missed references
grep -r "X.Y.Z" plugins/{name}/ README.md
```

### Common Mistakes to Avoid

- ❌ Updating plugin.json but forgetting marketplace table in root README.md
- ❌ Updating version number but not adding "Recent Improvements" section
- ❌ Forgetting to update SKILL.md metadata version
- ❌ Leaving old version numbers in documentation examples

### Automation Idea (Future)

Consider adding a version bump script:
```bash
./scripts/bump-plugin-version.sh nano-banana 0.0.8
```