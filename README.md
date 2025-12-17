# pigfoot's Claude Code Hubs

A curated collection of plugins, skills, and configuration templates for [Claude Code](https://docs.claude.com/en/docs/claude-code), plus integration with recommended third-party marketplaces.

## What's Inside

### 🔌 Plugins

**From this marketplace (pigfoot):**
- **[commit](./plugins/commit/)** - Smart commit message generation with conventional commits, emoji prefixes, and GPG signing support
- **[context7](./plugins/context7/)** - Access up-to-date documentation and code examples for any library or framework
- **[nano-banana](./plugins/nano-banana/)** - Python scripting and Gemini image generation using uv with inline script dependencies
- **[secure-container-build](./plugins/secure-container-build/)** - Build secure container images with Wolfi runtime, non-root users, and multi-stage builds. Templates for Python/uv, Bun, Node.js/pnpm, Golang, and Rust
- **[github-actions-container-build](./plugins/github-actions-container-build/)** - Build multi-architecture container images in GitHub Actions. Matrix builds (public repos), QEMU (private repos), Podman rootless builds

**Recommended third-party plugins (available in this marketplace):**
- **[superpowers](https://github.com/obra/superpowers)** - Comprehensive skills library with proven development workflows (TDD, debugging, code review)

### 🎯 Skills

Reusable workflow patterns included in plugins - automatically available after plugin installation.

### ⚙️ Configuration Templates

- **[.CLAUDE.md](./.CLAUDE.md)** - Comprehensive development guidelines template with language detection, workflow patterns, and best practices


## Prerequisites

### Required Tools

Before using this marketplace, ensure you have these tools installed:

#### macOS (using Homebrew)

Recommended to use [Homebrew](https://brew.sh/):

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install jq
brew install oven-sh/bun/bun
brew install uv
```

#### Linux

Use `apt`, `apt-get`, `yum`, `pacman`, `apk` or any native package manager tool.

**Example (Debian/Ubuntu):**
```bash
sudo apt-get update && sudo apt-get install -y jq

# bun for javascript/typescript
curl -fsSL https://bun.sh/install | bash
# uv for python
curl -LsSf https://astral.sh/uv/install.sh | sh
```

<details>
<summary>Running Claude Code on Windows</summary>

For the best experience, we recommend using [Windows Terminal](https://aka.ms/terminal):

- **Windows 11:** Windows Terminal is pre-installed. Just open it and run `claude`.
- **Windows 10:** Install Windows Terminal first:
  ```powershell
  # Using winget
  winget install Microsoft.WindowsTerminal

  # Or using Scoop
  scoop install windows-terminal
  ```

</details>

<details>
<summary>Windows (Scoop)</summary>

Install tools using [Scoop](https://scoop.sh/):

```powershell
# Install Scoop if you don't have it
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

# Install required tools
scoop install jq
scoop install bun
scoop install uv
```

> **Note:** Windows built-in `winget` is also possible, however Scoop is recommended for better compatibility with command line tools.

</details>

## Install Claude Code

Follow the [official installation guide](https://code.claude.com/docs/en/setup) or use one of the methods below:

**Homebrew (macOS, Linux):**
```bash
brew install --cask claude-code
```

**macOS, Linux, WSL, Git Bash:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

<details>
<summary>Windows PowerShell</summary>

```powershell
irm https://claude.ai/install.ps1 | iex

# Add to PATH (if needed)
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:USERPROFILE\.local\bin",
    "User"
)
```

</details>

## Custom Settings for Optimal Workflow (Optional)

This one-time setup grants Claude Code necessary permissions and configures `CLAUDE.md` for optimal workflow.

### Step 1: Configure Allow Permissions

**What this does:**
- Grants permissions for common commands (git, file operations, package managers)
- Enables skills and MCP tools
- Optimizes Claude Code settings

**macOS, Linux, WSL, Git Bash:**

```bash
# Create settings file if it doesn't exist
[[ ! -r "${HOME}/.claude/settings.json" ]] && mkdir -p "${HOME}/.claude" && echo "{}" > "${HOME}/.claude/settings.json"

# Add permissions
jq "$(cat <<'EOF'
.permissions.allow = (((.permissions // {}).allow // []) + [
  "Bash(ls:*)", "Bash(pwd:*)", "Bash(echo:*)", "Bash(export:*)", "Bash(test:*)",
  "Bash(mkdir:*)", "Bash(mv:*)", "Bash(cat:*)", "Bash(cp:*)", "Bash(chmod:*)", "Bash(touch:*)",
  "Bash(grep:*)", "Bash(find:*)", "Bash(sed:*)", "Bash(head:*)", "Bash(xargs:*)",
  "Bash(git:*)", "Bash(gh:*)", "Bash(jq:*)", "Bash(curl:*)",
  "Bash(node:*)", "Bash(npm:*)", "Bash(pnpm:*)", "Bash(npx:*)", "Bash(bun:*)", "Bash(bunx:*)",
  "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(uvx:*)",
  "Bash(docker:*)", "Bash(podman:*)", "Bash(buildah:*)",
  "Bash(gh:*)", "Bash(gpg:*)", "Bash(gpgconf:*)",
  "Read", "Edit", "NotebookEdit", "Update", "Write", "WebFetch", "WebSearch",
  "Bash(.specify/scripts/bash/check-prerequisites.sh:*)", "Bash(.specify/scripts/bash/create-new-feature.sh:*)",
  "Bash(.specify/scripts/bash/setup-plan.sh:*)", "Bash(.specify/scripts/bash/update-agent-context.sh:*)",
  "Skill(context7:*)", "mcp__plugin_context7_context7__get-library-docs", "mcp__plugin_context7_context7__resolve-library-id",
  "Skill(commit:*)", "Skill(nano-banana:*)", "Skill(superpowers:*)", "Skill(secure-container-build:*)", "Skill(github-actions-container-build:*)"
] | unique)
  | .alwaysThinkingEnabled = true
  | .includeCoAuthoredBy = false
  | .model = "opusplan"
  | .spinnerTipsEnabled = false
EOF
)" "${HOME}/.claude/settings.json" > /tmp/temp.json && mv -f /tmp/temp.json "${HOME}/.claude/settings.json"

echo "✅ Permissions configured successfully!"
```

<details>
<summary>Windows PowerShell</summary>

```powershell
# Create settings file if it doesn't exist
$settingsPath = "$env:USERPROFILE\.claude\settings.json"
if (-not (Test-Path $settingsPath)) {
    New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude" | Out-Null
    "{}" | Out-File -Encoding utf8 $settingsPath
}

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

if (-not $settings.permissions) {
    $settings | Add-Member -Type NoteProperty -Name "permissions" -Value ([PSCustomObject]@{}) -Force
}

if (-not $settings.permissions.allow) {
    $settings.permissions | Add-Member -Type NoteProperty -Name "allow" -Value @() -Force
}

$newPermissions = @(
    "Bash(git:*)", "Bash(gh:*)", "Bash(jq:*)", "Bash(curl:*)",
    "Bash(node:*)", "Bash(npm:*)", "Bash(pnpm:*)", "Bash(npx:*)", "Bash(bun:*)", "Bash(bunx:*)",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(uvx:*)",
    "Bash(docker:*)", "Bash(podman:*)", "Bash(buildah:*)",
    "Bash(gh:*)", "Bash(gpg:*)", "Bash(gpgconf:*)",
    "Read", "Edit", "NotebookEdit", "Update", "Write", "WebFetch", "WebSearch",
    "Bash(.specify/scripts/bash/check-prerequisites.sh:*)", "Bash(.specify/scripts/bash/create-new-feature.sh:*)",
    "Bash(.specify/scripts/bash/setup-plan.sh:*)", "Bash(.specify/scripts/bash/update-agent-context.sh:*)",
    "Skill(context7:*)", "mcp__plugin_context7_context7__get-library-docs", "mcp__plugin_context7_context7__resolve-library-id",
    "Skill(commit:*)", "Skill(nano-banana:*)", "Skill(superpowers:*)", "Skill(secure-container-build:*)", "Skill(github-actions-container-build:*)"
)

$merged = @($settings.permissions.allow) + $newPermissions | Select-Object -Unique
$settings.permissions.allow = $merged

$settings | Add-Member -Type NoteProperty -Name "alwaysThinkingEnabled" -Value $true -Force
$settings | Add-Member -Type NoteProperty -Name "includeCoAuthoredBy" -Value $false -Force
$settings | Add-Member -Type NoteProperty -Name "model" -Value "opusplan" -Force
$settings | Add-Member -Type NoteProperty -Name "spinnerTipsEnabled" -Value $false -Force

$settings | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $settingsPath

Write-Host "✅ Permissions configured successfully!"
```

</details>

### Step 2: Install Plugins

**Inside Claude Code**, run these commands to install plugins from [pigfoot/claude-code-hubs](https://github.com/pigfoot/claude-code-hubs):

```bash
# Add marketplace
/plugin marketplace add pigfoot/claude-code-hubs

# Install plugins (all available from pigfoot marketplace)
/plugin install commit@pigfoot
/plugin install context7@pigfoot
/plugin install nano-banana@pigfoot
/plugin install secure-container-build@pigfoot
/plugin install github-actions-container-build@pigfoot
/plugin install superpowers@pigfoot
```

### Step 3: Setup CLAUDE.md Template (Optional but Recommended)

The [CLAUDE.md](https://github.com/pigfoot/claude-code-hubs/blob/main/.CLAUDE.md) template provides comprehensive development guidelines that work with installed plugins.

**For global configuration (applies to all projects):**

**macOS, Linux, WSL, Git Bash:**
```bash
claudeDir="${HOME}/.claude"
curl -fsSL https://raw.githubusercontent.com/pigfoot/claude-code-hubs/main/.CLAUDE.md -o "${claudeDir}/CLAUDE.md"
```

<details>
<summary>Windows PowerShell</summary>

```powershell
$claudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $claudeDir)) { New-Item -ItemType Directory -Path $claudeDir }
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/pigfoot/claude-code-hubs/main/.CLAUDE.md" -OutFile "$claudeDir\CLAUDE.md"
```

</details>

**For project-specific configuration:**

Change `claudeDir` to your project root folder (e.g., `claudeDir="."` or `$claudeDir = "."`) in the commands above.

## Usage

### 🎯 commit Plugin - Smart Git Commits

```bash
/plugin install commit@pigfoot
```

**What it does:**
Automates the tedious parts of creating well-formatted commits.

**Benefits:**
- ✅ **No more commit message writer's block** - Analyzes your changes and suggests appropriate messages
- ✅ **Consistent format** - Automatic conventional commits with emoji (`✨ feat:`, `🐛 fix:`, etc.)
- ✅ **Multi-concern detection** - Suggests splitting commits when you've mixed different types of changes
- ✅ **GPG signing made easy** - Handles passphrase caching automatically
- ✅ **DCO compliance** - Always includes --signoff for projects requiring it

**Usage:**
Just say "commit changes" and Claude will handle the rest.

**Example:**
```bash
User: "commit changes"
→ Claude analyzes: auth changes + UI updates + docs
→ Suggests: Split into 3 commits?
→ Creates: ✨ feat: add JWT authentication
         💄 style: update login UI
         📝 docs: update auth documentation
