---
name: build
description: Take a specced issue from spec to open PR — decompose into a dependency-ordered task list, execute it (parallel subagents where tasks are independent), verify with focused tests, AI-review, and open the PR. Never merges. Invoke as /orc:build {number}.
model: sonnet
---

`build` takes one specced issue and drives it to an open, AI-reviewed PR for you
to merge. An issue of any size is built in one `build` run producing one PR —
there is no size gate. A draft PR opens right after branching (step 5) so you
can watch the diff land wave by wave; it's marked ready for review only once
implementation is done (step 9), which is also the earliest point `/orc:resume`
is allowed to act — before that, the implementation itself is still in
question, so a gate means a full rebuild, not a resume. When it can't safely
continue, it stops at a **gate**: commits and pushes whatever exists, comments
on the issue explaining why, sets `status:blocked`, and stops.

Everything project-specific — how to verify — comes from the repo's `CLAUDE.md`.
This skill hardcodes nothing about any one project.

## `--dry-run`

`/orc:build {number} --dry-run` runs everything through implementation,
verification, and review exactly as normal, including local git — the branch
is created and each wave is committed locally, so `git log` / `git diff
origin/main...HEAD` show real, inspectable output. It stops being "real" at
the network boundary: skip the `gh issue edit` label changes in steps 5 and
12, skip every `git push` (steps 8, 10, 11 — step 5 itself never pushes, it
only branches and opens the PR), and skip every `gh pr` call in steps 5, 9,
and 10 (create, edit, ready, comment) — print what each would have sent
instead. Step 12 (CI watch, mergeability, the label flip) needs a real,
pushed PR to check against, so there's nothing genuine to run there. End with:
```
DRY RUN — {n} wave(s) committed locally on branch {branch}, not pushed. Would
open a draft PR "{title}", mark it ready for review, and post an AI review.
Re-run without --dry-run to push and open it.
```
Gates still trip on real problems (spec, confidence, ambiguity, focused
verification, review blockers) — dry-run previews the push/PR boundary, it
doesn't skip validation.

## Gate procedure

Referenced throughout as "**gate: {name}**". When a gate trips:

1. Commit and push whatever exists on the branch (so it's inspectable) —
   unless nothing was built yet.
2. Comment on the issue. The recovery command depends on whether the PR has
   reached ready-for-review (step 9):
   ```
   🚧 Build paused: {gate name}

   {specific reason}

   What's needed: {the concrete fix}
   Resume: fix the above, then re-run `/orc:resume {number}` (continues from the reviewed PR).
   ```
   or, if the PR is still draft (implementation not yet complete — a full
   rebuild is correct here, not a resume):
   ```
   🚧 Build paused: {gate name}

   {specific reason}

   What's needed: {the concrete fix}
   Resume: fix the above, then re-run `/orc:build {number}` (it resets to origin/main and rebuilds from scratch — the draft PR is reused, not recreated).
   ```
3. Create the label defensively first (idempotent — a no-op if it already
   exists), then apply it:
   ```bash
   gh label create "status:blocked" -f >/dev/null 2>&1 || true
   gh issue edit {number} --remove-label "status:building" --add-label "status:blocked"
   ```
4. Stop.

If the user is actively in the loop, a gate may instead surface the problem and
offer to resolve it inline rather than pausing-and-exiting.

## Steps

### 0. Resolve target

Require an issue number (`^\d+$`) as `{number}`. If none is given, stop and ask
which issue to build.

### 1. Load

Invoke `issue-loader` with `{number}`. Use the returned title, slug, labels,
status, body, and spec comment.

Expect `status:ready`. If `status:blocked` or `status:building` from a prior
run, continue (this run resets the branch) — but if a PR already exists for
this issue **and it's marked ready for review**, `/orc:resume {number}` is
almost always what's wanted instead: it continues from the reviewed PR rather
than redoing real work. If the PR is still draft, there's nothing finished to
resume — a full `/orc:build` rebuild is correct. If `status:draft`: **gate:
spec** (no spec yet — run `/orc:plan {number}`).

### 2. Gate: spec

Validate the spec comment against `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`.
Three conditions must hold:

1. A `## Spec` comment exists.
2. Every **Acceptance Criterion** is machine-verifiable — tied to a test,
   command, or observable outcome (not "looks right").
3. **Open Questions** reads `None.`

If any fail, **gate: spec** naming the specific criteria that can't be checked or
the questions still open. Point the user to `/orc:plan {number}` to (re-)spec.

### 3. Gate: confidence

Read the spec's touchpoints and locate the real files in the codebase. If there
is material ambiguity — a named file/symbol doesn't exist, two readings of a
criterion would produce different code, an unstated dependency blocks the work —
**gate: confidence**, listing the exact unknowns to resolve. Confidence is
judged on concrete facts, not a numeric score, and it is **not** a size check:
a large but well-specified issue passes. Only genuine ambiguity gates here.

### 4. Gate: missing infra

If `CLAUDE.md` has no `## Verification` section (and no `## Focused Verification`
section), there is no way to prove the build is sound → **gate: missing infra**
(run `/orc:setup`).

### 5. Branch + draft PR

Always start from a clean base so reruns are deterministic:

```bash
git fetch origin main
git switch -C issue/{number}-{slug} origin/main
gh label create "status:building" -f >/dev/null 2>&1 || true
gh issue edit {number} --remove-label "status:ready,status:blocked" --add-label "status:building"
```

`switch -C` force-recreates the branch even if a previous run already pushed
commits to it — that's deliberate, so a rerun of `/orc:build` (as opposed to
`/orc:resume`) always starts genuinely clean.

