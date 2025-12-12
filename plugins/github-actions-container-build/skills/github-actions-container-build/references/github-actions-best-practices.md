# GitHub Actions Multi-arch Build Best Practices

## Public vs Private Repos: Choosing the Right Approach

### Decision Flowchart

```
Question 1: Is your repo public?
│
├─ YES (Public Repo)
│  └─ Use Standard ARM64 Runners ✅
│     • Free ubuntu-24.04-arm runners
│     • 10-50x faster (native)
│     • No setup required
│     → Use github-actions-workflow-native-arm64.yml
│
└─ NO (Private Repo)
   │
   Question 2: Have Team/Enterprise + willing to pay?
   │
   ├─ YES
   │  └─ Use ARM64 Larger Runners 💰
   │     • Custom runner setup required
   │     • Billed per minute (~37% cheaper than x64)
   │     • 10-50x faster (native)
   │     → Create custom ARM64 runner, modify workflow
   │
   └─ NO
      └─ Use QEMU Emulation ⚠️
         • Free tier compatible
         • 10-50x slower (emulation)
         • No additional setup
         → Use github-actions-workflow-qemu.yml
```

### Why This Matters

**Standard ARM64 runners (`ubuntu-24.04-arm`):**
- ✅ **Public repos**: Free, unlimited, works out of the box
- ❌ **Private repos**: **Don't work at all** (workflow will fail)

**ARM64 Larger Runners (custom runners):**
- ✅ **Private repos with Team/Enterprise**: Available (requires setup + billing)
- ❌ **Free tier**: Not available

**QEMU Emulation:**
- ✅ **All repos**: Works on free tier
- ⚠️ **Performance**: 10-50x slower than native

---

## Native ARM64 Runners (Public Repos Only)

### Why Native Runners?

Using native GitHub-hosted ARM64 runners instead of QEMU provides:

- **10-50x faster builds**: Native compilation vs. emulation
- **Better reliability**: No QEMU compatibility issues
- **Accurate testing**: True ARM64 environment
- **Lower costs**: Faster builds = less runner time

### Runner Configuration

```yaml
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: ubuntu-24.04-arm  # GitHub-hosted ARM64 runner
runs-on: ${{ matrix.runner }}
```

## Podman vs Docker

### Why Podman?

- **Rootless by default**: Better security
- **No daemon**: Direct container runtime
- **OCI compliant**: Works with all registries
- **Native manifest support**: Built-in multi-arch manifest creation

### Podman Installation

**Important:** Use `podman-static` instead of Ubuntu's default podman:

```yaml
- name: Install podman-static for heredoc support
  run: |
    echo "=== Installing podman-static v5.6.2 ==="
    # Why podman-static?
    # - Containerfile uses RUN <<EOT heredoc syntax (requires buildah >= 1.35.0)
    # - Ubuntu 24.04 podman (4.9.3) uses buildah 1.33.7 (too old, no heredoc)

    # Download correct architecture binary (for matrix builds)
    ARCH="${{ matrix.arch }}"
    if [ "$ARCH" = "amd64" ]; then
      PODMAN_ARCH="amd64"
    else
      PODMAN_ARCH="arm64"
    fi

    curl -fsSL -o /tmp/podman-linux-${PODMAN_ARCH}.tar.gz \
      https://github.com/mgoltzsche/podman-static/releases/latest/download/podman-linux-${PODMAN_ARCH}.tar.gz
    cd /tmp && tar -xzf podman-linux-${PODMAN_ARCH}.tar.gz

    # Install binaries to /usr/bin (not /usr/local/bin) to avoid AppArmor issues
    # Ref: https://github.com/mgoltzsche/podman-static#apparmor-profile
    sudo cp -f podman-linux-${PODMAN_ARCH}/usr/local/bin/* /usr/bin/
    sudo cp -r podman-linux-${PODMAN_ARCH}/etc/* /etc/ 2>/dev/null || true

    # Initialize rootless podman
    podman system migrate

    echo "Podman installed to: $(which podman)"
    podman --version
    echo "Architecture: $(uname -m)"
```

**Why podman-static?**
- Containerfiles in this skill use heredoc syntax (`RUN <<EOT`)
- Requires buildah >= 1.35.0
- Ubuntu 24.04's default podman (4.9.3) ships with buildah 1.33.7 (too old)
- podman-static v5.6.2 includes modern buildah with heredoc support

