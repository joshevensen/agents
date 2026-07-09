---
name: post-develop
description: Research and collaboratively develop an idea or outlined post into updated notes and a natural blog outline, then mark it outlined in metadata and the GitHub post list. Use with an optional post number when shaping or reshaping a post.
model: sonnet
---

## Steps

### 1. Select the post

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `posts_dir` and `post_list_issue` and determine `{owner}/{repo}`.

If no argument is provided, fetch the post-list issue and show all `idea`, `outlined`, and `draft` rows as `{nnn}  {Title} — {status}`. Let the user select by number. If an argument is provided, normalize it to three digits and use it directly.

Find exactly one local branch matching `post/{nnn}-*` and derive `{slug}` from that branch name. Abort on zero or multiple matches. The GitHub issue title is not a substitute for the slug.

### 2. Locate the worktree

Expected branch: `post/{nnn}-{slug}`. Expected worktree: `../$(basename "$(pwd)")-post-{nnn}-{slug}`. Confirm the actual association with `git worktree list --porcelain` rather than relying only on the directory name.

Require the worktree and verify that Git reports the expected branch there. If absent, stop with:

```text
Post worktree not found. Recreate it with:
git worktree add {worktree_path} post/{nnn}-{slug}
```

Do not develop files in the main checkout.

### 3. Validate and load

In the worktree, parse `meta.yaml`. Accept only `idea` or `outlined`; re-development of an outlined post is allowed. A draft must be deliberately moved back to outlined before this workflow.

Read `notes.md`, any existing `outline.md`, `.orc/config/editorial-guidelines.md`, and `~/.agents/skills/post-content-guide.md`.

### 4. Research collaboratively

Discuss the angle, reader intent, claims, examples, and section priorities. Use current web research and source finding where needed; prefer primary sources for technical, regulatory, pricing, and provider claims.

Scale effort by type: keep a response post tightly focused, give a staple post durable practical depth, and research a pillar post broadly enough to support authoritative coverage.

Update `notes.md` throughout the session with findings, source links, decisions, unresolved questions, and date-sensitive claims. Never invent a source or silently discard existing useful notes.

### 5. Produce the outline

When the user agrees the direction is ready, write or replace `outline.md`. Follow the content guide in the background, but present a natural post-specific outline rather than template labels. Include the intended point of each section, supporting evidence/examples, and promises the draft must fulfill.

Include FAQ planning only for pillar posts or when natural for a staple post. Omit FAQ from response posts. Note that the Answer Section is drafted last even though it appears near the beginning.

### 6. Update status

Use a YAML parser to set `status: outlined` while preserving all other metadata.

Fetch the current post-list issue body, locate the row by `{nnn}`, update only its status to `outlined`, and write the body back with `gh issue edit --body-file`. Report the worktree paths to `notes.md` and `outline.md`.