```

---

### 📚 context7 Plugin - Up-to-Date Library Docs

```bash
/plugin install context7@pigfoot
```

**What it does:**
Fetches current documentation and code examples from any library or framework.

**Benefits:**
- ✅ **Always current** - Gets latest docs, not outdated LLM training data
- ✅ **Better suggestions** - Claude works with actual API docs and best practices
- ✅ **Faster learning** - No need to manually browse documentation sites
- ✅ **Accurate examples** - Real code snippets from official sources
- ✅ **Version-specific** - Can target specific library versions

**Usage:**
Ask Claude about any library naturally.

**Examples:**
- "Show me the latest Next.js routing docs"
- "How do I use MongoDB aggregation pipeline?"
- "What are the best practices for React hooks?"
- "How to configure Vite for a library?"

**Behind the scenes:**
Claude automatically fetches documentation from Context7's curated database.

---

### 🍌 nano-banana Plugin - AI Image Generation

```bash
/plugin install nano-banana@pigfoot
```

**What it does:**
Generates and edits images using Google's Gemini models with Python scripting powered by uv.

**Benefits:**
- ✅ **AI image generation** - Create images from text descriptions using Gemini 3 Pro (Nano Banana Pro)
- ✅ **Image editing** - Edit existing images with AI-powered transformations
- ✅ **Interactive prompting** - Get help crafting effective prompts for better results
- ✅ **Inline dependencies** - Self-contained Python scripts with `uv run` and inline script metadata
- ✅ **Multiple models** - Choose between fast generation and professional quality

**Prerequisites:**
- [uv](https://docs.astral.sh/uv/) installed
- `GOOGLE_API_KEY` environment variable set with a valid Gemini API key

**Usage:**
Ask Claude to generate or edit images naturally.

**Examples:**
- "Generate an image of a futuristic cityscape at sunset"
- "Create a cute banana character with sunglasses"
- "Help me write a prompt for a professional product photo"
- "Edit this image to add a party hat"

**Skills Included:**
- `nano-banana` - Direct image generation and editing
- `nano-banana-prompting` - Interactive prompt crafting with best practices

**Behind the scenes:**
Claude uses Python with Google's Gemini API to generate images. Scripts run via `uv` with automatic dependency management, making it easy to create high-quality AI art.

---

### 🐳 secure-container-build Plugin - Secure Container Images

```bash
/plugin install secure-container-build@pigfoot
```

**What it does:**
Provides Containerfile templates and best practices for building secure container images.

**Benefits:**
- ✅ **Security-first runtime** - Wolfi distroless images with minimal attack surface and no CVEs
- ✅ **Non-root containers** - Run as UID 65532 by default
- ✅ **Multi-stage builds** - Minimal runtime images with only necessary artifacts
- ✅ **Production & debug variants** - Switch between secure production and debug-friendly images
- ✅ **Allocator optimization** - mimalloc support for Rust builds

**Supported Stacks:**
- **Python + uv** - Fast, reproducible Python builds
- **Bun** - All-in-one JavaScript runtime
- **Node.js + pnpm** - Efficient workspace-friendly builds
- **Golang** - Static and CGO builds
- **Rust** - glibc and musl builds with allocator options

**Usage:**
Ask Claude to create secure Containerfiles for your project.

**Examples:**
- "Create a secure Containerfile for my Python app"
- "Set up a multi-stage build for my Rust project"
- "Help me optimize my container image size"

---

### 🚀 github-actions-container-build Plugin - CI/CD Workflows

```bash
/plugin install github-actions-container-build@pigfoot
```

**What it does:**
Provides GitHub Actions workflows for building multi-architecture container images.

**Benefits:**
- ✅ **Matrix builds** - Native ARM64 runners for public repos (10-50x faster)
- ✅ **QEMU fallback** - Free emulation for private repos
- ✅ **Podman rootless** - Secure, daemonless container builds
- ✅ **Multi-arch manifests** - Single tag for amd64 and arm64
- ✅ **Retry logic** - Automatic retries for transient failures

**Usage:**
Ask Claude to set up CI/CD for your container builds.

**Examples:**
- "Set up GitHub Actions for multi-arch container builds"
- "I need a workflow to build ARM64 images for my public repo"
- "Create a container build pipeline for my private repository"

**Demo**
[![asciicast](https://asciinema.org/a/rda4CuvQuKXcl2DsfsU9Gul3N.svg)](https://asciinema.org/a/rda4CuvQuKXcl2DsfsU9Gul3N)

---

### 🦸 superpowers Plugin - Proven Development Workflows

```bash
/plugin install superpowers@pigfoot
```

> **Note:** This is a third-party plugin originally from [obra/superpowers](https://github.com/obra/superpowers), available in this marketplace for convenient installation

**What it does:**
Provides a comprehensive library of battle-tested skills that enforce systematic development practices.

**Benefits:**
- ✅ **TDD enforcement** - Test-Driven Development skill ensures you write tests first
- ✅ **Systematic debugging** - Four-phase framework (investigate → analyze → test → implement) instead of guess-and-fix
- ✅ **Code review automation** - Built-in review checkpoints before completing major tasks
- ✅ **Better planning** - Skills for breaking down complex work into manageable tasks
- ✅ **Verification gates** - "Evidence before claims" - forces running tests before saying "it works"
- ✅ **Parallel execution** - Dispatch multiple agents for independent tasks
- ✅ **Anti-patterns prevention** - Stops common mistakes (testing mocks, skipping tests, etc.)

**Key Skills Included:**

**Testing:**
- `test-driven-development` - Write test first, watch it fail, make it pass
- `condition-based-waiting` - Replace flaky timeouts with condition polling
- `testing-anti-patterns` - Prevents testing mock behavior and test-only methods

**Debugging:**
- `systematic-debugging` - Root cause first, then fix (no more guess-and-patch)
- `root-cause-tracing` - Trace bugs backward through call stack
- `verification-before-completion` - Must run verification before claiming "done"
- `defense-in-depth` - Validate at every layer to make bugs structurally impossible

**Collaboration:**
- `brainstorming` - Refines rough ideas into solid designs via Socratic method
- `writing-plans` - Creates detailed implementation plans for engineers
- `executing-plans` - Executes plans in batches with review checkpoints
- `requesting-code-review` - Automatic review against requirements
- `dispatching-parallel-agents` - Handle multiple independent failures concurrently

**Development:**
- `using-git-worktrees` - Isolated workspaces for parallel feature work
- `finishing-a-development-branch` - Structured options for merge/PR/cleanup

**Usage:**
Skills activate automatically when relevant, or you can invoke directly.

**Examples:**
```bash
# Automatic activation
User: "Add user authentication"
→ brainstorming skill activates for design refinement
→ test-driven-development activates during implementation
→ verification-before-completion activates before claiming done

