---
name: commit-push-pr
description: Commit changes, push to remote, and create a pull request in one step. Use when user wants to ship changes end-to-end. Handles GPG signing, branch creation if on main/master, and PR creation via gh CLI.
allowed-tools: "Bash(git *), Bash(gpg *), Bash(gh *)"
version: 0.0.2
---

# Commit Push PR Skill

Commits staged/unstaged changes, pushes to remote, and creates a pull request in a single workflow.

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

---

## Process

### ⚠️ CRITICAL: ALWAYS start with Step 1 (Environment Check) before attempting any commit

### 1. Environment Check (MANDATORY FIRST STEP)

Cache GPG passphrase if available:

```bash
if [ -n "$GPG_PASSPHRASE" ]; then
  gpg --batch --pinentry-mode loopback \
      --passphrase-file <(echo "$GPG_PASSPHRASE") \
      --clearsign >/dev/null 2>&1 <<< "test" && echo "GPG passphrase cached" || echo "GPG cache failed"
else
  echo "GPG_PASSPHRASE not set - GPG signing will prompt for passphrase"
fi
```

### 2. Branch Check

If currently on `main` or `master`, create a new branch first:

```bash
git checkout -b <descriptive-branch-name>
```

- Name based on changes: `feat/add-auth`, `fix/login-bug`, `docs/update-readme`
- Use a prefix matching the intended commit type

### 3. Analyze Changes

Use the context injected above (git status, diff, branch):

- Prefer staged files if any exist; otherwise stage all changes with `git add`
- For this skill: **single commit only** — if multi-concern, inform user and let them decide before proceeding

### 4. Create Commit

```bash
git add <relevant-files>
git commit --signoff --gpg-sign -m "<type>: <description>"
```

Conventional commit format: `<type>: <description>` (imperative mood, <72 chars)

### 5. Push

```bash
git push -u origin HEAD
```

### 6. Create PR

```bash
gh pr create --title "<commit-message>" --body "$(cat <<'EOF'
## Summary
- <key change 1>
- <key change 2>

## Test plan
- [ ] Verify <main behavior>
EOF
)"
```

- PR title = commit message (same text)
- Body: bullet summary of changes + basic test checklist
- Return the PR URL to the user

---

## Commit Types

| Type | Use Case |
|------|----------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation |
| style | Formatting, styling |
| refactor | Code restructure |
| perf | Performance |
| test | Tests |
| chore | Build/tools |
| ci | CI/CD |
| security | Security fix |
| build | Build system |

---

## Critical Rules

### NEVER

- ❌ Attempt git commit before GPG cache (Step 1)
- ❌ Push directly to `main`/`master` — always branch first
- ❌ Use past tense in commit message ("added" → "add")
- ❌ Make first line >72 chars
- ❌ Bypass hooks without asking

### ALWAYS

- ✅ **FIRST: Cache GPG passphrase (Step 1)**
- ✅ Create new branch if on main/master
- ✅ Use `--signoff --gpg-sign` on commit
- ✅ Push with `-u origin HEAD`
- ✅ Return PR URL to user after creation

---

## Example Session

```
User: "/commit-push-pr"

Process:
1. Cache GPG ✓
2. Context loaded: 3 files modified in src/auth/
3. On branch main → create feat/add-jwt-auth
4. Commit: feat: add JWT authentication
5. Push: git push -u origin HEAD
6. PR created: https://github.com/org/repo/pull/42
```
