# Tool Dependencies

Complete list of tools used by pre-commit hooks, how they're executed, and why these approaches were chosen.

## Tool Execution Strategy

### Python Tools (via `uvx --managed-python`)

**Why this approach:**

- ✅ **No system Python dependency** - Managed Python 3.14+ automatically downloaded
- ✅ **No virtual environments** - Each tool runs in isolated environment
- ✅ **Fast execution** - Rust-based uv is 10-100x faster than pip
- ✅ **Reproducible** - Same Python version across all machines

**Usage pattern:**

```bash
uvx --managed-python <tool-name> <args>
```

**Tools:**

| Tool | Version | Purpose |
|------|---------|---------|
| pre-commit | (latest) | Hook framework orchestration |
| ruff | (latest) | Python linter + formatter (replaces black, isort, flake8, pylint) |
| yamllint | (latest) | YAML linting |
| detect-secrets | (latest) | Secret scanning |

### JavaScript Tools (via `bunx`)

**Why this approach:**

- ✅ **No npm/node_modules** - Bun manages packages automatically
- ✅ **3-10x faster than npm** - Bun runtime is significantly faster
- ✅ **Auto-caching** - Dependencies cached globally
- ✅ **Zero configuration** - Just works

**Usage pattern:**

```bash
bunx <package-name> <args>
```

**Tools:**

| Tool | Version | Purpose |
|------|---------|---------|
| markdownlint-cli | (latest) | Markdown linting and auto-fixing |

### Project-specific Scripts (via `uv run --managed-python`)

**Why this approach:**

- ✅ **PEP 723 inline dependencies** - Dependencies declared in script headers
- ✅ **No separate requirements.txt** - Self-contained scripts
- ✅ **Managed Python** - Consistent Python version

**Usage pattern:**

```bash
uv run --managed-python scripts/<script-name>.py
```

**Scripts:**

| Script | Dependencies | Purpose |
|--------|--------------|---------|
| check-versions.py | None | Verify plugin version consistency across plugin.json, SKILL.md, README.md |
| validate-skill.py | pyyaml | Validate SKILL.md YAML frontmatter format |

### System Tools (direct execution)

**Tools:**

| Tool | Source | Purpose |
|------|--------|---------|
| jq | System | JSON manipulation in bash hooks |

## Detailed Tool Information

### ruff

**Website:** <https://github.com/astral-sh/ruff>

**What it does:**

- Python linter (replaces flake8, pylint, pycodestyle, pyflakes)
- Python formatter (replaces black, isort)
- Written in Rust - 10-100x faster than alternatives

**Configuration:**

- File: `pyproject.toml` or `ruff.toml`
- Used in: `ruff-check`, `ruff-format` hooks

**Example config:**

```toml
[tool.ruff]
line-length = 120
target-version = "py314"
```

### yamllint

**Website:** <https://github.com/adrienverge/yamllint>

**What it does:**

- Validates YAML syntax
- Enforces formatting rules (indentation, line length, trailing spaces)

**Configuration:**

- File: `.yamllint.yaml`
- Current rules: 120 char line length, 2-space indent, allow yes/no/on/off

**Key settings:**

```yaml
rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no', 'on', 'off']
```

### markdownlint-cli

**Website:** <https://github.com/igorshubovych/markdownlint-cli>

**What it does:**

- Markdown linting and formatting
- Enforces consistent Markdown style
- Auto-fixes many issues

**Configuration:**

- File: `.markdownlint.json`
- Ignore file: `.markdownlintignore`
- Current rules: 120 char line length, ATX headings, no trailing punctuation

**Key settings:**

```json
{
  "MD013": { "line_length": 120, "code_blocks": false, "tables": false },
  "MD033": { "allowed_elements": ["name", "artifact-id", ...] },
  "MD040": false,
  "MD060": false
}
```

### detect-secrets

**Website:** <https://github.com/Yelp/detect-secrets>

**What it does:**

- Scans for hardcoded secrets (API keys, tokens, passwords)
- Uses baseline file to track known false positives
- Prevents accidental credential commits

**Configuration:**

- File: `.secrets.baseline`
- Plugins: AWS, GitHub, Private Keys, Base64/Hex entropy, etc.

**Update baseline:**

```bash
# Scan and update baseline
uvx --managed-python detect-secrets scan --baseline .secrets.baseline

# Add inline exceptions
api_key = "fake-key-for-testing"  # pragma: allowlist secret
```

### conventional-pre-commit

**Website:** <https://github.com/compilerla/conventional-pre-commit>

**What it does:**

- Validates commit messages follow Conventional Commits format
- Enforces type prefix (feat, fix, docs, etc.)

**Allowed types:**

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Tests
- `build` - Build system
- `ci` - CI/CD
- `chore` - Maintenance
- `revert` - Revert changes

**Example messages:**

```bash
feat(nano-banana): add temperature parameter
fix: resolve URL parsing bug
docs: update pre-commit hooks guide
```

## Project-specific Validators

### check-versions.py

**Purpose:** Ensure version consistency across plugin files

**Validates:**

- `plugins/{name}/.claude-plugin/plugin.json` - `version` field
- `plugins/{name}/skills/{name}/SKILL.md` - `version` in YAML frontmatter
- `README.md` - Version in plugin table

**Example error:**

```
nano-banana: plugin.json=0.0.9 != SKILL.md=0.0.8
```

### validate-skill.py

**Purpose:** Validate SKILL.md YAML frontmatter format

**Validates:**

- YAML frontmatter exists and is valid
- Required fields: `name`, `description`
- Valid YAML syntax

**Example error:**

```
plugins/nano-banana/skills/nano-banana/SKILL.md:
  • Missing 'name' field
  • Invalid YAML: unexpected character
```

## Performance

### First Run

- **Duration:** 10-30 seconds
- **Why:** Tools downloaded and cached by uvx/bunx

### Subsequent Runs

- **Duration:** 1-5 seconds
- **Why:** Tools cached, only staged files checked

### Cache Locations

- **uv cache:** `~/.cache/uv/`
- **bun cache:** `~/.bun/install/cache/`
- **pre-commit cache:** `~/.cache/pre-commit/`

### Clear Cache

```bash
# Clear all caches
rm -rf ~/.cache/uv ~/.bun/install/cache ~/.cache/pre-commit

# Clear specific tool
uvx --managed-python --refresh <tool>
```

## Customization

### Modify Rules

Edit configuration files:

- `.yamllint.yaml` - YAML rules
- `.markdownlint.json` - Markdown rules
- `.pre-commit-config.yaml` - Hook settings

### Exclude Files

Add patterns to exclude specific files:

```yaml
# In .pre-commit-config.yaml
- id: markdownlint
  exclude: 'CHANGELOG.md|.claude/.*'
```

Or use ignore files:

- `.markdownlintignore` - For markdownlint
- `.gitignore` - Generally respected by most tools

### Add New Hooks

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: my-custom-hook
      name: My Custom Hook
      entry: bunx my-tool
      language: system
      types: [python]
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Pre-commit Checks

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'

      - name: Set up Bun
        uses: oven-sh/setup-bun@v2

      - name: Set up uv
        uses: astral-sh/setup-uv@v5

      - name: Run pre-commit
        run: uvx --managed-python pre-commit run --all-files
```

## Comparison with Traditional Approaches

### Old Approach (pip + venv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install pre-commit black flake8 yamllint
pre-commit install
```

**Issues:**

- ❌ Requires system Python
- ❌ Virtual environment management overhead
- ❌ Slow pip installs
- ❌ Version conflicts between tools

### New Approach (uv + bun)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://bun.sh/install | bash
uvx --managed-python pre-commit install
```

**Benefits:**

- ✅ No system Python dependency
- ✅ No virtual environments
- ✅ Fast Rust-based tooling
- ✅ Automatic version management

## Maintenance

### Update Hook Versions

```bash
# Update all hooks to latest versions
uvx --managed-python pre-commit autoupdate

# Review changes
git diff .pre-commit-config.yaml

# Test before committing
uvx --managed-python pre-commit run --all-files
```

### Update Secrets Baseline

When adding new test data or examples:

```bash
# Scan and update baseline
uvx --managed-python detect-secrets scan --baseline .secrets.baseline

# Review changes
git diff .secrets.baseline

# Commit updated baseline
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

## Support

- **Issues:** Report problems via GitHub Issues
- **pre-commit docs:** <https://pre-commit.com/>
- **uv docs:** <https://docs.astral.sh/uv/>
- **bun docs:** <https://bun.sh/docs>
