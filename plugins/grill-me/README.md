# grill-me

A relentless interview to stress-test and sharpen a plan or design before building.

Adapted from [Matt Pocock's `grill-me` / `grilling` skills](https://github.com/mattpocock/skills/tree/main/skills/productivity),
consolidated into a single skill with structured question dimensions and convergence signals.

## ✨ Recent Improvements (v0.0.1)

- Initial release: single-skill consolidation of Matt Pocock's `grill-me` + `grilling`
- `disable-model-invocation: true` — explicit `/grill-me` trigger only, no spurious auto-invocation
- Keeps the original power (one-question-at-a-time, recommended answers, codebase-first,
  no execution before shared understanding)
- Adds question dimensions (goal / scope / assumptions / dependencies / edge cases /
  alternatives / risk) so no facet is left unexamined
- Adds explicit convergence signals before enactment

## What it does

When you invoke `/grill-me`, Claude interviews you relentlessly about every aspect of your plan or design:

- **One question at a time** — waits for your answer before continuing; never overwhelms with multiple questions at once.
- **Recommended answers** — each question comes with a recommended answer to guide your thinking.
- **Codebase-first** — if a question can be answered by exploring the codebase, Claude explores it instead of asking you.
- **Walks the design tree** — resolves dependencies between decisions one by one, branch by branch.
- **No premature execution** — Claude will not enact the plan until you confirm a shared understanding.

## When to use

- Before building a feature, to stress-test the design
- When a plan feels hand-wavy and needs pressure
- To surface hidden assumptions and dependencies
- To make sure no branch of the design tree is left unexamined

## Usage

```
/grill-me <paste your plan or describe your idea>
```

Trigger phrases containing "grill" also activate it.

## Attribution

Based on [mattpocock/skills](https://github.com/mattpocock/skills) — `grill-me` and `grilling` skills.
MIT-style adaptation; original credit to Matt Pocock.
