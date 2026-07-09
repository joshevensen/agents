---
name: merge
description: Stage uncommitted changes, create a branch, commit, push, open a PR, wait for CI and Copilot, then squash-merge. Use for quick manual edits that don't warrant a full task workflow.
model: sonnet
---

## Steps

### 1. Preflight

Check for uncommitted changes:
```bash
git status --short
git diff --stat
```

If the working tree is clean, stop and report:
```
Nothing to commit — working tree is clean.
```

---

### 2. Confidence check

Inspect the full diff:
```bash
git diff
```

Score the change against these criteria:

| Signal | Weight |
|---|---|
| > 50 lines changed | high concern |
| New files added (not just edits) | medium concern |
| Changes to config, migrations, auth, billing, routing, or env vars | high concern |
| Changes span more than 3 files | medium concern |
| Logic changes (conditionals, loops, algorithms) | medium concern |
| Pure cosmetic/copy/whitespace/comment edits | no concern |

If the diff triggers **any high concern** or **two or more medium concerns**, stop and report:
```
CONFIDENCE CHECK FAILED
This change looks too significant for /quick-merge:
  {bullet list of triggered signals}

Use /task-build → /task-merge instead.
```

Wait for the user to confirm override (`proceed anyway`) or stop.

---

### 3. Commit message

If `{message}` was supplied as an argument, use it verbatim.

Otherwise, inspect the diff and produce a short, imperative commit message (50 chars max). Show it to the user and confirm before proceeding:
```
Commit message: {message}
Proceed? (yes to continue)
```

---

### 4. Create branch

Derive a slug from the commit message (lowercase, hyphens, max 40 chars).

If currently on `main`/`master`:
```bash
git checkout -b quick/{slug}
```

If already on a non-main branch, stay on it and continue.

---

### 5. Stage and commit

```bash
git add -A
git commit -m "{message}"
```

---

### 6. Push

```bash
git push -u origin HEAD
```

---

### 7. Open PR

Check for an existing PR on this branch:
```bash
gh pr view --json number,url 2>/dev/null
```

If no PR exists, create one targeting `main`:
```bash
gh pr create \
  --title "{message}" \
  --body "Quick manual fix — no associated task." \
  --base main
```

Capture the PR number.

---

### 8. Wait for CI

```bash
gh pr checks {pr} --repo {owner}/{repo} --watch
```

If any checks fail, stop and report the failing check names. Do not attempt to auto-fix — this is a quick-merge, not a task build. Wait for the user to resolve and re-run, or to confirm abandoning the merge.

---

### 9. Wait for Copilot review

```bash
${CLAUDE_PLUGIN_ROOT}/skills/quick-merge/scripts/wait-for-pr-review {owner}/{repo} {pr}
```

Exit 0 (review state on stdout): proceed to fetch threads.
Exit 1 (timed out after 5 minutes): skip thread processing and note:
```
No Copilot review received — proceeding.
```

Once a review is detected, fetch all unresolved, non-outdated review threads:
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

Filter to `isResolved: false` and `isOutdated: false`.

If no threads: proceed to step 10.

For each thread, present it and wait for direction:
```
Copilot thread {i}/{n}
FILE: {path}:{line}
DIFF:
{diff hunk}

COMMENT:
{comment body}

RECOMMENDATION:
{what to do}

(f) fix  (r) reply  (d) defer
```

**`(f)` — Fix:**
1. Show the exact edit and confirm.
2. Apply, commit (`fix: address Copilot comment in {file}`), push.
3. Resolve the thread:
   ```bash
   gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "{thread-id}"}) { thread { isResolved } } }'
   ```

**`(r)` — Reply:** Post a reply, then resolve the thread.

**`(d)` — Defer:** Leave unresolved and continue.

---

### 10. Merge

```bash
gh pr merge {pr} --squash --delete-branch
```

---

### 11. Return to main

```bash
git checkout main
git pull
```

---

### 12. Report

```
Done — squash-merged and back on main.
```
