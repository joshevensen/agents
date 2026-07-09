---
name: build
description: Take a task/bug issue (or a feature id) from spec to open PR — implement, verify, AI-review — then stop for your manual merge. Runs autonomously when ORC_AUTONOMOUS=1, stopping at gates it can't safely pass. Invoke as /orc:build 123 or /orc:build F001, or via an @claude comment on a ready issue.
model: sonnet
---

`build` is the one autonomous skill. It never merges — it stops at an open, AI-reviewed PR for you to merge. When it can't safely continue, it stops at a **gate**: leaves its branch pushed for inspection, comments on the issue explaining why, sets `status:blocked`, and exits. Fix the cause and re-run — it resets to `origin/main` and starts fresh.

Everything project-specific (how to verify, the pre-commit gate) comes from the repo's `AGENTS.md`. This skill hardcodes nothing about any one project.

## Gate procedure

Referenced throughout as "**gate: {name}**". When a gate trips:

1. Commit and push whatever exists on the branch (so it's inspectable) — unless nothing was built yet.
2. Comment on the issue:
   ```
   🚧 Build paused: {gate name}

   {specific reason}

   What's needed: {the concrete fix}
   Resume: fix the above, then re-run `orc:build {number}` (it resets to origin/main and rebuilds from scratch).
   ```
3. `gh issue edit {number} --remove-label "status:building" --add-label "status:blocked"`.
4. Stop.

In **interactive** mode (`ORC_AUTONOMOUS` unset), a gate may instead surface the problem to the user and offer to resolve it inline rather than blocking-and-exiting.

## Steps

### 0. Resolve target

Require an argument. Then:

- **Issue number** (`^\d+$`) — use it directly as `{number}`.
- **Feature id** (`^F\d+$`) — read `.orc/features/{id}-*.md`, parse the ordered task list, and select the **first task whose issue is still open**. Set that as `{number}`. If every task is closed: report `Feature {id} is complete — all tasks merged.` and stop.

If no argument is given, stop and ask which issue or feature to build.

### 1. Detect mode

```bash
echo "${ORC_AUTONOMOUS:-0}"
```

`1` → autonomous (gates comment-and-exit). Otherwise interactive.

### 2. Load

Invoke `issue-loader` with `{number}`. Use the returned title, slug, labels, status, body, and spec comment.

Expect `status:ready`. If `status:blocked` or `status:building` from a prior run, continue (this run resets the branch). If `status:draft`: **gate: spec** (no spec yet).

### 3. Gate: spec

The spec comment must exist and its acceptance criteria must be **machine-verifiable** — each tied to a test, command, or observable behavior. If there is no spec, or criteria are vague ("looks right", "works well"), **gate: spec** with the specific criteria that can't be checked. Point the user to `/orc:create {number}` to (re-)spec.

### 4. Gate: confidence

Read the spec's touchpoints and locate the real files in the codebase. If there is material ambiguity — a named file/symbol doesn't exist, two readings of a criterion would produce different code, an unstated dependency blocks the work — **gate: confidence**, listing the exact unknowns to resolve. Confidence is judged on concrete facts, not a numeric score.

### 5. Gate: scope

Estimate the files the spec will touch. If it is clearly bigger than one task (≈20+ files, or spans multiple subsystems), **gate: scope**: this is a feature — run `/orc:plan` to split it.

### 6. Gate: missing infra

- If `AGENTS.md` has no `## Pre-commit Gate` (or verification) section, there is no way to prove the build is sound → **gate: missing infra** (run `/orc:setup`).
- If `{number}` is a feature task and the feature's Pennant flag doesn't exist yet, **gate: missing infra** (the flag-setup task must merge first).

### 7. Branch

Always start from a clean base so reruns are deterministic:

```bash
git fetch origin main
git switch -C task/{number}-{slug} origin/main
gh issue edit {number} --remove-label "status:ready,status:blocked" --add-label "status:building"
```

### 8. Implement

Work the spec top to bottom. **No guessing**: if a step is ambiguous, incomplete, or conflicts with the codebase, **gate: ambiguity** with the exact question and the options you see. Keep a short running list of non-obvious choices and discovered constraints — this becomes the PR body's implementation notes.

### 9. Verify + pre-commit gate

Run the commands under `AGENTS.md` `## Verification`, then `## Pre-commit Gate`. If a command fails and the fix isn't a trivially safe correction, **gate: gate/verify** with the failing command and output. If a command can't run (missing binary/env), record it and continue.

### 10. Commit + push

Stage only files this task changed (never `git add .` blindly). Commit with a conventional message — `feat(#{number}): {title}` (or `fix(...)` for a bug) — and push:

```bash
git push -u origin task/{number}-{slug}
```

### 11. Review

Invoke `/orc:review` with base `main`, passing the spec and your implementation notes. If it returns a residual **BLOCKER** that wasn't safely auto-fixed, **gate: review blocker** with the finding. Warnings are noted in the PR and do not block.

### 12. Docblocks + changelog

Update file-level docblocks for changed files. Invoke `changelog-writer` and insert its `## [Unreleased]` block into `CHANGELOG.md` if the repo keeps one. Commit and push any changes.

### 13. Open PR

```bash
gh issue edit {number} --remove-label "status:building" --add-label "status:built"
```

Open the PR against `main` using the repo's PR template. Include the implementation notes and the AI-review summary from step 11 in the body, and `Closes #{number}`. Post the PR URL as an issue comment. **Do not merge.**

### 14. Report

```
PR open for #{number} — {pr-url}
Reviewed, {n} warning(s) noted. Ready for your merge.
```

If building a feature (`F###`), remind: run `/orc:build {id}` again after merging to pick up the next task.
