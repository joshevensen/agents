---
name: post-abandon
description: Destructively abandon an unpublished post by removing its worktree, branch, files from main, and GitHub post-list entry, optionally returning the topic to Ideas. Use with an optional post number only when the user wants to discard in-progress post work.
model: sonnet
---

## Steps

### 1. Select the post

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `posts_dir` and `post_list_issue` and determine `{owner}/{repo}`.

If no number is supplied, fetch the post-list issue and show all non-published rows as `{nnn}  {Title} — {status}`. Let the user choose. Normalize the number to three digits.

Find exactly one local branch matching `post/{nnn}-*` and derive `{slug}` from it. If no branch exists, search main for exactly one `{posts_dir}/{nnn}/*/meta.yaml` as a recovery fallback. Parse metadata from the worktree when available, otherwise from main, and refuse to abandon a `published` post.

### 2. Inspect destructive scope

Set branch `post/{nnn}-{slug}` and expected worktree `../$(basename "$(pwd)")-post-{nnn}-{slug}`. Show:

- post title, number, status, and type
- worktree path and whether it exists
- branch and whether local/remote copies exist
- directory to be deleted from main
- uncommitted worktree changes, if any

Ask whether to remove the entry entirely or move the topic back to Ideas with a one-line description. Then require an explicit destructive confirmation naming the post number. Do nothing until confirmed.

### 3. Preserve issue intent first

Fetch the current issue body. Remove the row identified by `{nnn}`. If retaining the topic, add `- {Title} — {description}` beneath Ideas unless it already exists. Preserve unrelated content and update with `gh issue edit --body-file`.

If the issue update fails, stop before deleting local data.

### 4. Remove Git state

If the worktree exists, remove it with `git worktree remove`; use `--force` only after separately warning that uncommitted changes will be lost and obtaining another confirmation.

Delete the local branch with `git branch -D post/{nnn}-{slug}`. If a remote branch exists, ask before deleting it with `git push origin --delete`.

### 5. Remove main files

From a clean main worktree, delete `{posts_dir}/{nnn}/{slug}/` if it exists, then remove the now-empty `{posts_dir}/{nnn}/` directory. Commit the deletion if tracked files changed. Never delete a non-empty number directory containing another slug.

Report what was deleted and whether the topic was retained in Ideas.