**Why install to /usr/bin (not /usr/local/bin)?**
- Avoids AppArmor permission issues on Ubuntu
- `/usr/local/bin/podman` triggers "failed to reexec: Permission denied" errors
- Default AppArmor profile only allows `/usr/bin` paths
- Alternative: Modify AppArmor profile with `sudo aa-complain /usr/bin/runc` (not recommended for CI)
- Ref: https://github.com/mgoltzsche/podman-static#apparmor-profile

## Multi-arch Workflow Pattern

### Step 1: Build Architecture-specific Images

Build each architecture separately on native runners:

```yaml
jobs:
  build-app:
    strategy:
      matrix:
        include:
          - arch: amd64
            runner: ubuntu-24.04
          - arch: arm64
            runner: ubuntu-24.04-arm
    runs-on: ${{ matrix.runner }}
    steps:
      - name: Build & push
        run: |
          IMAGE="${{ env.REGISTRY }}/${{ env.IMAGE_OWNER }}/app"
          TAG="${{ matrix.arch }}"
          
          podman build -f Containerfile -t "$IMAGE:$TAG" .
          podman push "$IMAGE:$TAG"
```

### Step 2: Create Multi-arch Manifest

Combine architecture-specific images into a single manifest:

```yaml
jobs:
  manifest-app:
    needs: build-app
    runs-on: ubuntu-24.04
    steps:
      - name: Create & push manifest
        run: |
          IMAGE="${{ env.REGISTRY }}/${{ env.IMAGE_OWNER }}/app"
          
          podman manifest create "$IMAGE:latest" || true
          podman manifest add "$IMAGE:latest" "docker://$IMAGE:amd64"
          podman manifest add "$IMAGE:latest" "docker://$IMAGE:arm64"
          podman manifest push --all "$IMAGE:latest"
```

## Registry Authentication

### GitHub Container Registry (GHCR)

Use built-in GITHUB_TOKEN for authentication:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_OWNER: ${{ github.repository_owner }}

steps:
  - name: Login to registry
    run: |
      podman login "$REGISTRY" \
        -u "${{ github.actor }}" \
        -p '${{ secrets.GITHUB_TOKEN }}'
```

## Workflow Triggers

Recommended trigger configuration:

```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch: {}  # Allow manual triggers
```

## Cost Optimization

- Use matrix builds to parallelize architecture builds
- Cache build layers when possible (Podman supports BuildKit cache)
- Only rebuild changed applications (path filters)
- Use workflow concurrency to cancel outdated builds

## Debugging Tips

### View Build Logs

```bash
# Check Podman version
podman --version

# Inspect built image
podman inspect "$IMAGE:$TAG"

