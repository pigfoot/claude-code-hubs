---
name: github-actions-container-build
description: Build multi-architecture container images in GitHub Actions. Matrix builds (public repos with native ARM64), QEMU emulation (private repos), or ARM64 larger runners (Team/Enterprise). Uses Podman rootless builds with manifest support
---

# GitHub Actions Container Build

Build multi-architecture container images in GitHub Actions using Podman and native ARM64 runners.

## Core Principles

### Choose Your Workflow

**CRITICAL: Ask these questions before generating any workflow.**

**Question 1: Is your GitHub repository public?**
- **Yes** → Use `github-actions-workflow-matrix-build.yml` (free standard ARM64 runners, 10-50x faster)
- **No** → Go to Question 2

**Question 2: Do you have GitHub Team/Enterprise + willing to pay for ARM64 builds?**
- **Yes** → Use ARM64 larger runners (custom setup required, paid per minute)
- **No** → Use `github-actions-workflow-qemu.yml` (free QEMU emulation, slower but works on free tier)

### 1. Matrix Builds (Public Repos)

**For public repositories** - use GitHub-hosted standard ARM64 runners:
- 10-50x faster builds (native vs. emulation)
- Better reliability and accuracy
- Lower CI costs
- **Completely free for public repos**
- **Not available for private repos**

```yaml
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: ubuntu-24.04-arm  # Standard ARM64 runner (public repos only)
```

### 2. QEMU Builds (Private Repos - Free Tier)

**For private repositories on free tier** - use QEMU emulation:
- Works on GitHub Free plan
- Slower (10-50x) than native ARM64 runners
- Uses `docker/setup-qemu-action` for ARM64 emulation
- Single-job pattern with `--platform linux/amd64,linux/arm64`

```yaml
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

### 4. podman-static for Heredoc Support

Ubuntu 24.04's bundled podman (4.9.3) uses buildah 1.33.7 which doesn't support heredoc syntax. Install podman-static for full BuildKit compatibility:

```yaml
- name: Install podman-static
  run: |
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
      PODMAN_ARCH="amd64"
    else
      PODMAN_ARCH="arm64"
    fi
    curl -fsSL -o /tmp/podman-linux-${PODMAN_ARCH}.tar.gz \
      https://github.com/mgoltzsche/podman-static/releases/latest/download/podman-linux-${PODMAN_ARCH}.tar.gz
    cd /tmp && tar -xzf podman-linux-${PODMAN_ARCH}.tar.gz
    sudo cp -f podman-linux-${PODMAN_ARCH}/usr/local/bin/* /usr/bin/
    podman system migrate
```

**Important:** Install to `/usr/bin/` (not `/usr/local/bin/`) to avoid AppArmor issues.

## Quick Start

### For Public Repos (Matrix Build)

1. **Copy workflow template**:
   ```bash
   cp assets/github-actions-workflow-matrix-build.yml .github/workflows/build.yml
   ```

2. **Customize image name**:
   ```yaml
   IMAGE="$REGISTRY/$IMAGE_OWNER/your-app-name"
   ```

3. **Add your Containerfile** (see **secure-container-build** plugin for templates)

### For Private Repos (QEMU)

1. **Copy workflow template**:
   ```bash
   cp assets/github-actions-workflow-qemu.yml .github/workflows/build.yml
   ```

2. Follow steps 2-3 from above.

## Workflow Structure

Each application follows this pattern:

### Matrix Build Workflow
1. **Build job** (matrix): Build and push architecture-specific images on native runners
2. **Manifest job**: Create and push multi-arch manifest combining both architectures

### QEMU Workflow
1. **Single job**: Build multi-arch manifest directly with `--platform` flag

## Multi-arch Manifest Creation

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

## ARM64 Larger Runners (Private Repos with Team/Enterprise)

**For private repositories with GitHub Team or Enterprise Cloud plans:**

Standard ARM64 runners (`ubuntu-24.04-arm`) don't work in private repos. Instead, create **ARM64 larger runners**:

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

## Registry Configuration

### GitHub Container Registry (GHCR) - Default

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_OWNER: ${{ github.repository_owner }}

- name: Login to GHCR
  run: |
    echo "${{ secrets.GITHUB_TOKEN }}" | podman login "$REGISTRY" \
      -u "${{ github.actor }}" \
      --password-stdin
```

### Docker Hub (Optional)

```yaml
- name: Login to Docker Hub
  run: |
    echo "${{ secrets.DOCKERHUB_TOKEN }}" | podman login docker.io \
      -u "${{ secrets.DOCKERHUB_USERNAME }}" \
      --password-stdin

# Push to Docker Hub
podman push "docker://docker.io/${{ secrets.DOCKERHUB_USERNAME }}/app:$TAG"
```

## Reference Documentation

For detailed information, see `references/github-actions-best-practices.md`.

## Containerfile Templates

For Containerfile templates and security best practices, see the **secure-container-build** plugin which provides:
- Production-ready templates for Python/uv, Bun, Node.js/pnpm, Golang, and Rust
- Wolfi runtime images with non-root users
- Multi-stage build patterns
- Allocator optimization for Rust

## Troubleshooting

### Common Issues

**Authentication failed**:
- Ensure GITHUB_TOKEN has package write permission
- Check registry URL and credentials

**Manifest add failed**:
- Verify architecture-specific images exist in registry
- Check image tags match exactly

**ARM64 runner not available**:
- Standard ARM64 runners only work for public repos
- For private repos, use QEMU or larger runners

**podman-static installation fails**:
- Verify correct architecture detection
- Check GitHub releases for podman-static availability

**AppArmor issues**:
- Install binaries to `/usr/bin/` not `/usr/local/bin/`
- Run `podman system migrate` after installation

### Local Testing

**Test manifest locally**:
```bash
podman manifest inspect "$IMAGE:latest"
```

**Verify multi-arch support**:
```bash
podman manifest inspect ghcr.io/owner/app:latest | jq '.manifests[].platform'
```
