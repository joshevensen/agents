---
name: push
description: Commit uncommitted changes with a real message, run the AI review, push, and open a PR — no merge. Use for manual edits that don't warrant a full /orc:create + /orc:build cycle.
model: sonnet
---

`push` is the quick, local sibling of `build`: for changes you made by hand rather than through a spec. It always runs the AI review before anything reaches a PR — that's non-negotiable, since review is what catches bugs headed for `main`, spec or no spec. It never merges.

## Steps

### 1. Preflight

```bash
git status --short
git diff --stat
```

If the working tree is clean, report `Nothing to commit — working tree is clean.` and stop.

### 2. Size check

Inspect the full diff (`git diff`). If it's large or risky — 50+ lines, new files, touches config/migrations/auth/billing/routing/env vars, spans 3+ files, or has real logic changes (not cosmetic) — say so and suggest `/orc:create` + `/orc:build` instead, which get you a spec and gated review. Wait for explicit confirmation (`proceed anyway`) before continuing. Pure cosmetic/copy/whitespace diffs skip this.

### 3. Commit message

Use `{message}` verbatim if supplied. Otherwise draft a short, imperative one (50 chars max) from the diff and confirm it with the user before proceeding.

### 4. Branch

If on `main`/`master`, branch: `git checkout -b quick/{slug}` (slug from the message, lowercase, hyphens, max 40 chars). If already on a non-main branch, stay on it.

### 5. Commit and push

```bash
git add -A
git commit -m "{message}"
git push -u origin HEAD
```

### 6. Review

Invoke `/orc:review` with base `main`. It auto-fixes safe findings itself and commits them (`fix: address review findings`). For residual BLOCKERs and WARNINGs, work through them interactively (`review` offers `(f)/(r)` per finding when run standalone):

**`(f)` — Fix:** show the exact edit, confirm, apply, then commit:
```bash
git commit -am "fix: {brief description of the finding}"
```

**`(r)` — Reply/defer:** note it for the PR body, no commit.

Once every finding is resolved or deferred, push whatever `review` and this step committed:
```bash
git push
```
Do not open the PR before this push — otherwise fixes stay local-only and the PR won't reflect them.

### 7. Open PR

```bash
gh pr view --json number,url 2>/dev/null
```

If none exists, create one:
```bash
gh pr create --title "{message}" --body "{ai-review summary from step 6}" --base main
```

### 8. Merge readiness

**CI:**
```bash
gh pr checks {pr} --watch
```
If a check fails, fetch the log and diff, invoke `ci-debugger`, and confirm the fix with the user before applying (this is interactive — don't auto-apply silently). Commit, push, re-watch.

**Mergeability:**
```bash
gh pr view {pr} --json mergeable --jq .mergeable
```
If `CONFLICTING`: rebase onto `origin/main`, invoke `conflict-classifier`, resolve simple conflicts, surface complex ones to the user. Push `--force-with-lease`.

### 9. Report

```
PR open — {pr-url}
Reviewed, CI green, mergeable. Merge it yourself when ready.
```
