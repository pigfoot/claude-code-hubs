---
name: github-actions-secure-container-build
description: Build secure, multi-architecture container images in GitHub Actions with Wolfi runtime and Podman. Supports (1) public repos with free standard ARM64 runners, (2) private repos with QEMU emulation or ARM64 larger runners, (3) Containerfiles with security best practices (Wolfi runtime, non-root, heredoc syntax), (4) Python/uv, Bun, and Node.js/pnpm builds, (5) production and debug image variants with comprehensive troubleshooting guides.
---

# GitHub Container CI Best Practices

Build secure, multi-architecture container images in GitHub Actions using native ARM64 runners and security-hardened runtime images.

## Core Principles

⚠️ **CRITICAL: Choose Your Workflow**

**Question 1: Is your GitHub repository public?**
- ✅ **Yes** → Use `github-actions-workflow-native-arm64.yml` (free standard ARM64 runners, 10-50x faster)
- ❌ **No** → Go to Question 2

**Question 2: Do you have GitHub Team/Enterprise + willing to pay for ARM64 builds?**
- ✅ **Yes** → Use ARM64 larger runners (custom setup required, paid per minute, see "ARM64 Larger Runners" section)
- ❌ **No** → Use `github-actions-workflow-qemu.yml` (free QEMU emulation, slower but works on free tier)

**This skill will always ask these questions before generating any workflow.**

---

### 1. Security-First Runtime Images

Use **Wolfi glibc-dynamic** as the runtime base image:
- Minimal attack surface (no unnecessary packages)
- Built-in CVE-free by design
- Non-root user by default (UID 65532)
- Regular security updates by Chainguard

**Production vs Development:**
```dockerfile
# ARG for choosing runtime image tag
ARG RUNTIME_TAG=latest
FROM cgr.dev/chainguard/glibc-dynamic:${RUNTIME_TAG}
```

- **`latest`** (default): Production - no shell, most secure ⭐
- **`latest-dev`**: Development - includes shell for debugging

**Build for debugging:**
```bash
podman build --build-arg RUNTIME_TAG=latest-dev -t myapp:debug .
podman run -it myapp:debug sh  # Can exec with shell
```

### 2. Native Multi-arch Builds (Standard ARM64 Runners)

**For public repositories** - use GitHub-hosted standard ARM64 runners:
- 10-50x faster builds (native vs. emulation)
- Better reliability and accuracy
- Lower CI costs
- **Completely free for public repos** ✅
- **Not available for private repos** ❌ (use QEMU or larger runners instead)

```yaml
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: ubuntu-24.04-arm  # Standard ARM64 runner (public repos only)
```

### 2b. QEMU Multi-arch Builds (Private Repos - Free Tier)

**For private repositories on free tier** - use QEMU emulation:
- Works on GitHub Free plan
- Slower (10-50x) than native ARM64 runners
- Uses `docker/setup-qemu-action` for ARM64 emulation
- Single-job pattern with `--platform linux/amd64,linux/arm64`

**Why QEMU for private repos?**
- Standard ARM64 runners (`ubuntu-24.04-arm`) don't work in private repos at all
- ARM64 larger runners require Team/Enterprise plan + per-minute billing
- QEMU provides ARM64 compatibility without additional costs
- Acceptable tradeoff for private projects with limited CI budgets

**Key difference:**
```yaml
# Native ARM64 (public repos): Matrix strategy, separate runners
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: ubuntu-24.04-arm

# QEMU (private repos): Single runner with platform flag
runs-on: ubuntu-latest
steps:
  - uses: docker/setup-qemu-action@v3
  - run: podman build --platform linux/amd64,linux/arm64 --manifest ...
```

### 3. Podman Over Docker

Use Podman for container builds:
- Rootless by default (better security)
- No daemon required
- Native multi-arch manifest support
- OCI compliant

### 4. Multi-stage Builds

Always use multi-stage builds to minimize runtime image size:
- **Builder stage**: Full build environment (Python/Node.js official images)
- **Runtime stage**: Minimal Wolfi image with only runtime artifacts

## Quick Start

**FIRST:** Determine repository type and choose workflow template:

⚠️ **Ask the user:**
```
Is your GitHub repository public or private?
- Public → Use github-actions-workflow-native-arm64.yml (recommended, 10-50x faster)
- Private → Use github-actions-workflow-qemu.yml (QEMU emulation, free tier compatible)
```

### Python + uv Project (Public Repo)

1. **Copy Containerfile template**:
   ```bash
   cp assets/Containerfile.python-uv ./Containerfile
   ```

2. **Update application command**:
   ```dockerfile
   CMD ["python", "your_app.py"]  # Change to your entry point
   ```

3. **Copy GitHub Actions workflow** (choose based on repo type):

   **For public repos (native ARM64):**
   ```bash
   cp assets/github-actions-workflow-native-arm64.yml .github/workflows/build.yml
   ```

   **For private repos (QEMU):**
   ```bash
   cp assets/github-actions-workflow-qemu.yml .github/workflows/build.yml
   ```

4. **Customize image name** in workflow:
   ```yaml
   IMAGE="$REGISTRY/$IMAGE_OWNER/your-app-name"
   ```

### Bun Project

1. **Copy Containerfile template**:
   ```bash
   cp assets/Containerfile.bun ./Containerfile
   ```

2. **Update runtime command**:
   ```dockerfile
   CMD ["bun", "run", "start"]  # Change to your script
   ```

3. Follow steps 3-4 from Python section above.

### Node.js + pnpm Project

1. **Copy Containerfile template**:
   ```bash
   cp assets/Containerfile.nodejs ./Containerfile
   ```

2. **Update entry point**:
   ```dockerfile
   CMD ["node", "./dist/index.js"]  # Change to your compiled output
   ```

3. Follow steps 3-4 from Python section above.

### Golang Project

**First: Do you need CGO?** (packages with C bindings)

Most Go projects don't need CGO. Quick test:
```bash
CGO_ENABLED=0 go build .
# ✅ Success → Use Containerfile.golang (static, recommended)
# ❌ Fails → Use Containerfile.golang-cgo (CGO)
```

**Common CGO packages:** `mattn/go-sqlite3`, `git2go/git2go`, `h2non/bimg`

**Option A: Pure Go (no CGO) - Recommended**

1. **Copy Containerfile template**:
   ```bash
   cp assets/Containerfile.golang ./Containerfile
   ```

2. **Update binary name**:
   ```dockerfile
   CMD ["/app/server"]  # Change to your binary name
   ```

3. Follow steps 3-4 from Python section above.

**Option B: Requires CGO (SQLite, C libraries)**

1. **Copy CGO template**:
   ```bash
   cp assets/Containerfile.golang-cgo ./Containerfile
   ```

2. Follow steps 2-3 from Option A above.

## Builder Image Selection

### Python Projects

```dockerfile
FROM docker.io/python:3-slim AS builder
```

Use official Python slim images for building Python applications with uv.

### Bun/Node.js Projects

```dockerfile
FROM docker.io/node:lts-slim AS builder
```

Use official Node.js LTS slim images for building Bun or Node.js applications.

### Golang Projects

```dockerfile
FROM docker.io/golang:1 AS builder
```

Use official Golang images for building Go applications. Includes Go toolchain and gcc for CGO support.

## Key Patterns

### Non-root User Configuration

Wolfi images use UID 65532 (nonroot user) by default:

```dockerfile
# No need to create user, already exists in Wolfi
USER 65532:65532

# When copying files from builder, set ownership
COPY --from=builder --chown=65532:65532 /app /app
```

### Init System (tini)

Wolfi images don't include tini. Copy it from builder:

```dockerfile
# Copy tini from builder stage
COPY --from=builder /usr/bin/tini-static /usr/bin/tini

# Use as entrypoint for proper signal handling
ENTRYPOINT ["tini", "--"]
CMD ["your-app"]
```

### Build Cache Optimization

Use BuildKit cache mounts to speed up dependency installation:

```dockerfile
# Python/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Bun
RUN bun install --frozen-lockfile

# pnpm
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
```

### Multi-arch Manifest Creation

After building architecture-specific images, create a multi-arch manifest:

```bash
IMAGE="$REGISTRY/$IMAGE_OWNER/app"

# Create manifest
podman manifest create "$IMAGE:latest" || true

# Add architecture-specific images
podman manifest add "$IMAGE:latest" "docker://$IMAGE:amd64"
podman manifest add "$IMAGE:latest" "docker://$IMAGE:arm64"

# Push manifest
podman manifest push --all "$IMAGE:latest"
```

## Workflow Structure

Each application follows this pattern:

1. **Build job** (matrix): Build and push architecture-specific images on native runners
2. **Manifest job**: Create and push multi-arch manifest combining both architectures

Example job names:
- `build-python-uv` → `manifest-python-uv`
- `build-bun` → `manifest-bun`
- `build-node` → `manifest-node`

## Reference Documentation

For detailed information, consult these reference files:

- **Security practices**: See `references/security-best-practices.md`
- **GitHub Actions patterns**: See `references/github-actions-best-practices.md`
- **Dependency management**: See `references/dependency-management.md`
- **Debugging containers**: See `references/debugging-containers.md`

## Debugging Support

All Containerfile templates support both production and debug builds:

### Production Build (Default)
```bash
podman build -t myapp:latest .
```
- Uses `cgr.dev/chainguard/glibc-dynamic:latest`
- No shell (most secure)
- Minimal attack surface

### Debug Build
```bash
podman build --build-arg RUNTIME_TAG=latest-dev -t myapp:debug .
```
- Uses `cgr.dev/chainguard/glibc-dynamic:latest-dev`
- Includes shell and basic tools
- For development/troubleshooting only

⚠️ **Never use debug images in production!**

For detailed debugging techniques, see `references/debugging-containers.md`.

## Troubleshooting

### Common Issues

**Authentication failed**:
- Ensure GITHUB_TOKEN has package write permission
- Check registry URL and credentials

**Manifest add failed**:
- Verify architecture-specific images exist in registry
- Check image tags match exactly

**Build timeout**:
- Review Containerfile for inefficient layers
- Enable BuildKit cache mounts
- Consider splitting large builds

**ARM64 runner not available**:
- Ensure GitHub-hosted ARM64 runners are enabled for your repository
- Check runner availability in repository settings

### Local Testing

**Test image locally**:
```bash
podman run --rm -it "$IMAGE:$TAG"
```

**Inspect built image**:
```bash
podman inspect "$IMAGE:$TAG"
```

**View manifest**:
```bash
podman manifest inspect "$IMAGE:latest"
```

## Customization

### ARM64 Larger Runners (Private Repos with Team/Enterprise)

**For private repositories with GitHub Team or Enterprise Cloud plans:**

Standard ARM64 runners (`ubuntu-24.04-arm`) don't work in private repos. Instead, you can create **ARM64 larger runners**:

**Setup steps:**
1. Go to **Organization Settings → Actions → Runners → New runner**
2. Select **"Larger runners"**
3. Choose **"Ubuntu 24.04 by Arm Limited"** partner image
4. Name your runner (e.g., `my-org-arm64-runner`)
5. Configure size (e.g., 4-core, 16GB RAM)

**Update workflow to use custom runner:**
```yaml
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: my-org-arm64-runner  # Your custom ARM64 larger runner name
```

**Cost:**
- Billed per minute (not included in free minutes)
- ~37% cheaper than x64 larger runners
- Ref: [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)

### Changing Runtime Image

If Wolfi glibc-dynamic doesn't meet your needs, consider:
- `cgr.dev/chainguard/static:latest` - For static binaries
- `cgr.dev/chainguard/python:latest` - Python-specific Wolfi image
- `cgr.dev/chainguard/node:latest` - Node.js-specific Wolfi image

Update the runtime stage `FROM` line accordingly.

### Adding More Architectures

To add ARM32 or other architectures:

1. Add to build matrix:
   ```yaml
   - arch: armv7
     runner: ubuntu-24.04-arm  # Or custom runner
   ```

2. Add to manifest:
   ```bash
   podman manifest add "$IMAGE:latest" "docker://$IMAGE:armv7"
   ```

### Registry Configuration

To use different registries (Docker Hub, AWS ECR, etc.):

1. Update `REGISTRY` environment variable
2. Adjust login command with appropriate credentials
3. Update image naming format if needed
