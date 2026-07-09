---
name: post-publish
description: Finalize and publish a draft post by rebasing its worktree branch, setting published metadata, updating the GitHub post-list issue, squash-merging into main, and removing the worktree and branch. Use with an optional post number when the user is ready to set a post live.
model: sonnet
---

## Steps

### 1. Select and validate

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `posts_dir` and `post_list_issue` and determine `{owner}/{repo}`.

If no number is supplied, fetch the post-list issue and show only `draft` posts. Let the user choose. Normalize the number to three digits, find exactly one local branch matching `post/{nnn}-*`, and derive `{slug}` from it.

Require worktree `../$(basename "$(pwd)")-post-{nnn}-{slug}` on branch `post/{nnn}-{slug}`, confirming it with `git worktree list --porcelain`. Parse `{posts_dir}/{nnn}/{slug}/meta.yaml` there and require `status: draft`. Require a non-empty `post.md` and a clean worktree. Confirm explicitly that the user is ready to publish; stop on anything other than a clear confirmation.

### 2. Rebase on main

Determine the repository's main worktree and verify its `main` branch is clean. Fetch the remote, update main with a fast-forward-only pull, then rebase the post branch onto main from the post worktree.

If any conflict occurs, stop the rebase at the conflict, list the files and conflict sections, and wait for user resolution. Do not guess, abort, or continue automatically.

### 3. Finalize metadata

Review tags with the user and apply any final changes. Using the current local date in the repository's timezone, set:

```yaml
status: published
published_at: YYYY-MM-DD
```

Preserve all other metadata. Commit all final post changes on the post branch with a concise message such as `publish: {title}`.

### 4. Update the post-list issue

Fetch the issue body immediately before editing. Locate the row by `{nnn}`, set Status to `published`, and set Published to the same `YYYY-MM-DD`. Preserve all other rows and sections. Update through a temporary file with `gh issue edit --body-file`.

If this fails, stop before merging and report that the branch is ready but the index was not updated.

### 5. Squash-merge locally

From the clean main worktree:

```bash
git merge --squash post/{nnn}-{slug}
git commit -m "publish: {title}"
```

Verify the committed files and metadata. Push main only if the repository normally pushes publication changes directly; otherwise report the local main commit and stop before cleanup. Do not assume a PR workflow that the post plan does not specify.

### 6. Clean up

After the main commit is secured, remove the worktree and delete the local post branch:

```bash
git worktree remove {worktree_path}
git branch -d post/{nnn}-{slug}
```

Delete the remote post branch if one exists and the user confirms it is no longer needed. The post directory stays at `{posts_dir}/{nnn}/{slug}/` on main. Report the publication date and main commit.
