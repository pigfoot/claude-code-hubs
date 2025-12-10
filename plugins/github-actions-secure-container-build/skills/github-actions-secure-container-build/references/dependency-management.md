# Dependency Management Best Practices

## Python + uv

### Why uv?

- **10-100x faster**: Rust-based package installer
- **Reproducible builds**: Lock file ensures consistent dependencies
- **Cache-friendly**: Excellent support for Docker layer caching
- **Modern**: Designed for container and CI environments

### uv Configuration

```dockerfile
# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configure uv for containers
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
```

### Optimal Build Pattern

```dockerfile
# Install dependencies first (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy source code
COPY . ./

# Install project (separate layer for optimal caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable
```

## Bun

### Why Bun?

- **Fast package installation**: Built-in package manager
- **All-in-one**: Runtime + package manager + bundler
- **Drop-in replacement**: Compatible with npm/yarn/pnpm
- **Small binaries**: Can compile standalone executables

### Bun Configuration

```dockerfile
# Install bun from official image
COPY --from=docker.io/oven/bun:slim /usr/local/bin/bun /usr/local/bin/

# Create symlink for bunx
RUN ln -sf ./bun /usr/local/bin/bunx
```

### Lock File Usage

```dockerfile
# Copy lock file first for caching
COPY package.json bun.lockb* /app/

# Install with frozen lockfile
RUN bun install --frozen-lockfile
```

## Node.js + pnpm

### Why pnpm?

- **Disk efficient**: Content-addressable storage
- **Fast**: Symlink-based approach
- **Strict**: Better dependency resolution than npm
- **Workspace support**: Monorepo-friendly

### pnpm Configuration

```dockerfile
# Enable corepack (pnpm included in Node.js)
RUN corepack enable && corepack use pnpm

# Use cache mount for pnpm store
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --production=false
```

### Production Optimization

```dockerfile
# Build TypeScript
RUN pnpm exec tsc --project .
RUN pnpm build

# Remove devDependencies for runtime
RUN pnpm prune --production
```

## Golang + Go Modules

### Why Go Modules?

- **Built-in dependency management**: No external tools needed (since Go 1.11)
- **Reproducible builds**: go.sum ensures version integrity
- **Fast**: Module cache works well with Docker layer caching
- **Vendoring optional**: Can vendor with `go mod vendor` if needed

### Optimal Build Pattern

```dockerfile
# Copy go.mod and go.sum first (cached layer)
COPY go.mod go.sum ./

# Download dependencies (separate layer for better caching)
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Copy source code
COPY . ./

# Build with caches for both modules and build artifacts
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app/server .
```

### CGO vs Static Builds

**CGO_ENABLED=0 (Static Binary):**
```dockerfile
# Build static binary (no runtime dependencies)
RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-w -s" -o /app/server .

# Runtime: Use static base image
FROM cgr.dev/chainguard/static:latest
```

**Benefits:**
- Single standalone binary (no glibc needed)
- Smallest possible image (~10-20MB)
- Most portable and secure
- Cannot use packages with C bindings

**CGO_ENABLED=1 (Dynamic Binary):**
```dockerfile
# Build with CGO enabled (can use C libraries)
RUN CGO_ENABLED=1 GOOS=linux \
    go build -ldflags="-w -s" -o /app/server .

# Runtime: Use glibc-dynamic base image
FROM cgr.dev/chainguard/glibc-dynamic:latest
```

**Benefits:**
- Can use packages with C bindings (SQLite, libgit2, etc.)
- Requires glibc at runtime
- Slightly larger image (~30-50MB)

**Build flags:**
- `-ldflags="-w -s"` - Strip debug info and symbol table (smaller binary)
- `-trimpath` - Remove file system paths from binary (reproducibility)

### When to Use CGO

✅ **Use static (CGO_ENABLED=0) if:**
- Pure Go code and dependencies
- Most web services, APIs, CLI tools

❌ **Use CGO (CGO_ENABLED=1) if:**
- Using `mattn/go-sqlite3` or other C library bindings
- Build fails with `CGO_ENABLED=0`

## Cache Mount Best Practices

### BuildKit Cache Mounts

Use cache mounts to speed up dependency installation:

```dockerfile
# Python/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# pnpm
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install

# npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Go modules
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Go build (with both module and build cache)
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app/server .
```

### Benefits

- **Faster builds**: Dependencies cached across builds
- **Lower bandwidth**: Don't re-download unchanged packages
- **CI-friendly**: Cache persists between workflow runs

## Lock File Management

### Always Commit Lock Files

```
✅ COMMIT:
- uv.lock
- bun.lockb
- pnpm-lock.yaml
- package-lock.json

❌ DO NOT COMMIT:
- node_modules/
- .venv/
- __pycache__/
```

### Use Frozen Lock Files in CI

```dockerfile
# Python/uv
uv sync --frozen  # Fail if lock file out of sync

# Bun
bun install --frozen-lockfile

# pnpm
pnpm install --frozen-lockfile

# npm
npm ci  # Clean install from lock file
```

## Dependency Updates

### Update Strategy

1. **Development**: Update dependencies locally
2. **Lock files**: Commit updated lock files
3. **CI**: Build validates lock files work
4. **Production**: Deploy with frozen dependencies

### Security Updates

- Run dependency audits: `uv pip check`, `npm audit`, `pnpm audit`
- Use Dependabot or Renovate for automated updates
- Test updates in CI before merging:
