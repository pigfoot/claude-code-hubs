# github-actions-container-build

Build multi-architecture container images in GitHub Actions using Podman and native ARM64 runners.

## Features

- **Matrix builds**: Native ARM64 runners for public repos (10-50x faster than QEMU)
- **QEMU fallback**: Free emulation for private repos on GitHub Free tier
- **Podman rootless**: Secure, daemonless container builds
- **Multi-arch manifests**: Single tag for amd64 and arm64
- **Retry logic**: Automatic retries for transient failures

## Workflow Options

| Workflow | Use Case | Speed |
|----------|----------|-------|
| `github-actions-workflow-matrix-build.yml` | Public repos | Fast (native) |
| `github-actions-workflow-qemu.yml` | Private repos (free tier) | Slow (emulated) |

## Quick Start

```bash
# Install the plugin
/plugin install github-actions-container-build@pigfoot

# For public repos (native ARM64)
cp assets/github-actions-workflow-matrix-build.yml .github/workflows/build.yml

# For private repos (QEMU)
cp assets/github-actions-workflow-qemu.yml .github/workflows/build.yml
```

## Usage

Ask Claude to set up CI/CD for your container builds:

- "Set up GitHub Actions for multi-arch container builds"
- "I need a workflow to build ARM64 images for my public repo"
- "Create a container build pipeline for my private repository"

## Related

For Containerfile templates and security best practices, see the **secure-container-build** plugin.

## Version

0.0.1
