---
name: commit
description: Smart commit creation with conventional commits and GPG signing. Use when user says "commit" or requests committing changes. Handles staged file detection, suggests splits for multi-concern changes, and applies proper commit format.
allowed-tools: "Bash(git *), Bash(gpg *)"
version: 0.0.2
---

# Commit Skill

Creates well-formatted commits following conventional commit standards.

## When to Use

- User says "commit", "commit these changes", or uses `/commit`
- After code changes are ready to be committed
- Need help with commit message formatting
- Want automatic detection of multi-concern changes

## Core Features

- **GPG signing** with cached passphrase (if `$GPG_PASSPHRASE` set)
- **Staged vs unstaged detection** - commits only staged files when present
- **Split suggestions** - analyzes diffs for multiple logical changes
- **Conventional commits** - `<type>: <description>` format
- **Pre-commit hook integration** - respects Husky/other hooks
- **Always --signoff** - DCO compliance

---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

---

## Process

### ⚠️ CRITICAL: ALWAYS start with Step 1 (Environment Check) before attempting any commit

### 1. Environment Check (MANDATORY FIRST STEP)

#### MUST cache GPG passphrase if available

```bash
# If GPG_PASSPHRASE is set, cache it to gpg-agent
if [ -n "$GPG_PASSPHRASE" ]; then
  gpg --batch --pinentry-mode loopback \
      --passphrase-file <(echo "$GPG_PASSPHRASE") \
      --clearsign >/dev/null 2>&1 <<< "test" && echo "✅ GPG passphrase cached" || echo "❌ GPG cache failed"
else
  echo "⚠️  GPG_PASSPHRASE not set - GPG signing will prompt for passphrase (and fail in non-interactive environment)"
fi
```

#### Why this matters

- GPG_PASSPHRASE purpose: Allow GPG to sign automatically without interactive password prompt
- If GPG_PASSPHRASE is set → **Must cache first**, otherwise git commit --gpg-sign will fail
- If GPG_PASSPHRASE not set → GPG will attempt interactive password prompt (fails in Claude Code environment)

#### GPG signing decision

- Whether to use --gpg-sign should be determined by project policy or git config
- In this project: **always use --gpg-sign** (assumes GPG is configured)

#### When committing

```bash
# Always use --gpg-sign (passphrase is cached if GPG_PASSPHRASE was set)
git commit --signoff --gpg-sign -m "..."
```

### 2. Analyze Changes

```bash
git status --short

# Prefer staged files if any exist
if ! git diff --staged --quiet; then
  git diff --staged --stat    # Staged changes
else
  git diff HEAD --stat        # All changes
fi
```

### 3. Multi-Concern Detection

Suggest split if:

- **Different patterns**: `src/` + `test/` + `docs/`
- **Mixed types**: feat + fix + docs
- **Unrelated concerns**: auth logic + UI styling
- **Large changeset**: >500 lines

#### Ask user

```
Multiple concerns detected:
1. Auth changes (src/auth/*)
2. UI updates (src/components/*)
3. Docs (README.md)

Split into 3 commits?
- feat: add JWT authentication
- style: update login UI
- docs: update auth documentation

[split/all]
```

### 4. Create Commit

Format: `<type>: <description>`

#### Rules

- Imperative mood ("add" not "added")
- First line <72 chars
- Atomic (single purpose)
- Use body for "why" if needed

```bash
git commit --signoff ${USE_GPG:+--gpg-sign} -m "<type>: <description>"
```

### 5. Handle --no-verify

If user requests `--no-verify`:

```
⚠️  Requested to skip pre-commit hooks.

Bypasses: linting, tests, formatting
Reason: [ask user]

Approve? [yes/no]
```

Only proceed if confirmed.

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
| revert | Revert changes |
| wip | Work in progress |

---

## Split Decision Examples

### ❌ Bad - Mixed concerns

```diff
+ src/auth/login.ts (feat)
+ src/components/Button.css (style)
+ README.md (docs)
```

**Split into:** 3 separate commits

### ✅ Good - Single concern

```diff
+ src/auth/login.ts
+ src/auth/middleware.ts
+ tests/auth.test.ts
```

**One commit:** `feat: add authentication`

### ❌ Bad - Mixed types

```diff
+ Add export feature (feat)
+ Fix date bug (fix)
```

**Split into:** 2 commits by type

### ❌ Bad - Large multi-feature

```diff
300+ lines: auth system
200+ lines: UI components
150+ lines: database
```

**Split into:** 3 commits by feature

---

## Critical Rules

### NEVER

- ❌ Add Claude signature to commits
- ❌ Commit without checking staged status
- ❌ Skip split suggestions for multi-concern
- ❌ Use past tense ("added" → "add")
- ❌ Make first line >72 chars
- ❌ Bypass hooks without asking
- ❌ **Attempt git commit before running GPG cache command**

### ALWAYS

- ✅ **FIRST: Run Environment Check (Step 1) to cache GPG passphrase**
- ✅ Use --signoff flag (always)
- ✅ Use --gpg-sign flag (always, passphrase is cached in Step 1)
- ✅ Analyze diff before commit
- ✅ Suggest splits when appropriate
- ✅ Use imperative mood
- ✅ Pick correct type
- ✅ Ask approval for --no-verify

---

## Integration Notes

### With CLAUDE.md

CLAUDE.md references this skill: "Use `/commit` or say 'commit changes'"

### With spec-kit

Reference planning docs in commit body:

```
feat: add user authentication

- JWT token validation
- Protected routes middleware
- Tests cover happy/error paths

Related to Stage 2 of PLAN.md (User Story 1.2)
```

### With Husky

Hooks run automatically unless --no-verify used (requires approval).

---

## Example Sessions

### Simple commit

```
User: "commit these changes"

Process:
1. Check GPG ✓
2. Analyze: src/auth/login.ts (modified)
3. Single concern ✓
4. Create: feat: add login endpoint
5. Execute: git commit --signoff --gpg-sign -m "..."
```

### Split required

```
User: "commit"

Process:
1. Detect: auth + UI + docs
2. Suggest split (3 commits)
3. User confirms "split"
4. Commit each separately with proper type
```

### Skip hooks

```
User: "/commit --no-verify"

Response:
"⚠️ Skip hooks? Bypasses linting/tests.
Reason: [wait]"

User: "hotfix for production"

Action: Proceed with --no-verify
```

---

## Troubleshooting

### GPG fails

```bash
echo $GPG_PASSPHRASE  # Check set
gpg --clearsign <<< "test"  # Test manually
# If fails: commit without --gpg-sign
```

### Hook fails

Check output → fix issue → retry
Critical case only: ask about --no-verify

### No changes

```bash
git status
# No changes: inform user
# Unstaged only: "Stage files first?"
```

---

## Progressive Disclosure

Keep this main file under 500 lines. For extensive reference:

- Emoji cheatsheet → See `emoji-reference.md` (if needed)
- Advanced patterns → See `advanced-commits.md` (if needed)

Current approach: All essential info in this file for immediate use.

---
