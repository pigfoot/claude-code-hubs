# secure-container-build

Build secure container images with Wolfi runtime, non-root users, and multi-stage builds.

## Features

- **Security-first runtime**: Wolfi distroless images with minimal attack surface and no CVEs
- **Non-root containers**: Run as UID 65532 by default
- **Multi-stage builds**: Minimal runtime images with only necessary artifacts
- **Production & debug variants**: Switch between secure production and debug-friendly images
- **Allocator optimization**: mimalloc support for Rust builds

## Supported Stacks

| Stack | Containerfile | Runtime Image |
|-------|--------------|---------------|
| Python + uv | `Containerfile.python-uv` | glibc-dynamic |
| Bun | `Containerfile.bun` | glibc-dynamic |
| Node.js + pnpm | `Containerfile.nodejs` | glibc-dynamic |
| Golang (static) | `Containerfile.golang` | static |
| Golang (CGO) | `Containerfile.golang-cgo` | glibc-dynamic |
| Rust (glibc) | `Containerfile.rust` | glibc-dynamic |
| Rust (musl) | `Containerfile.rust-musl` | static |

## Quick Start

```bash
# Install the plugin
/plugin install secure-container-build@pigfoot

# Copy template for your stack
cp assets/Containerfile.python-uv ./Containerfile

# Build production image
podman build -t myapp:latest .

# Build debug image (with shell)
podman build --build-arg RUNTIME_TAG=latest-dev -t myapp:debug .
```

## Usage

Ask Claude to set up secure container builds for your project:

- "Create a secure Containerfile for my Python app"
- "Set up a multi-stage build for my Rust project"
- "Help me optimize my container image size"

## Related

For CI/CD automation with GitHub Actions, see the **github-actions-container-build** plugin.

## Version

0.0.1
