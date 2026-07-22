---
name: build
description: Take a specced issue from spec to open PR — decompose into a dependency-ordered task list, execute it (parallel subagents where tasks are independent), verify with focused tests, AI-review, and open the PR. Never merges. Invoke as /orc:build {number}.
model: sonnet
---

`build` takes one specced issue and drives it to an open, AI-reviewed PR for you
to merge. An issue of any size is built in one `build` run producing one PR —
there is no size gate. When it can't safely continue, it stops at a **gate**:
commits and pushes whatever exists, comments on the issue explaining why, sets
`status:blocked`, and stops. Fix the cause and re-run — it resets to
`origin/main` and starts fresh.

Everything project-specific — how to verify — comes from the repo's `CLAUDE.md`.
This skill hardcodes nothing about any one project.

## `--dry-run`

`/orc:build {number} --dry-run` runs everything through implementation,
verification, and review exactly as normal, including local git — the branch
is created and every wave's work is committed locally, so `git log` / `git diff
origin/main...HEAD` show real, inspectable output. It stops being "real" at the
network boundary: skip the `gh issue edit` label changes in steps 5 and 13,
skip `git push` in step 9, and skip step 12's `gh pr create` entirely — print
the title, body, and labels it would have used instead of creating anything.
Steps 13-14 (CI watch, mergeability, the label flip) need a real PR to check
against, so there's nothing genuine to run there; report what's left to verify
once the branch is actually pushed. End with:
```
DRY RUN — {n} commit(s) on local branch {branch}, not pushed. Would open PR:
"{title}" against main. Re-run without --dry-run to push and open it.
```
Gates still trip on real problems (spec, confidence, ambiguity, focused
verification, review blockers) — dry-run previews the push/PR boundary, it
doesn't skip validation.

## Gate procedure

Referenced throughout as "**gate: {name}**". When a gate trips:

1. Commit and push whatever exists on the branch (so it's inspectable) — unless
   nothing was built yet.
2. Comment on the issue. The recovery command depends on whether a PR was
   already opened (step 12) — if so, everything through review is done and
   only the CI/mergeability tail failed, so `/orc:resume` picks up from there
   instead of redoing the whole build:
   ```
   🚧 Build paused: {gate name}

   {specific reason}

   What's needed: {the concrete fix}
   Resume: fix the above, then re-run `/orc:resume {number}` (continues from the open PR).
   ```
   or, if no PR exists yet:
   ```
   🚧 Build paused: {gate name}

   {specific reason}

   What's needed: {the concrete fix}
   Resume: fix the above, then re-run `/orc:build {number}` (it resets to origin/main and rebuilds from scratch).
   ```
3. `gh issue edit {number} --remove-label "status:building" --add-label "status:blocked"`.
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
this issue, `/orc:resume {number}` is almost always what's wanted instead: it
continues from the open PR rather than redoing the whole build. If
`status:draft`: **gate: spec**
(no spec yet — run `/orc:plan {number}`).

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

### 5. Branch

Always start from a clean base so reruns are deterministic:

```bash
git fetch origin main
git switch -C issue/{number}-{slug} origin/main
gh issue edit {number} --remove-label "status:ready,status:blocked" --add-label "status:building"
```

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
then run **focused verification** (step 8) for the files that wave touched
before starting the next wave. Keep a short running list of non-obvious choices
and discovered constraints — this becomes the PR body's implementation notes.

### 8. Focused verification

Verification defaults to **scoped/filtered** test runs — never the full suite.
At every point in the build (per wave, pre-commit, pre-PR) run only the tests
covering what changed: the test file(s) a task touched, or the domain around a
shared file it modified.

Prefer the command in `CLAUDE.md`'s **`## Focused Verification`** section (a
PHPUnit `--filter`, `pytest -k`, a JS test-path arg, etc. — necessarily
per-repo). If that section is absent, derive a narrow invocation from
`## Verification` by scoping it to the touched paths. **Do not run the whole
suite** — that is CI's job (step 13), and the CI-watch step is the safety net
for anything a focused run misses.

If a focused command fails and the fix isn't a trivially safe correction,
**gate: gate/verify** with the failing command and output. If a command can't
run (missing binary/env), record it and continue.

### 9. Commit + push

Stage only files this build changed (never `git add .` blindly). Commit with a
conventional message — `feat(#{number}): {title}` (or `fix(...)` for a bug) —
and push:

```bash
git push -u origin issue/{number}-{slug}
```

### 10. Review (folded in)

Review the branch's full diff against `origin/main` before it becomes a PR.
Refresh it first (`git fetch origin main`) — the waves and verification above
take time, so `origin/main` may have moved since step 5. Run all five agents
**in parallel**, passing each the spec, your implementation notes, and the
full diff (`git diff origin/main...HEAD`) — never the build conversation, so
each reviews with fresh eyes:

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
touches logic the spec depends on. Commit auto-fixes together
(`fix: address review findings`) and re-run focused verification on what they
touched.

Fill `${CLAUDE_PLUGIN_ROOT}/templates/ai-review.md` with each section's status
and findings — this becomes the PR's AI-review comment. If a residual
**BLOCKER** remains after safe auto-fixes, **gate: review blocker** with the
finding. Warnings are noted in the PR and do not block.

### 11. Docblocks + changelog

Update file-level docblocks for changed files. If the repo keeps a
`CHANGELOG.md`, invoke `changelog-writer` and insert its entry at the placement
it specifies — its output leads with a `Placement:` line naming exactly where
the blocks go (an existing `## [Unreleased]` section, a new version heading,
etc.). Commit and push any changes.

### 12. Open PR

Open the PR against `main` using the repo's PR template. Include the
implementation notes and the AI-review summary in the body, and
`Closes #{number}`.

```bash
pr_url=$(gh pr create --base main --title "{title}" --body "{body}")
pr=$(basename "$pr_url")
```

`gh pr create` has no `--json` — it prints only the URL, so read `{pr}` back
from that. Post the PR URL as an issue comment. **Do not change the issue's
status label yet** — it stays `status:building` until step 13 confirms the PR
is actually green and mergeable.

### 13. Merge readiness

"Open" isn't useful if it's red or unmergeable — check both before reporting
done. Neither step merges. **This is where the full test suite runs** — CI is
the authoritative full-suite check that focused local runs deliberately leave to
it.

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
gh issue edit {number} --remove-label "status:building" --add-label "status:built"
```
Setting this any earlier risks a step-13 gate firing after `status:building`
has already been replaced — the gate procedure's label swap would then have
nothing to remove, leaving `status:built` and `status:blocked` on the issue at
the same time.

### 14. Report

```
PR open for #{number} — {pr-url}
CI green, mergeable, {n} warning(s) noted. Ready for your merge.
```
