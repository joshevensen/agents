---
name: push
description: Commit uncommitted changes with a real message, run the AI review, push, and open a PR — no merge. Use for manual edits that don't warrant a full /orc:create + /orc:build cycle.
model: sonnet
---

`push` is the quick, local sibling of `build`: for changes you made by hand rather than through a spec — seeing the code directly, not going through `create`/`plan`/`build`. It always runs the AI review before anything reaches a PR — that's non-negotiable, since review is what catches bugs headed for `main`, spec or no spec. It never merges.

## `--dry-run`

`/orc:push --dry-run` runs the size check, commits locally (step 5), and runs
the full AI review (step 6) exactly as normal — real commits on a real local
branch, inspectable with `git log` / `git diff origin/main...HEAD`. It skips
`git push` in step 5 and every step afterward that needs a pushed branch: no
`git push` after review fixes, no `gh pr create` in step 7 (print the title
and body it would have used instead), and step 8 (CI, mergeability) has
nothing real to check without a pushed PR, so skip it and say so. End with:
```
DRY RUN — {n} commit(s) on local branch {branch}, not pushed. Would open PR:
"{message}" against main. Re-run without --dry-run to push and open it.
```

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

Run the AI review over the diff against `origin/main` — the same orchestration
`build` folds in. Refresh it first (`git fetch origin main` — push never fetches
elsewhere, so this is the only chance), then gather the diff
(`git diff origin/main...HEAD`), and run all five agents in parallel, passing
each the full diff (and any notes you have — there's no spec):

- `review-correctness`, `review-security`, `review-quality`, `review-impact`
- `deploy-risk-scanner` — `HIGH` risk counts as a BLOCKER, `low` as a NOTE

Then run `/code-review` over the same diff as a sixth pass; if unavailable, note
it and continue. Fill `${CLAUDE_PLUGIN_ROOT}/templates/ai-review.md` with the
results for the PR body.

Auto-fix clearly safe findings (lint, missing import, type error, typo, dead
code the diff introduced) and commit them (`fix: address review findings`) —
never anything that changes behavior. For residual BLOCKERs and WARNINGs, work
through them interactively, `(f)` fix / `(r)` reply-defer per finding:

**`(f)` — Fix:** show the exact edit, confirm, apply, then commit:
```bash
git commit -am "fix: {brief description of the finding}"
```

**`(r)` — Reply/defer:** note it for the PR body, no commit.

Once every finding is resolved or deferred, push whatever review committed:
```bash
git push
```
Do not open the PR before this push — otherwise fixes stay local-only and the PR won't reflect them.

### 7. Open PR

```bash
pr=$(gh pr view --json number --jq .number 2>/dev/null)
```

If none exists, create one — `gh pr create` has no `--json`, it prints only
the URL, so read `{pr}` back from that:
```bash
pr_url=$(gh pr create --title "{message}" --body "{ai-review summary from step 6}" --base main)
pr=$(basename "$pr_url")
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
If `CONFLICTING`: `git fetch origin && git rebase origin/main` to surface markers, invoke `conflict-classifier`, resolve simple conflicts, surface complex ones to the user. Push `--force-with-lease`.

### 9. Report

```
PR open — {pr-url}
Reviewed, CI green, mergeable. Merge it yourself when ready.
```