Open a draft PR immediately so the diff is visible as waves land, or reuse one
left over from a previous run of this same issue:

```bash
existing=$(gh pr list --head "issue/{number}-{slug}" --state open --json number,isDraft --jq '.[0]')
```

- **No open PR** — create one, in draft, with a placeholder body (the real
  implementation notes go in at step 9):
  ```bash
  pr_url=$(gh pr create --draft --base main --title "{title}" --body "🚧 Build in progress. Closes #{number}.")
  pr=$(basename "$pr_url")
  ```
  `gh pr create` has no `--json` — it prints only the URL, so read `{pr}` back
  from that.
- **An open PR already exists** — reuse it (`pr` = its number). If it isn't
  already draft, put it back — its branch is about to be wiped and redone, so
  its state has to match:
  ```bash
  gh pr ready {pr} --undo 2>/dev/null || true
  ```

Post the PR URL as an issue comment.

### 6. Plan the task list

Decompose the spec into a **task list with a dependency graph**. For each task,
note the files it will touch and which other tasks it depends on. A real
dependency is a decision or artifact one task produces that another needs (a
schema settled in task 2 that task 4 builds on) — not mere thematic similarity.

Group the tasks into waves:

- **Independent tasks** (no unmet dependency, and — ideally — disjoint file
  sets) run in **parallel**, one subagent each.
- **Dependent tasks** run **after** the tasks they depend on, in sequence.

Where two otherwise-independent tasks **share a file**, either serialize them
(same wave, but one after the other) or run them in isolated git worktrees and
reconcile the file before the integration pass. Never let two parallel subagents
write the same file concurrently.

### 7. Execute the waves

For each wave, dispatch its tasks:

- **Parallel** independent tasks via subagents (the Task/general-purpose agent),
  one per task, launched together. Give each subagent the spec, its specific
  task, the exact files it owns, and an instruction to touch nothing outside
  them.
- **Match the model to the task's complexity:** dispatch mechanical or
  repetitive edits (rename, boilerplate, config) with a cheaper/faster model, and
  logic-heavy or design-sensitive work with a stronger model. Set the model per
  subagent at dispatch.
- **No guessing.** If a task is ambiguous, incomplete, or conflicts with the
  codebase, stop that work and **gate: ambiguity** with the exact question and
  the options you see.

After each wave, integrate the results (resolve any worktree reconciliation),
then run **focused verification and commit** (step 8) before starting the next
wave. Keep a short running list of non-obvious choices and discovered
constraints across all waves — this becomes the PR body's implementation notes
at step 9.

### 8. Focused verification + commit per wave

Verification defaults to **scoped/filtered** test runs — never the full suite.
After each wave, run only the tests covering what that wave changed: the test
file(s) a task touched, or the domain around a shared file it modified.

Prefer the command in `CLAUDE.md`'s **`## Focused Verification`** section (a
PHPUnit `--filter`, `pytest -k`, a JS test-path arg, etc. — necessarily
per-repo). If that section is absent, derive a narrow invocation from
`## Verification` by scoping it to the touched paths. **Never run the whole
suite** — that is CI's job (step 12).

If `CLAUDE.md` has a **`## CI-Only Verification`** section, never run anything
it lists, in any form — those suites (typically slow, browser-driven e2e) are
left to CI entirely.

If a focused command fails and the fix isn't a trivially safe correction,
**gate: gate/verify** with the failing command and output. If a command can't
run (missing binary/env), record it and continue.

Once a wave's focused verification passes, commit and push it immediately —
this is what makes the draft PR's diff update live as the build progresses.
Stage only files that wave changed (never `git add .` blindly):

