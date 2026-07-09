---
name: task-merge
description: Check CI, fix any failures, then squash-merge a PR, clean up the branch, and return to main. Use after /task-build.
model: sonnet
---

## Steps

### 0. Resolve number

If `{number}` was not supplied as an argument, scan the conversation for the most recently mentioned task number (e.g. `#42`, `task 42`, `issue 42`, or just `42` in a task context). Use that number and confirm:
```
Using task #{number} — run /task-merge {number} explicitly to override.
```
If no number can be inferred, stop and ask: "Which task number should I merge?"

---

### 1. Load

Invoke the `issue-loader` agent. Pass the issue number and `{owner}/{repo}`.

Extract the PR number from the returned `pr_url`. Derive the branch name from the returned `branch` field.

---

### 2. CI check

```bash
gh pr checks {pr} --repo {owner}/{repo}
```

If all checks pass: proceed.

If any checks are failing, enter CI fix mode:

1. Fetch logs for the first failing check:
   ```bash
   gh run view {run-id} --repo {owner}/{repo} --log-failed
   ```
2. Get the branch diff:
   ```bash
   git diff main...HEAD
   ```
3. Invoke the `ci-debugger` agent. Pass the failing check name, log output, and diff.
4. Evaluate the proposed fix:
   - **Apply silently** if confidence is high and the fix is clearly safe (e.g. missing import, type error, lint issue, test fixture update).
   - **Stop and report** if confidence is low, the fix touches logic that could contradict the spec or plan, or the scope is larger than a trivial correction. Present the diagnosis and wait for direction.
5. Apply, commit (`fix(#{number}): fix CI — {brief description}`), push.
6. Re-watch CI:
   ```bash
   gh pr checks {pr} --repo {owner}/{repo} --watch
   ```
7. Repeat from step 1 until all checks pass.

---

### 3. Conflict check

```bash
gh pr view {pr} --repo {owner}/{repo} --json mergeable --jq '.mergeable'
```

If `CONFLICTING`:

1. Check out the branch and rebase onto main to surface conflict markers:
   ```bash
   git fetch origin
   git checkout {branch}
   git rebase origin/main
   ```

2. Invoke the `conflict-classifier` agent. Pass the current branch name.

3. If the agent reports any **complex** conflicts: stop and present the conflicting sections to the user and wait for direction.

4. If all conflicts are **simple**: apply the resolutions the agent recommends, stage the files, and continue:
   ```bash
   git add {files}
   git rebase --continue
   ```

5. Push the resolved branch:
   ```bash
   git push --force-with-lease
   ```

---

### 4. Deploy risk check

Invoke the `deploy-risk-scanner` agent. Pass the PR number.

If the agent reports risk level **HIGH** or any findings:
```
DEPLOY RISKS
{agent findings}
```
Stop and wait for confirmation before proceeding.

If risk level is **none** or **low** with no blocking findings, proceed to step 5 without prompting.

---

### 5. Queue sync

Invoke the `queue-sync` agent in the background. Pass `{owner}/{repo}`. Do not wait for it to complete.

---

### 6. Merge and cleanup

Unlink the Herd site for this worktree if it exists:
```bash
cd {worktree-path}/platform && herd unlink task-{number}.fibermade
```

Then merge, delete the branch, sync the queue file, and remove the worktree:
```bash
${CLAUDE_PLUGIN_ROOT}/skills/task-merge/scripts/cleanup {owner}/{repo} {pr} {branch} {number} {slug}
```

GitHub closes the issue via `Closes #{number}` in the PR body.

---

### 7. Report

```
Merged, cleaned up, and ready for the next task.
```
