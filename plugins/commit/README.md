# commit Plugin

Smart git commit workflow with conventional commits and GPG signing.

## Skills

- `/commit` — Create well-formatted commits with conventional commits format,
  staged/unstaged detection, multi-concern split suggestions, and GPG signing
- `/commit-push-pr` — Commit, push, and open a PR end-to-end in one step

## Recent Improvements (v0.0.2)

- Added live git context injection (status, diff, branch, recent commits auto-loaded on invoke)
- Added `/commit-push-pr` skill: commit + push + `gh pr create` in a single workflow
- Added `Bash(gpg *)` to allowed-tools for explicit GPG passphrase caching support
- Removed emoji prefix from commit format (`<type>: <description>` — no emoji)
