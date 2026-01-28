#!/usr/bin/env bash
# Setup script for pre-commit hooks
# Checks prerequisites and installs hooks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error counter
ERRORS=0

echo "🔍 Checking prerequisites for pre-commit hooks..."
echo ""

# Check uv
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} uv installed (version: $UV_VERSION)"
else
    echo -e "${RED}✗${NC} uv not found"
    echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    ERRORS=$((ERRORS + 1))
fi

# Check bun
if command -v bun &> /dev/null; then
    BUN_VERSION=$(bun --version)
    echo -e "${GREEN}✓${NC} bun installed (version: $BUN_VERSION)"
else
    echo -e "${RED}✗${NC} bun not found"
    echo "  Install: curl -fsSL https://bun.sh/install | bash"
    ERRORS=$((ERRORS + 1))
fi

# Check jq
if command -v jq &> /dev/null; then
    JQ_VERSION=$(jq --version | sed 's/jq-//')
    echo -e "${GREEN}✓${NC} jq installed (version: $JQ_VERSION)"
else
    echo -e "${RED}✗${NC} jq not found"
    echo "  Install: brew install jq (macOS) or apt-get install jq (Linux)"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Exit if prerequisites missing
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Missing $ERRORS required tool(s)${NC}"
    echo ""
    echo "Please install missing tools and try again."
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites satisfied${NC}"
echo ""

# Check if already in git repository
if [ ! -d .git ]; then
    echo -e "${RED}✗${NC} Not a git repository"
    echo "  Run: git init"
    exit 1
fi

# Install pre-commit hooks
echo "📦 Installing pre-commit hooks..."
echo ""

# Install pre-commit hook
if uvx --managed-python pre-commit install; then
    echo -e "${GREEN}✓${NC} Pre-commit hook installed"
else
    echo -e "${RED}✗${NC} Failed to install pre-commit hook"
    exit 1
fi

# Install commit-msg hook for conventional commits
if uvx --managed-python pre-commit install --hook-type commit-msg; then
    echo -e "${GREEN}✓${NC} Commit-msg hook installed"
else
    echo -e "${RED}✗${NC} Failed to install commit-msg hook"
    exit 1
fi

echo ""

# Verify configuration files exist
echo "🔍 Verifying configuration files..."
echo ""

CONFIG_FILES=(
    ".pre-commit-config.yaml"
    ".yamllint.yaml"
    ".markdownlint.json"
    ".markdownlintignore"
    ".secrets.baseline"
)

MISSING_CONFIGS=0
for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        echo -e "${GREEN}✓${NC} $config"
    else
        echo -e "${YELLOW}⚠${NC} $config missing (will be created on first run)"
        MISSING_CONFIGS=$((MISSING_CONFIGS + 1))
    fi
done

echo ""

# Verify project-specific scripts
echo "🔍 Verifying project scripts..."
echo ""

SCRIPTS=(
    "scripts/check-versions.py"
    "scripts/validate-skill.py"
)

MISSING_SCRIPTS=0
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo -e "${GREEN}✓${NC} $script"
    else
        echo -e "${RED}✗${NC} $script missing"
        MISSING_SCRIPTS=$((MISSING_SCRIPTS + 1))
    fi
done

echo ""

if [ $MISSING_SCRIPTS -gt 0 ]; then
    echo -e "${RED}❌ Missing $MISSING_SCRIPTS required script(s)${NC}"
    exit 1
fi

# Test pre-commit installation
echo "🧪 Testing pre-commit installation..."
echo ""

if uvx --managed-python pre-commit --version > /dev/null 2>&1; then
    PC_VERSION=$(uvx --managed-python pre-commit --version)
    echo -e "${GREEN}✓${NC} pre-commit version: $PC_VERSION"
else
    echo -e "${RED}✗${NC} pre-commit test failed"
    exit 1
fi

echo ""

# Optional: Run hooks on all files
echo "📝 Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Test hooks on all files (optional):"
echo "   uvx --managed-python pre-commit run --all-files"
echo ""
echo "2. Make your first commit to verify hooks work:"
echo "   git add ."
echo "   git commit -m 'chore: setup pre-commit hooks'"
echo ""
echo "3. Read documentation:"
echo "   - docs/PRE-COMMIT-HOOKS.md - Usage guide"
echo "   - docs/TOOL-DEPENDENCIES.md - Tool details"
echo ""

# Ask if user wants to run hooks now
read -p "Run pre-commit on all files now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Running pre-commit hooks on all files..."
    echo ""
    if uvx --managed-python pre-commit run --all-files; then
        echo ""
        echo -e "${GREEN}✅ All hooks passed!${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Some hooks failed. Review the output above and fix issues.${NC}"
        exit 1
    fi
else
    echo ""
    echo "Skipped. Run manually with: uvx --managed-python pre-commit run --all-files"
fi

echo ""
echo -e "${GREEN}🎉 Pre-commit setup complete!${NC}"
