---
name: review
description: Run the orc AI review over the current diff — four parallel review agents plus /code-review — then process findings. Runs standalone, and is the shared review step invoked by /orc:build and /orc:push. No code reaches a PR without it.
model: sonnet
---

Review the working branch's diff for correctness, security, quality, and impact, then handle what it finds. This skill is the single source of truth for "AI review" across orc — `build` and `push` both invoke it so every change headed for `main` is reviewed the same way.

## Inputs

Callers (`build`, `push`) pass what they have; standalone runs infer sensible defaults:

- **base** — the ref to diff against. Default `main`.
- **spec** — the issue's Spec comment, if any. Optional for standalone runs.
- **impl notes** — notes the builder recorded about non-obvious choices. Optional.
- **mode** — `autonomous` when `ORC_AUTONOMOUS=1`, else `interactive`.

## Steps

### 1. Gather the diff

```bash
git diff {base}...HEAD
git diff {base}...HEAD --name-only
```

If the diff is empty, report "Nothing to review" and stop.

### 2. Run the review agents in parallel

Invoke all four in parallel, passing each the **spec (if any), impl notes (if any), and the full diff** — never the build conversation, so each reviews the code with fresh eyes:

- `review-correctness` — acceptance criteria, scope drift, logic errors
- `review-security` — injection, auth gaps, data exposure, insecure defaults
- `review-quality` — complexity, pattern consistency, test coverage
- `review-impact` — breaking changes, side effects, performance, **destructive/irreversible migrations**

Each returns findings tagged `BLOCKER`, `WARNING`, or `NOTE`.

### 3. Add an independent pass

Run `/code-review` over the same diff as a fifth, independent perspective. If it isn't available in this environment, note that and continue with the four agents.

### 4. Classify

Collect every finding into three buckets: **BLOCKERS**, **WARNINGS**, **NOTES**. A finding counts as a BLOCKER if any agent marks it so.

### 5. Auto-fix the safe ones

For findings that are unambiguous and clearly safe to fix (lint, missing import, type error, obvious typo, dead code the diff introduced), apply the fix directly. Do **not** auto-fix anything that changes behavior, touches logic the spec depends on, or is larger than a trivial correction. Commit auto-fixes together:

```bash
git commit -am "fix: address review findings"
```

Mark each auto-fixed finding as resolved (`~~finding~~ — fixed in {sha}`).

### 6. Emit the review summary

Fill in `${CLAUDE_PLUGIN_ROOT}/skills/review/templates/ai-review.md` with each section's status and findings. This is the body `build`/`push` post as the PR's AI-review comment.

### 7. Hand off

- **Called by `build`/`push`:** return the residual (non-auto-fixed) **BLOCKER** list plus the summary. The caller decides what to do — `build` treats a residual blocker as its Review-blocker gate.
- **Standalone, interactive:** present BLOCKERS then WARNINGS and offer, per finding, `(f) fix  (r) reply/defer`. Apply confirmed fixes and commit.
