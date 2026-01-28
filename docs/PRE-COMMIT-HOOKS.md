# Pre-commit Hooks Guide

Automated quality checks that run before each commit to ensure code quality, security, and consistency.

## Quick Start

### Prerequisites

Install required tools:

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install bun (JavaScript runtime)
curl -fsSL https://bun.sh/install | bash

# Verify installations
uv --version
bun --version
```

### Install Pre-commit

```bash
# Install pre-commit framework
uvx --managed-python pre-commit install

# Install commit-msg hook for conventional commits
uvx --managed-python pre-commit install --hook-type commit-msg

# Verify installation
uvx --managed-python pre-commit --version
```

### Run Hooks

```bash
# Run all hooks on staged files
uvx --managed-python pre-commit run

# Run all hooks on all files
uvx --managed-python pre-commit run --all-files

# Run specific hook
uvx --managed-python pre-commit run ruff-check
uvx --managed-python pre-commit run markdownlint

# Skip hooks (NOT recommended)
git commit --no-verify -m "emergency fix"
```

## Hook Phases

### Phase 1: General File Checks

Fast checks with no external dependencies:

- **trailing-whitespace** - Remove trailing spaces
- **end-of-file-fixer** - Ensure files end with newline
- **check-merge-conflict** - Detect merge conflict markers
- **check-added-large-files** - Block files >500KB
- **check-json** - Validate JSON syntax
- **check-yaml** - Validate YAML syntax
- **mixed-line-ending** - Enforce LF line endings

### Phase 2: Secrets Protection

**CRITICAL** - Prevents committing sensitive data:

- **block-env-files** - Block `.env` files (allows `.env.example`, `.env.template`)
- **detect-secrets** - Scan for API keys, tokens, passwords using baseline

**Baseline file:** `.secrets.baseline`

Update baseline when adding legitimate secrets (test data, examples):

```bash
uvx --managed-python detect-secrets scan --baseline .secrets.baseline
```

### Phase 3: Language-specific Linting

#### Python (via `uvx --managed-python`)

- **ruff-check** - Fast linter (replaces flake8, pylint)
- **ruff-format** - Fast formatter (replaces black, isort)

Configuration: `pyproject.toml` or `ruff.toml`

#### YAML (via `uvx --managed-python`)

- **yamllint** - YAML linter with custom rules

Configuration: `.yamllint.yaml`

#### Markdown (via `bunx`)

- **markdownlint** - Markdown linter and formatter

Configuration: `.markdownlint.json`, `.markdownlintignore`

### Phase 4: Project-specific Validations

Custom validators for this project:

- **check-plugin-json-syntax** - Validate all `plugin.json` files
- **check-plugin-required-fields** - Ensure required fields (`name`, `version`, `description`, `skills`)
- **check-version-consistency** - Verify version matches across `plugin.json`, `SKILL.md`, `README.md`
- **validate-skill-metadata** - Check SKILL.md YAML frontmatter format

Scripts: `scripts/check-versions.py`, `scripts/validate-skill.py`

### Phase 5: Commit Message Validation

- **conventional-pre-commit** - Enforce conventional commit format

**Allowed types:**
`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Format:** `<type>(<scope>): <description>`

Examples:

```bash
feat: add temperature parameter to nano-banana
fix(confluence): resolve URL parsing bug
docs: update pre-commit hooks guide
```

## Troubleshooting

### Hook Fails with "command not found"

Ensure `uv` and `bun` are in PATH:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"  # uv
export PATH="$HOME/.bun/bin:$PATH"    # bun

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

### Secrets Detected (False Positive)

If detect-secrets flags legitimate test data:

```bash
# Update baseline to include the file
uvx --managed-python detect-secrets scan --baseline .secrets.baseline

# Or add inline comment in code
password = "fake-password-for-testing"  # pragma: allowlist secret
```

### Slow Hook Execution

First run is slower due to tool downloads. Subsequent runs use cache:

- `uvx` cache: `~/.cache/uv/`
- `bunx` cache: `~/.bun/install/cache/`

### Skip Specific Hook

```bash
# Skip one hook
SKIP=ruff-check git commit -m "message"

# Skip multiple hooks
SKIP=ruff-check,markdownlint git commit -m "message"
```

### Update Hooks

```bash
# Update to latest hook versions
uvx --managed-python pre-commit autoupdate

# Clean and reinstall
uvx --managed-python pre-commit clean
uvx --managed-python pre-commit install
```

## Configuration Files

| File | Purpose | Tool |
|------|---------|------|
| `.pre-commit-config.yaml` | Main pre-commit configuration | pre-commit |
| `.yamllint.yaml` | YAML linting rules | yamllint |
| `.markdownlint.json` | Markdown linting rules | markdownlint |
| `.markdownlintignore` | Files to exclude from Markdown linting | markdownlint |
| `.secrets.baseline` | Known secrets baseline | detect-secrets |

## Best Practices

### For Contributors

1. **Install hooks immediately** after cloning:

   ```bash
   uvx --managed-python pre-commit install
   uvx --managed-python pre-commit install --hook-type commit-msg
   ```

2. **Run before committing** to catch issues early:

   ```bash
   uvx --managed-python pre-commit run
   ```

3. **Don't bypass hooks** unless absolutely necessary

4. **Update baseline** when adding test fixtures with mock credentials

### For Maintainers

1. **Keep hooks updated**:

   ```bash
   uvx --managed-python pre-commit autoupdate
   ```

2. **Test hook changes** before committing:

   ```bash
   uvx --managed-python pre-commit run --all-files
   ```

3. **Document exceptions** in `.markdownlintignore`, `.yamllint.yaml`, etc.

## CI/CD Integration

Add to GitHub Actions:

```yaml
name: Pre-commit
on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: oven-sh/setup-bun@v2
      - uses: astral-sh/setup-uv@v5
      - run: uvx --managed-python pre-commit run --all-files
```

## Performance Tips

- **Parallel execution**: pre-commit runs hooks in parallel when possible
- **File filtering**: Hooks only run on relevant file types
- **Caching**: `uvx` and `bunx` cache dependencies for fast subsequent runs
- **Incremental**: Only staged files are checked (use `--all-files` for full scan)

## Related Documentation

- [TOOL-DEPENDENCIES.md](./TOOL-DEPENDENCIES.md) - Detailed tool information
- [pre-commit documentation](https://pre-commit.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
