---
name: resume
description: Continue a build that stopped after its PR was already open — re-runs CI and mergeability without redoing implementation, review, or the PR itself. Use for a blocked issue where the block was an infra flake or a fix you've already applied, not a foundational problem. Invoke as /orc:resume {number}.
model: sonnet
---

`build` always rebuilds from scratch on a rerun — deliberately, so every run is
deterministic. That's right when the block is foundational (spec, confidence,
ambiguity, a review blocker mid-implementation): the branch that produced it
was wrong or incomplete, and there's no saved per-wave state to resume into
safely. `resume` covers the one case where a full rebuild is pure waste: the
PR is **already open**, meaning implementation, review, docblocks, and the
changelog all already succeeded — only the CI/mergeability tail failed. That
happens on a real regression, but also on infra flakes with no code fix at
all (a flaky runner, an environment mismatch between a remote session and CI).
Rebuilding from scratch re-does everything to fix nothing.

## `--dry-run`

`/orc:resume {number} --dry-run` runs steps 1-3 exactly as normal (they're
read-only) and, in step 4, still watches CI and checks mergeability — those
are read-only too. Skip only the mutations a real fix would need: if CI fails,
show `ci-debugger`'s diagnosis but don't commit/push its fix; if the PR is
`CONFLICTING`, show `conflict-classifier`'s classification but don't rebase,
resolve, or force-push; and skip the final `gh issue edit` to `status:built`.
End with:
```
DRY RUN — PR #{pr}: {CI status, diagnosis if failing} / {mergeable status,
classification if conflicting}. Re-run without --dry-run to apply and resume.
```

## Steps

### 0. Resolve target

Require an issue number (`^\d+$`) as `{number}`. If none is given, stop and
ask which issue to resume.

### 1. Load and classify

Invoke `issue-loader` with `{number}`. Use the returned slug and status.

- **`status:built`** — already done. Report and stop.
- **`status:ready` / `status:draft` / `status:building`** — no blocked run to
  resume. If `status:building`, a build may currently be in progress elsewhere;
  otherwise there's nothing to continue. Stop.
- **`status:blocked`** — continue to step 2.

### 2. Find the PR

```bash
gh pr list --head "issue/{number}-{slug}" --state all \
  --json number,url,state,headRefName --jq '.[0]'
```

- **No PR found** — the previous run stopped before step 12 of `build`
  (spec, confidence, missing-infra, ambiguity, focused-verification, or a
  review-blocker gate). There's no completed implementation to resume into.
  Report this and point to `/orc:build {number}` for a full rebuild. Stop.
- **PR found but `MERGED` or `CLOSED`** — status:blocked doesn't match reality
  (issue should be `status:built`, or the PR was closed by hand). Report the
  mismatch and stop rather than guessing what the user intended.
- **PR found and `OPEN`** — continue to step 3.

### 3. Check out the existing branch

Reuse the branch exactly as it stands — never recreate it (that would discard
the completed implementation this skill exists to preserve):

```bash
git fetch origin
git switch "issue/{number}-{slug}"
git fetch origin main
```

### 4. Re-run merge readiness

This mirrors `build`'s step 13 exactly — keep both in sync if either changes.

**CI:**
```bash
gh pr checks {pr} --watch
```
If a check fails, fetch its log (`gh run view {run-id} --log-failed`) and the
diff, invoke `ci-debugger`, and apply the fix only if it's clearly safe
(missing import, type error, lint, fixture update, a CI-config/environment
fix for an infra flake). Commit (`fix(#{number}): fix CI — {reason}`), push,
re-watch. If the fix isn't safe or checks still fail after one attempt,
**gate: gate/verify** with the failing check and diagnosis — same gate
procedure as `build` (commit and push what exists, comment on the issue,
`status:blocked`, stop).

**Mergeability:**
```bash
gh pr view {pr} --json mergeable --jq .mergeable
```
If `CONFLICTING`: `git fetch origin && git rebase origin/main` to surface
markers, invoke `conflict-classifier`. Auto-resolve files it marks simple,
stage, `git rebase --continue`, then `git push --force-with-lease`. If any
file is marked complex, **gate: gate/verify** with the conflicting sections.

**Once CI is green and the PR is mergeable:**
```bash
gh issue edit {number} --remove-label "status:building,status:blocked" --add-label "status:built"
```

### 5. Report

```
PR resumed for #{number} — {pr-url}
CI green, mergeable. Ready for your merge.
```
