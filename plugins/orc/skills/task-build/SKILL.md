---
name: task-build
description: Implement a spec, run AI review, open a PR, and process feedback — all in one sitting. Requires status:ready and a Spec comment. Use --dry-run to plan without building.
model: sonnet
---

## Steps

### 0. Resolve number

If `{number}` was not supplied as an argument, scan the conversation for the most recently mentioned task number (e.g. `#42`, `task 42`, `issue 42`, or just `42` in a task context). Use that number and confirm:
```
Using task #{number} — run /task-build {number} explicitly to override.
```
If no number can be inferred, stop and ask: "Which task number should I build?"

---

### 1. Load

Invoke the `issue-loader` agent. Pass the issue number and `{owner}/{repo}`.

Use the returned metadata for all subsequent references to the issue's title, labels, status, slug, branch, body, spec comment, and PR URL.

Confirm `status:ready`. If not:
- `status:draft` → "Run /task-create {number} to generate a spec first."
- `status:progress` → "Task is already in progress."
- `status:built` → task has a PR open. Offer:
  ```
  Task #{number} is status:built — PR is already open.

  (r) re-process PR review threads
  (b) rebuild from scratch — resets branch to origin/main
  ```
  On `(r)`: skip to step 12 (Parallel AI review) and re-process.
  On `(b)`: reset status to `status:ready` and continue from step 3.
- `status:defective` → prior build failed. Offer:
  ```
  Task #{number} is status:defective — prior build failed.

  (r) rebuild — spec is fine, retry the build
  (s) re-spec first — run /task-create {number} to fix the spec
  ```
  On `(r)`: reset label to `status:ready` and continue from step 3.
  On `(s)`: stop. Run `/task-create {number}`, then `/task-build {number}`.

If no spec comment was returned:
```
No spec found on #{number}. Run /task-create {number} to generate a spec.
```

Display: task title, problem statement or bug description, acceptance criteria.

---

### 2. Spec quality check

Evaluate whether the spec is complete enough to build from:
- Are acceptance criteria concrete and independently verifiable?
- Are scope boundaries clear (feature: in/out of scope present; bug: reproduction steps present)?
- Are there ambiguities that would require guessing during implementation?

If the spec fails:
```
Spec isn't ready to build from. Issues found:
  - {issue}
  - {issue}

Run /task-create {number} to refine the spec, then retry.
```
Stop.

---

### 3. Branch + Worktree

Skip entirely if `--dry-run`.

Determine branch name: `task/{number}-{slug}` where slug is lowercase kebab-case of the title.

Determine worktree path: `../$(basename $(pwd))-task-{number}-{slug}`

```bash
git branch --list "task/{number}-*"
git worktree list | awk -v b="[task/{number}-{slug}]" '$3 == b {print $1}'
```

**Branch does not exist — fresh build:**
```bash
git worktree add {worktree-path} -b task/{number}-{slug} origin/main
```

**Branch exists, no worktree:**
```bash
git worktree add {worktree-path} task/{number}-{slug}
```

**Branch exists, worktree exists, status is `status:ready`** — prior partial attempt:
```
Branch task/{number}-{slug} already exists at {worktree-path}.

(r) resume from where it left off
(s) hard reset to origin/main — discards all changes on this branch
```
On `(s)`: `git -C {worktree-path} reset --hard origin/main`

**Status is `status:defective`** — branch already reset to `origin/main`:
```
Task #{number} was marked defective. Branch is at origin/main.
Ready to rebuild? (y) yes
```

**Continue all remaining steps from within `{worktree-path}`.** All file reads, writes, and git commands run from there. The original directory stays on main.

**Worktree setup — restore gitignored generated files.**
Worktrees inherit only what's in git. Files listed in `.gitignore` do not exist in a fresh worktree and must be set up before the full gate can run. For the platform app, always run these after the worktree is created:

```bash
# Vite manifest — needed for HTTP tests that render Inertia views
ln -s {main-repo}/platform/public/build {worktree-path}/platform/public/build

# Wayfinder TypeScript types — needed for typecheck
cd {worktree-path}/platform && php artisan wayfinder:generate
```

If `public/build` doesn't exist in the main repo either, the gate's typecheck and HTTP tests will fail — note this clearly rather than silently skipping it.

---

### 4. Approach summary

Read the spec's **Codebase Touchpoints**, **Files to Create**, and **Files to Modify** sections. Summarize as 3–5 bullets confirming what will change and why.