# Manual invocation
User: "/brainstorm how to architect this feature"
```

**Why it matters:**
Without superpowers, you might get working code. With superpowers, you get **tested, verified, systematically-designed code** that follows proven patterns.

---

### ⚙️ .CLAUDE.md Configuration

Once configured, Claude will:
- Auto-detect your communication language (supports Traditional Chinese, Japanese, etc.)
- Write all code and documentation in English
- Follow your project's conventions
- Apply TDD workflow automatically (when superpowers installed)
- Use the right tools for your stack
- Integrate seamlessly with commit and context7 plugins

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [commit](./plugins/commit/) | Conventional commits with emoji and GPG signing | 0.0.1 |
| [context7](./plugins/context7/) | Library documentation via Context7 MCP server | 0.0.1 |
| [nano-banana](./plugins/nano-banana/) | Python scripting and Gemini image generation | 0.0.1 |
| [secure-container-build](./plugins/secure-container-build/) | Secure container images with Wolfi runtime | 0.0.1 |
| [github-actions-container-build](./plugins/github-actions-container-build/) | Multi-arch container builds in GitHub Actions | 0.0.1 |

## Project Structure

```
claude-code-hubs/
├── .claude-plugin/
│   └── marketplace.json                        # Marketplace registry
├── plugins/
│   ├── commit/                          # Git commit automation plugin
│   ├── context7/                        # Documentation plugin
│   ├── nano-banana/                     # AI image generation plugin
│   ├── secure-container-build/          # Containerfile templates plugin
│   └── github-actions-container-build/  # GitHub Actions CI/CD plugin
├── .CLAUDE.md                                  # Global configuration template
├── .specify/                                   # Spec-kit templates and memory
└── README.md                                   # This file
```

## Troubleshooting

<details>
<summary>Click to expand troubleshooting guide</summary>

### Permission Issues

If Claude asks for permissions repeatedly:
```bash
# Verify settings were applied
cat ~/.claude/settings.json | jq '.permissions.allow'

