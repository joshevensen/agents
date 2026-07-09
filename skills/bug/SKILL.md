---
name: bug
description: Debug and fix a bug from a description or Sentry link — diagnosis through merged into main. No issue created. Runs full AI review before merge.
model: opus
---

## Arguments

- `{input}` — a Sentry issue URL or a plain description of the bug
- `[--dry-run]` — diagnose and plan the fix without applying it

---

## Steps

### 0. Resolve repo

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

---

### 1. Intake

**If the input is a Sentry URL:**

Parse the URL to extract `{org}` and `{issue-id}`. Sentry URLs follow these forms:
- `https://sentry.io/organizations/{org}/issues/{issue-id}/`
- `https://{org}.sentry.io/issues/{issue-id}/`

Fetch the issue:
```bash
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/issues/{issue-id}/"
```

Fetch the latest event (stack trace, breadcrumbs, request context):
```bash
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/issues/{issue-id}/events/latest/"
```

If `$SENTRY_AUTH_TOKEN` is not set, stop:
```
SENTRY_AUTH_TOKEN is not set. Either set it or paste the error details directly.
```

Extract from the response:
- Error title and type
- Full stack trace (all frames, innermost last)
- Breadcrumbs (last 10)
- Request URL and method if present
- Affected user count and first/last seen

**If the input is a plain description or pasted error:**

Use the provided text as the bug context. No API call needed.

---

### 2. Diagnose

Read the stack trace or description. Trace through the relevant source files starting from the innermost frame, working outward. For each relevant file:
- Read the file at the line indicated
- Understand what the code is doing and what could cause the reported error
- Follow any referenced dependencies, models, or services

Look for:
- The exact line causing the error
- The condition that triggers it (null value, missing key, race condition, wrong assumption)
- Whether the bug is in application code, a dependency interaction, or a data/state issue
- Whether it is likely intermittent or deterministic

---

### 3. Root cause + confidence

Present the diagnosis:

```
ROOT CAUSE
{clear explanation of exactly what is failing and why}

EVIDENCE
{specific stack frames or code lines that support the diagnosis}

PROPOSED FIX
{description of the minimal change that resolves the issue}

Files to change:
- {file} — {what changes}

Confidence: {score}/100 — {brief reason}
```

**Score ≥ 70 — auto-proceed:**
Continue to step 4.

**Score < 70 — pause:**
```
Low confidence — say "proceed" to apply the fix anyway, or clarify the bug context.
```
Wait for the user.

**If `--dry-run`:** stop here. Report the diagnosis and proposed fix.

---

### 4. Branch + Worktree

Derive a slug from the error title: lowercase, spaces and punctuation → hyphens, max 50 chars.

Branch name: `bug/{slug}`
Worktree path: `../{basename-of-pwd}-bug-{slug}`

```bash
git fetch origin
git worktree add {worktree-path} -b bug/{slug} origin/main
```

If the branch already exists:
```
Branch bug/{slug} already exists.

(r) resume  (s) reset to origin/main
```
On `(s)`: `git -C {worktree-path} reset --hard origin/main`

**Worktree setup — restore gitignored generated files.**

```bash
ln -s {main-repo}/platform/public/build {worktree-path}/platform/public/build
cd {worktree-path}/platform && php artisan wayfinder:generate
```

**Continue all remaining steps from within `{worktree-path}`.**

---

### 5. Fix

Apply the minimal change that resolves the root cause. Do not refactor surrounding code or address unrelated issues.

**No guessing allowed.** If the fix requires information not in the stack trace or source files — stop and ask.

---

### 6. Verify

Run commands listed in `AGENTS.md` under `## Verification`. Skip if the section does not exist.

---

### 7. Pre-commit gate

Run commands listed in `AGENTS.md` under `## Pre-commit Gate`. If a command fails: stop and report which command failed and why. Do not proceed until resolved.

---

### 8. Commit and push

Review changes:
```bash
git status --short
git diff --stat
```

Stage only the files changed by the fix — do not use `git add .`.

Commit:
```
fix: {brief description of what was broken and how it is fixed}
```

```bash
git push -u origin bug/{slug}
```

---

### 9. Parallel AI review

Collect inputs:
- **Bug context** — the root cause diagnosis from step 3 (used as the spec)
- **Diff** — `git diff main...HEAD`

Invoke all four agents in parallel. Pass each the bug context and diff:

- **`review-correctness`** — does the fix actually address the root cause? Are there edge cases where the bug could still occur?
- **`review-security`** — does the fix introduce any injection, auth, or data exposure issues?
- **`review-quality`** — is the fix clean and consistent with surrounding code patterns?
- **`review-impact`** — does the fix have unintended side effects, breaking changes, or performance implications?

---

### 10. Surface blockers and warnings

If no BLOCKERs or WARNINGs: proceed.

Otherwise:
```
{n} findings need attention:

BLOCKERS
1. [Correctness] {file}:{line} — {finding}

WARNINGS
2. [Security] {file}:{line} — {finding}

(f) fix all  (r) review one by one  (d) defer all and continue
```

**`(f)`:** Work through each finding. Show exact edit, confirm `(y/n)`, apply. Commit: `fix: address review findings` and push.

**`(r)`:** For each finding: show detail, offer `(f) fix  (d) defer`.

**`(d)`:** Continue. Deferred items appear in the PR body.

---

### 11. Changelog

Invoke the `changelog-writer` agent. Pass the bug description and fix summary.

The agent returns a `## [Unreleased]` block with a `### Fixed` entry. Insert it into `CHANGELOG.md`.

---

### 12. Commit changelog

```bash
git add CHANGELOG.md
git commit -m "docs: changelog"
git push
```

---

### 13. Open PR

```bash
gh pr create --repo {owner}/{repo} \
  --title "fix: {brief description}" \
  --body "$(cat <<'EOF'
## Root Cause

{root cause explanation from step 3}

## Fix

{description of what changed and why}

{Sentry link if available}
EOF
)" \
  --base main \
  --head bug/{slug}
```

---

### 14. CI check

```bash
gh pr checks {pr} --repo {owner}/{repo} --watch
```

If any checks are failing, enter CI fix mode:

1. Fetch logs: `gh run view {run-id} --repo {owner}/{repo} --log-failed`
2. Get diff: `git diff main...HEAD`
3. Invoke the `ci-debugger` agent. Pass the failing check name, log output, and diff.
4. **Apply silently** if confidence is high and the fix is safe. **Stop and report** if confidence is low or scope is non-trivial.
5. Apply, commit (`fix: fix CI — {description}`), push.
6. Re-watch. Repeat until all checks pass.

---

### 15. Deploy risk check

Invoke the `deploy-risk-scanner` agent. Pass the PR number.

If risk level is **HIGH** or any findings exist:
```
DEPLOY RISKS
{agent findings}
```
Stop and wait for confirmation before proceeding.

If risk level is **none** or **low**, proceed without prompting.

---

### 16. Merge and cleanup

Squash-merge, delete the branch, and remove the worktree:

```bash
gh pr merge {pr} --repo {owner}/{repo} --squash \
  --subject "fix: {brief description}"

MAIN=$(git worktree list | awk 'NR==1 {print $1}')
git -C "$MAIN" pull origin main
git -C "$MAIN" branch -D bug/{slug}
git -C "$MAIN" worktree remove --force {worktree-path}
```

Invoke the `queue-sync` agent in the background. Pass `{owner}/{repo}`.

---

### 17. Report

```
Fixed and merged.

Bug:   {error title or description}
Fix:   {one-line description of the change}
PR:    #{pr} (squash-merged into main)
{Sentry: {url} if applicable}
```