```bash
git add {wave's files}
git commit -m "feat(#{number}): {wave summary}"
git push
```

### 9. Ready for review

All waves are implemented, verified, and pushed. Before review, replace the
PR's step-5 placeholder with the real thing:

```bash
gh pr edit {pr} --title "{title}" --body "{implementation notes}

Closes #{number}."
gh pr ready {pr}
```

Marking the PR ready for review **here** — not after review passes — is the
signal `/orc:resume` checks: a draft PR means implementation isn't finished
(resume refuses); ready-for-review means it is, and only review/CI/mergeability
are left (resume can continue from there).

### 10. Review (folded in)

Review the branch's full diff against `origin/main`. Refresh it first
(`git fetch origin main`) — the waves and verification above take time, so
`origin/main` may have moved since step 5. Run all five agents **in
parallel**, passing each the spec, your implementation notes, and the full
diff (`git diff origin/main...HEAD`) — never the build conversation, so each
reviews with fresh eyes:

- `review-correctness` — acceptance criteria, scope drift, logic errors
- `review-security` — injection, auth gaps, data exposure, insecure defaults
- `review-quality` — complexity, pattern consistency, test coverage
- `review-impact` — breaking changes, side effects, performance regressions
- `deploy-risk-scanner` — migrations, env vars, job schema, webhook/API changes

Each review agent tags findings `BLOCKER`, `WARNING`, or `NOTE`.
`deploy-risk-scanner` returns a risk level — treat `HIGH` as a `BLOCKER`, `low`
as a `NOTE`. Then run `/code-review` over the same diff as a sixth, independent
pass; if it isn't available here, note that and continue with the five agents.

**Auto-fix the safe ones** — lint, missing import, type error, obvious typo,
dead code the diff introduced. Never auto-fix anything that changes behavior or
touches logic the spec depends on. Commit and push auto-fixes together
(`fix: address review findings`) and re-run focused verification on what they
touched.

Fill `${CLAUDE_PLUGIN_ROOT}/templates/ai-review.md` with each section's status
and findings, capture the current commit (`git rev-parse HEAD` — after any
auto-fix commit above) for the template's `sha:` marker, and post it as a **PR
comment** — never fold review content into the PR description:

```bash
gh pr comment {pr} --body-file {filled-template}
```

The `sha:`/`verdict:` marker line is load-bearing: it's how `/orc:resume`
tells a still-fresh review apart from a stale one. If a residual **BLOCKER**
remains after safe auto-fixes, **gate: review blocker** with the finding —
the posted comment's `verdict:BLOCK` is what a later `/orc:resume` will see.
Warnings are noted in the comment and do not block.

### 11. Docblocks + changelog

Update file-level docblocks for changed files. If the repo keeps a
`CHANGELOG.md`, invoke `changelog-writer` and insert its entry at the placement
it specifies — its output leads with a `Placement:` line naming exactly where
the blocks go (an existing `## [Unreleased]` section, a new version heading,
etc.). Commit and push any changes.

### 12. Merge readiness

"Ready for review" isn't useful if it's red or unmergeable — check both before
reporting done. Neither step merges. **This is where the full test suite
runs** — CI is the authoritative full-suite check that focused local runs
deliberately leave to it.

**CI:**
```bash
gh pr checks {pr} --watch
```
If a check fails, fetch its log (`gh run view {run-id} --log-failed`) and the
diff, invoke `ci-debugger`, and apply the fix only if it's clearly safe (missing
import, type error, lint, fixture update). Commit (`fix(#{number}): fix CI —
{reason}`), push, re-watch. If the fix isn't safe or checks still fail after one
attempt, **gate: gate/verify** with the failing check and diagnosis.

**Mergeability:**
```bash
gh pr view {pr} --json mergeable --jq .mergeable
```
If `CONFLICTING`: `git fetch origin && git rebase origin/main` to surface
markers, invoke `conflict-classifier`. Auto-resolve files it marks simple,
stage, `git rebase --continue`, then `git push --force-with-lease`. If any file
is marked complex, **gate: gate/verify** with the conflicting sections.

**Once CI is green and the PR is mergeable**, the issue is genuinely built —
only now flip the label:
```bash
gh label create "status:built" -f >/dev/null 2>&1 || true
gh issue edit {number} --remove-label "status:building" --add-label "status:built"
```
Setting this any earlier risks a gate firing after `status:building` has
already been replaced — the gate procedure's label swap would then have
nothing to remove, leaving `status:built` and `status:blocked` on the issue at
the same time.

### 13. Report

```
PR open for #{number} — {pr-url}
CI green, mergeable, {n} warning(s) noted. Ready for your merge.
```
