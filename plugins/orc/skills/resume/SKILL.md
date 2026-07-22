---
name: resume
description: Continue a build that stopped after its PR reached ready-for-review — re-checks review freshness, then CI and mergeability, without redoing implementation. Use for a blocked issue past the review gate, not mid-implementation. Invoke as /orc:resume {number}.
model: sonnet
---

`build` always rebuilds from scratch on a rerun — deliberately, so every run is
deterministic. That's right whenever the PR is still **draft**: implementation
itself is still in question there (an ambiguity gate, a failed wave, an
unfinished review pass), and there's no saved per-wave state to resume into
safely. `resume` only ever acts once the PR is **marked ready for review** —
`build` sets that exactly once implementation is done, right before the review
step. Past that point, a gate means the code is fine and something downstream
failed: a review finding needing a second look, a CI flake, a merge conflict.
Rebuilding from scratch there re-does real, correct work to fix nothing.

## `--dry-run`

`/orc:resume {number} --dry-run` runs steps 1-3 exactly as normal (they're
read-only), and in step 4 actually runs the review agents if review turns out
stale (that's read-only until the final post) — local auto-fix commits still
happen so you can inspect them, but skip the `gh pr comment` post itself and
print what it would have said. In step 5, still watch CI and check
mergeability — those are read-only too. Skip only the mutations a real fix
would need: if CI fails, show `ci-debugger`'s diagnosis but don't commit/push
its fix; if the PR is `CONFLICTING`, show `conflict-classifier`'s
classification but don't rebase, resolve, or force-push; skip the final `gh
issue edit` to `status:built`. End with:
```
DRY RUN — PR #{pr}: review {fresh: PASS/BLOCK | stale, would re-review | none, would review}.
CI: {status, diagnosis if failing}. Mergeable: {status, classification if conflicting}.
Re-run without --dry-run to apply and resume.
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

### 2. Find the PR and check it's past the review gate

```bash
gh pr list --head "issue/{number}-{slug}" --state all \
  --json number,url,state,isDraft --jq '.[0]'
```

- **No PR found** — the previous run gated before step 5 of `build` (spec,
  confidence, or missing-infra). Nothing exists yet to resume into. Report
  this and point to `/orc:build {number}`. Stop.
- **PR found but `MERGED` or `CLOSED`** — `status:blocked` doesn't match
  reality (issue should be `status:built`, or the PR was closed by hand).
  Report the mismatch and stop rather than guessing what the user intended.
- **PR found, `OPEN`, but still `isDraft: true`** — implementation isn't
  finished (a gate before step 9 of `build`: ambiguity or a focused-verification
  failure mid-wave). There's real but incomplete work on the branch — resuming
  into it risks building on a decision that was never actually settled. Report
  this and point to `/orc:build {number}` (which reuses this draft PR rather
  than recreating it). Stop.
- **PR found, `OPEN`, `isDraft: false`** — implementation is done and the PR
  reached the review gate. Continue to step 3.

### 3. Check out the existing branch

Reuse the branch exactly as it stands — never recreate it (that would discard
the completed implementation this skill exists to preserve):

```bash
git fetch origin
git switch "issue/{number}-{slug}"
git fetch origin main
```

### 4. Check review freshness, re-review if needed

Look for the most recent AI-review comment and its `sha:`/`verdict:` marker
(see `${CLAUDE_PLUGIN_ROOT}/templates/ai-review.md`):

```bash
comment_body=$(gh pr view {pr} --json comments \
  --jq '[.comments[] | select(.body | test("<!-- orc:ai-review sha:"))] | last | .body')
review_sha=$(echo "$comment_body" | grep -oP 'sha:\K[a-f0-9]+')
review_verdict=$(echo "$comment_body" | grep -oP 'verdict:\K[A-Z]+')
head_sha=$(git rev-parse HEAD)
```

- **No such comment** — review never completed for the current implementation
  (a run crashed between step 9 and posting it). Treat as stale: run review.
- **`review_sha` == `head_sha`** — fresh. Trust it without re-running anything:
  - `verdict:PASS` (or `WARNING`) — skip straight to step 5.
  - `verdict:BLOCK` — nothing has changed since the blocker was found. Report
    it and stop; don't silently retry the same review. Either fix it and push
    a commit yourself, then re-run `/orc:resume`, or resolve it manually.
- **`review_sha` != `head_sha`** — stale: HEAD moved since that comment (a
  manual fix was pushed, or a prior resume attempt did). Re-review — this
  mirrors `build`'s steps 10-11 exactly, keep both in sync if either changes:
  run all five review agents plus `/code-review` in parallel against
  `git diff origin/main...HEAD`, auto-fix safe findings and re-verify, fill
  `ai-review.md` with the post-auto-fix `git rev-parse HEAD` as the new
  `sha:` marker, and post it via `gh pr comment` — never the PR description.
  Then run `changelog-writer`/docblocks the same way `build` step 11 does.
  If a residual BLOCKER remains, **gate: review blocker** (commit and push
  what exists, comment on the issue, `status:blocked`, stop). Otherwise
  continue to step 5.

### 5. Merge readiness

This mirrors `build`'s step 12 exactly — keep both in sync if either changes.

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

### 6. Report

```
PR resumed for #{number} — {pr-url}
CI green, mergeable. Ready for your merge.
```