# Re-run the permission configuration script
```

### Plugin Installation Fails

```bash
# Inside Claude Code, check marketplace connection
/plugin marketplace list

# Try removing and re-adding marketplace
/plugin marketplace remove pigfoot/claude-code-hubs
/plugin marketplace add pigfoot/claude-code-hubs
```

### Tools Not Found

Ensure tools are in your PATH:
```bash
# Check installations
which jq bun uv

# If not found, reinstall following Prerequisites section
```

</details>

## Advanced Configuration

### Customizing .CLAUDE.md

The template includes:
- **Language Detection**: Auto-detects your primary language
- **Git Workflow**: Smart commit patterns with the commit plugin
- **Testing**: TDD workflow activation
- **Tool Detection**: Auto-discovers your project's stack

Edit `~/.claude/CLAUDE.md` or `./CLAUDE.md` to customize for your needs.

### Adding More Plugins

Browse available plugins in `plugins/` directory, then:
```bash
/plugin install <plugin-name>@pigfoot
```

## Available Plugins

| Plugin | Origin | Description | Skills Included |
|--------|--------|-------------|-----------------|
| [commit](./plugins/commit/) | pigfoot | Conventional commits with emoji and GPG signing | `commit:commit` |
| [context7](./plugins/context7/) | pigfoot | Library documentation via Context7 MCP | `context7:skills` |
| [nano-banana](./plugins/nano-banana/) | pigfoot | Python scripting and Gemini image generation | `nano-banana:nano-banana`, `nano-banana:nano-banana-prompting` |
| [secure-container-build](./plugins/secure-container-build/) | pigfoot | Secure container images with Wolfi runtime | `secure-container-build:secure-container-build` |
| [github-actions-container-build](./plugins/github-actions-container-build/) | pigfoot | Multi-arch container builds in GitHub Actions | `github-actions-container-build:github-actions-container-build` |
| [superpowers](https://github.com/obra/superpowers) | 3rd-party (obra) | Proven development workflows (TDD, debugging, review) | 17+ skills (brainstorming, TDD, systematic-debugging, etc.) |

**Installation:** All plugins can be installed from this marketplace using `/plugin install <name>@pigfoot`

## Contributing

Contributions are welcome! If you'd like to add a plugin or improve existing ones:
- Read [.specify/memory/constitution.md](./.specify/memory/constitution.md) for project principles
- Include complete documentation and tests
- Use semantic versioning

## For Plugin Developers

Interested in creating your own plugins? See our [Developer Guide](./docs/DEVELOPMENT.md) for:
- Plugin structure and standards
- Skill development best practices
- Testing and quality requirements
- Submission process

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