# Test image locally
podman run --rm -it "$IMAGE:$TAG"
```

### Common Issues

1. **Authentication failed**: Ensure GITHUB_TOKEN has package write permission
2. **Manifest add failed**: Verify architecture-specific images exist
3. **Build timeout**: Check for inefficient Containerfile layers

---

## QEMU Emulation (Private Repos)

### When to Use QEMU

Use QEMU for private repositories on GitHub Free plan:
- Native ARM64 runners require GitHub Team/Enterprise
- QEMU provides ARM64 compatibility without additional costs
- Acceptable tradeoff for private projects with limited CI budgets

### QEMU Setup

```yaml
jobs:
  build-app:
    runs-on: ubuntu-latest  # Single AMD64 runner, not matrix
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Install podman-static for heredoc support
        run: |
          echo "=== Installing podman-static v5.6.2 ==="
          # Why podman-static?
          # - Containerfile uses RUN <<EOT heredoc syntax (requires buildah >= 1.35.0)
          # - Ubuntu 24.04 podman (4.9.3) uses buildah 1.33.7 (too old, no heredoc)

          curl -fsSL -o /tmp/podman-linux-amd64.tar.gz \
            https://github.com/mgoltzsche/podman-static/releases/latest/download/podman-linux-amd64.tar.gz
          cd /tmp && tar -xzf podman-linux-amd64.tar.gz

          # Install binaries to /usr/bin (not /usr/local/bin) to avoid AppArmor issues
          # Ref: https://github.com/mgoltzsche/podman-static#apparmor-profile
          sudo cp -f podman-linux-amd64/usr/local/bin/* /usr/bin/
          sudo cp -r podman-linux-amd64/etc/* /etc/ 2>/dev/null || true

          # Initialize rootless podman
          podman system migrate

          echo "Podman installed to: $(which podman)"
          podman --version

      - name: Build multi-arch image with QEMU
        run: |
          IMAGE="ghcr.io/${{ github.repository_owner }}/app"

          # Single build command for all platforms
          podman build \
            --platform linux/amd64,linux/arm64 \
            --format docker \
            --manifest "$IMAGE:latest" \
            -f ./Containerfile \
            .

          # Push manifest directly
          podman manifest push "$IMAGE:latest" "docker://$IMAGE:latest"
```

### Key Differences from Native ARM64

| Aspect | Native ARM64 | QEMU |
|--------|-------------|------|
| **Runner** | Matrix: `ubuntu-24.04` + `ubuntu-24.04-arm` | Single: `ubuntu-latest` |
| **QEMU Setup** | Not needed | `docker/setup-qemu-action@v3` required |
| **Build Pattern** | Separate builds per arch | Single build with `--platform` |
| **Manifest** | Created after both builds complete | Created during build |
| **Speed** | Fast (native) | Slow (emulation, 10-50x) |
| **Cost** | Free (public only) | Free (all repos) |

### Performance Comparison

**Native ARM64 (Public Repos):**
- AMD64 build: ~2-3 minutes
- ARM64 build: ~2-3 minutes (parallel)
- Total: ~3 minutes (parallel execution)

**QEMU (Private Repos):**
- Multi-arch build: ~30-90 minutes
- Total: ~30-90 minutes (sequential emulation)

**Optimization tips for QEMU:**
- Use BuildKit cache mounts
- Minimize layers in Containerfile
- Consider building only critical architectures
- Use workflow caching for dependencies

### Optional: Docker Hub Support

Both native and QEMU workflows support Docker Hub:

**Setup Docker Hub secrets:**
1. Go to **Settings → Secrets and variables → Actions**
2. Add these secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub account username
   - `DOCKERHUB_TOKEN`: Personal Access Token from [Docker Hub Security](https://hub.docker.com/settings/security)
     - **Required permission**: `Read & Write` (or `Delete` if you need to clean up old tags)

```yaml
- name: Login to Docker Hub
  run: |
    echo "${{ secrets.DOCKERHUB_TOKEN }}" | podman login docker.io \
      -u "${{ secrets.DOCKERHUB_USERNAME }}" \
      --password-stdin

# Then push to both registries
- name: Push to Docker Hub
  run: |
    podman manifest push "$IMAGE:latest" \
      "docker://docker.io/${{ secrets.DOCKERHUB_USERNAME }}/app:latest"
```

---

## ARM64 Larger Runners (Private Repos with Team/Enterprise)

### When to Use

For private repositories with GitHub Team or Enterprise Cloud plans that need native ARM64 performance.

**Important:** Standard ARM64 runners (`ubuntu-24.04-arm`) **don't work in private repos**. You must use larger runners instead.

### Setup Steps

**1. Create ARM64 Larger Runner:**
- Go to **Organization Settings → Actions → Runners → New runner**
- Select **"Larger runners"**
- Choose **"Ubuntu 24.04 by Arm Limited"** partner image
- Name your runner (e.g., `my-org-arm64-4core`)
- Configure size:
  - **4-core, 16GB RAM** (recommended for most builds)
  - **8-core, 32GB RAM** (for heavy builds)

**2. Update Workflow:**
```yaml
strategy:
  matrix:
    include:
      - arch: amd64
        runner: ubuntu-24.04
      - arch: arm64
        runner: my-org-arm64-4core  # Your custom runner name (not ubuntu-24.04-arm)
```

### Cost Comparison

| Runner Type | Public Repo | Private Repo (Free) | Private Repo (Team/Enterprise) |
|-------------|-------------|---------------------|--------------------------------|
| **Standard ARM64** | ✅ Free | ❌ Not available | ❌ Not available |
| **ARM64 Larger Runner** | ❌ Not free | ❌ Not available | ✅ Paid per minute (~37% cheaper than x64) |
| **QEMU Emulation** | ✅ Free | ✅ Free | ✅ Free (but slow) |

### Pricing

- Billed per minute of usage
- ~37% cheaper than equivalent x64 larger runners
- Not included in free minutes
- Ref: [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)

### When to Choose Larger Runners vs QEMU

**Use ARM64 Larger Runners if:**
- Build time is critical (frequent deployments)
- CI budget allows for per-minute billing
- Need native ARM64 testing environment

**Use QEMU if:**
- On free tier or limited CI budget
- Builds are infrequent
- Can tolerate 10-50x slower builds
- Just need ARM64 compatibility, not performance