```
Approach:
- {bullet}
...
```

If more than 20 files appear across those sections, recommend splitting the task before proceeding.

---

### 5. Confidence score

Score the approach 0–100 based on:
- Spec completeness
- Codebase clarity (are the right files clearly identifiable?)
- Absence of ambiguity or unknown dependencies

**Score ≥ 70 — auto-proceed:**
```
Confidence: {score}/100 — {brief reason}
```
Proceed to execution immediately.

**Score < 70 — human review required:**
```
Confidence: {score}/100 — {brief reason}

Say "proceed" when ready to build.
```
Wait for the user. Discuss or revise as needed. On "proceed", continue to execution.

**If `--dry-run`:** stop here regardless of score. Report the score.

---

### 6. Setup

Create the task folder if it doesn't already exist:
```bash
mkdir -p .orc/tasks/{number}-{slug}
```

Initialize the implementation notes file from the template at `${CLAUDE_PLUGIN_ROOT}/skills/task-build/templates/impl-notes.md`. Write it to `.orc/tasks/{number}-{slug}/impl-notes.md`.

Update status:
```bash
gh issue edit {number} --repo {owner}/{repo} \
  --remove-label "status:ready,status:defective" \
  --add-label "status:progress"
```

---

### 7. Execute

Work through plan steps in order. Do not stop between steps unless blocked.

**No guessing allowed.** If a step is ambiguous, incomplete, or conflicts with the codebase — stop and ask:
- Which step triggered the question
- What is ambiguous or missing
- What options exist and which you lean toward

**Append to `.orc/tasks/{number}-{slug}/impl-notes.md` whenever:**
- The actual approach diverged from the plan step
- A constraint was discovered that wasn't in the spec
- A non-obvious choice was made (especially if an alternative was rejected)
- Anything that would surprise a future reader of the code

Do NOT append for steps that executed exactly as planned.

**On failure:**
1. Revert uncommitted changes: `git checkout .`
2. Hard reset: `git reset --hard origin/main`
3. Append a failure entry to `.orc/tasks/{number}-{slug}/impl-notes.md` under `## Failures`:
   ```markdown
   ### Attempt {n}: {step number and title}
   - **Tried:** {approach}
   - **Outcome:** {what went wrong}
   - **Resolved by:** {leave blank — build stopped here}
   ```
4. Update status:
   ```bash
   gh issue edit {number} --repo {owner}/{repo} \
     --remove-label "status:progress" \
     --add-label "status:defective"
   ```
5. Stop and report. Run `/task-create {number}` to fix the spec, then `/task-build {number}` to rebuild.

---

### 8. Verify

Run verification commands listed in `AGENTS.md` under `## Verification`. Skip if the section does not exist.

---

### 9. Pre-commit gate

Run commands listed in `AGENTS.md` under `## Pre-commit Gate`. If a command fails: stop and report which command failed and why. Do not proceed until resolved.

If a command cannot run (missing binary, wrong environment): record it and continue.

---

### 10. Commit and push

Review changes before staging:
```bash
git status --short
git diff --stat
```

Identify any unrelated changes (files not part of this task). If found:
```
{n} unrelated change(s) found:
  {file} — {description}

Commit these separately first?
(y) yes  (n) leave them unstaged
```

Stage task-related files explicitly — do not use `git add .`.

Commit with a conventional message:
```
{type}(#{number}): {short title}
```
Infer `{type}` from the issue title: starts with "Fix"/"Resolve"/"Correct" → `fix`; starts with "Refactor"/"Clean"/"Simplify" → `refactor`; starts with "Document"/"Update docs" → `docs`; otherwise → `feat`.

```bash
git push -u origin task/{number}-{slug}
```

---

### 11. Link to Herd

```bash
cd {worktree-path}/platform && herd link task-{number}.fibermade
```

This makes the branch available at `http://task-{number}.fibermade.test` alongside the main site at `http://fibermade.test`.

---

### 12. Parallel AI review

Collect all inputs the review agents will need:

**Spec** — find the comment whose body starts with `## Spec` in the issue comments. Store the full text.

**Implementation notes** — read `.orc/tasks/{number}-{slug}/impl-notes.md`.

**Diff** — `git diff main...HEAD`

**Changed files** — `git diff main...HEAD --name-only`

Invoke all four agents in parallel. Pass each the full spec, implementation notes, and diff:

- **`review-correctness`** — verifies acceptance criteria, scope drift, and logic correctness
- **`review-security`** — checks for injection, auth gaps, data exposure, and insecure defaults
- **`review-quality`** — checks complexity, pattern consistency, and test coverage
- **`review-impact`** — checks for breaking changes, side effects, and performance regressions

---

### 13. Surface blockers and warnings

If there are no BLOCKERs or WARNINGs: proceed directly to step 14.

Otherwise:
```
{n} findings need attention:

BLOCKERS
1. [Correctness] {file}:{line} — {finding}

WARNINGS
2. [Security] {file}:{line} — {finding}

(f) fix all  (r) review one by one  (d) defer all and continue
```

**`(f)` — Fix all:** Work through each BLOCKER then WARNING. Show the exact edit, confirm `(y/n)`, apply. Commit all fixes together: `fix(#{number}): address AI review findings` and push.

**`(r)` — Review one by one:** For each finding show detail and offer `(f) fix  (d) defer`.

**`(d)` — Defer all:** Continue. Deferred items appear in the PR review comment.

---

### 14. Automated docblocks

For each file in the diff, run both passes automatically — no confirmation prompts.

**Pass A — remove redundant function-level docblocks**

A docblock is redundant if everything it says is immediately derivable from the function name, parameter names/types, and return type. Remove it silently.

**Pass B — write or update file-level docblocks**

Using the spec, implementation notes, and agent findings, write a file-level docblock for each changed file:

```
{description — what this file does}
@context   {why this file exists / the "why" from spec}
@gotchas   {non-obvious behavior, constraints, or surprises from impl-notes and agent findings}
@dependencies {key dependencies this file relies on}
```

If a file already has a file-level docblock: update it. If not: add one.

---

### 15. Automated changelog

Invoke the `changelog-writer` agent. Pass the task title and PR title.

The agent reads the diff and existing `CHANGELOG.md` and returns a `## [Unreleased]` block. Insert that block at the top of the changelog's `## [Unreleased]` section (or create the section if absent).

---

### 16. Commit docblocks and changelog

If anything changed in steps 14–15:
```bash
git add -A
git commit -m "docs(#{number}): docblocks and changelog"
git push
```

---

### 17. Open PR

Update status:
```bash
gh issue edit {number} --repo {owner}/{repo} \
  --remove-label "status:progress" \
  --add-label "status:built"
```

Read the PR body template from `.github/PULL_REQUEST_TEMPLATE.md`. Fall back to `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/pull-request-template.md` if missing.

```bash
gh pr create --repo {owner}/{repo} \
  --title "({number}): {short title}" \
  --body "{body}" \
  --base main \
  --head {branch}
```

Post the PR URL as a comment on the issue:
```bash
gh issue comment {number} --repo {owner}/{repo} --body "{pr-url}"
```

---

### 18. Post AI review comment

Read `${CLAUDE_PLUGIN_ROOT}/skills/task-build/templates/ai-review.md`. Fill in each agent's findings. Mark any finding fixed in step 13 as: `~~{finding}~~ — fixed in {commit-sha}`.

```bash
gh pr comment {pr} --repo {owner}/{repo} --body "{ai-review-body}"
```

---

### 19. Wait for Copilot review

```bash
${CLAUDE_PLUGIN_ROOT}/skills/task-build/scripts/wait-for-pr-review {owner}/{repo} {pr}
```

Exit 0: proceed with Copilot threads first. Exit 1 (timed out): proceed with human threads only.

---

### 20. Process review threads

Fetch all unresolved, non-outdated review threads:
```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr}) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 10) {
            nodes {
              author { login }
              body
              diffHunk
              path
              line
            }
          }
        }
      }
    }
  }
}'
```

Filter to `isResolved: false` and `isOutdated: false`. If none: skip to step 21.

List all threads upfront (Copilot first, then human). Work through one at a time:

```
Thread {i}/{n}
FILE: {path}:{line}
DIFF:
{diff hunk}

COMMENT ({author}):
{comment body}

RECOMMENDATION:
{what to do; note any reasons to push back}

(f) fix  (r) reply  (d) defer
```

**`(f)`:** Show edit → confirm → apply → commit `fix(#{number}): address review comment in {file}` → push → reply → resolve thread via GraphQL.

**`(r)`:** Show draft reply → confirm → post → resolve thread.

**`(d)`:** Leave unresolved, move on.

---

### 21. Report

```
PR #{pr} open — {pr-url}
Preview: http://task-{number}.fibermade.test

Run /task-merge {number} when ready.
```
