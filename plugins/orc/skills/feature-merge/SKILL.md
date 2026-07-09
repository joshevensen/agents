---
name: feature-merge
description: Merge a completed feature branch into main. Verifies all phases are done, merges in latest main, resolves conflicts, runs pre-commit gate, opens a PR, waits for CI, squash-merges, and closes the feature issue.
model: sonnet
---

## Arguments

- `{number}` — the feature issue number

---

## Steps

### 1. Load feature issue

Invoke the `issue-loader` agent. Pass the issue number and `{owner}/{repo}`.

Confirm the returned labels include `feature`. Derive:
- `{Name}` — the returned title
- `{slug}` — the returned `slug` field
- `{feature-branch}` — `feature/{slug}`

---

### 2. Verify all phases complete

Confirm `status:built`. If not:
- `status:draft` → "Run /feature-plan {number} to generate phase specs first."
- `status:ready` → "No phases have been built yet. Run /feature-build {number} to start."
- `status:progress` → "A phase build is still in progress. Wait for it to complete."

Find the `## Phases` section in the issue body. Check that every item is checked (`- [x]`).

If any phase is unchecked, stop:
```
Not all phases are complete. Remaining:

  - Phase {n} — {name}
  ...

Run /feature-build {number} to complete the next phase.
```

If there is no `## Phases` section, stop:
```
No phase tracker found on #{number}.
Run /feature-plan {number} to set up phases first.
```

---

### 3. Confirm

```
All {n} phases complete for #{number} — {Name}.
This will squash-merge feature/{slug} into main.

Proceed? (y) yes  (n) cancel
```

---

### 4. Create worktree for the feature branch

Determine worktree path: `../{basename-of-pwd}-feature-{slug}`

```bash
git fetch origin

git branch --list "{feature-branch}"
git worktree list | awk -v b="[{feature-branch}]" '$3 == b {print $1}'
```

**Worktree does not exist:**
```bash
git worktree add {worktree-path} {feature-branch}
```

**Worktree already exists** (prior incomplete merge attempt): use it as-is.

**Continue all remaining steps from within `{worktree-path}`.**

---

### 5. Merge main into feature branch

```bash
git merge origin/main --no-edit
```

If the merge succeeds cleanly: proceed.

If there are conflicts:

1. Invoke the `conflict-classifier` agent. Pass the current branch name (`{feature-branch}`).

2. If the agent reports any **complex** conflicts: stop and present the conflicting sections to the user and wait for direction.

3. If all conflicts are **simple**: apply the resolutions the agent recommends and stage the files:
   ```bash
   git add {files}
   git merge --continue --no-edit
   ```

4. Push the updated feature branch:
   ```bash
   git push origin {feature-branch}
   ```

---

### 6. Pre-commit gate

Run commands listed in `AGENTS.md` under `## Pre-commit Gate`. If a command fails: stop and report which command failed and why. Do not proceed until resolved.

If a command cannot run (missing binary, wrong environment): record it and continue.

If the gate produced changes (e.g. auto-formatting), commit and push:
```bash
git add {changed-files}
git commit -m "chore(feature/{slug}): pre-merge gate fixes"
git push origin {feature-branch}
```

---

### 7. Open PR

Derive `{owner}/{repo}` from the remote:
```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Build the PR body from the feature issue. Include the phase list from the `## Phases` section.

```bash
gh pr create \
  --title "feat({slug}): {Name}" \
  --body "$(cat <<'EOF'
Closes #{number}

## {Name}

{opening paragraph from feature issue body}

## Phases

{Phases section from feature issue body}
EOF
)" \
  --base main \
  --head {feature-branch}
```

Capture the PR number.

---

### 8. CI check

```bash
gh pr checks {pr} --repo {owner}/{repo} --watch
```

If all checks pass: proceed.

If any checks are failing, enter CI fix mode:

1. Fetch logs for the first failing check:
   ```bash
   gh run view {run-id} --repo {owner}/{repo} --log-failed
   ```
2. Get the diff:
   ```bash
   git diff main...HEAD
   ```
3. Invoke the `ci-debugger` agent. Pass the failing check name, log output, and diff.
4. Evaluate the proposed fix:
   - **Apply silently** if confidence is high and the fix is clearly safe.
   - **Stop and report** if confidence is low or the fix is non-trivial.
5. Apply, commit (`fix(feature/{slug}): fix CI — {brief description}`), push.
6. Re-watch CI and repeat until all checks pass.

---

### 9. Squash-merge into main

```bash
gh pr merge {pr} --repo {owner}/{repo} --squash \
  --subject "feat({slug}): {Name}" \
  --body "Closes #{number}"
```

---

### 10. Close feature issue

GitHub closes the issue automatically via `Closes #{number}` in the PR body. Verify:
```bash
gh issue view {number} --repo {owner}/{repo} --json state --jq '.state'
```

If still open, close it manually:
```bash
gh issue close {number} --repo {owner}/{repo} \
  --comment "All phases complete — merged in #{pr}."
```

Remove the status label now that the issue is closed:
```bash
gh issue edit {number} --repo {owner}/{repo} --remove-label "status:built"
```

---

### 11. Queue sync

Invoke the `queue-sync` agent in the background. Pass `{owner}/{repo}`. Do not wait for it to complete.

---

### 12. Clean up

Pull main and remove the feature branch and worktree:

```bash
MAIN=$(git worktree list | awk 'NR==1 {print $1}')

git -C "$MAIN" pull origin main
git -C "$MAIN" push origin --delete {feature-branch}
git -C "$MAIN" branch -D {feature-branch} 2>/dev/null || true
git -C "$MAIN" worktree remove --force {worktree-path}
```

Remove local phase specs and feature config:
```bash
rm -rf .orc/features/{slug}
```

---

### 13. Report

```
Feature #{number} — {Name} merged.
PR:     #{pr} (squash-merged into main)
Branch: feature/{slug} deleted
Issue:  #{number} closed
Local:  .orc/features/{slug}/ removed
Queue:  #{number} checked off

Back on main.
```
