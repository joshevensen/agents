---
name: post-create
description: Capture a blog topic or promote an item from the post Ideas list, choose its response/staple/pillar type, and create its numbered directory, branch, worktree, metadata, notes, and GitHub post-list entry. Use when starting a new post.
model: sonnet
---

## Steps

### 1. Load configuration

From the repository root, require `.orc/config/posts.config.json`. If missing, stop with: `Post infrastructure is not configured. Run /setup posts first.`

Parse `posts_dir` and `post_list_issue` with a JSON parser. Resolve `posts_dir` relative to the repository root. Determine `{owner}/{repo}` with `gh repo view --json nameWithOwner --jq '.nameWithOwner'`.

### 2. Establish the topic

If the user says `from ideas`, fetch the issue body:

```bash
gh issue view {post_list_issue} --repo {owner}/{repo} --json body --jq '.body'
```

Parse the `## Ideas` section, display each title and description, and let the user choose. Preserve the exact selected line for later removal.

Otherwise, use the supplied topic. Interview the user about audience, search intent, angle, and desired outcome. Limit this to two or three exchanges unless critical information is missing.

Recommend a post type and explain the scope briefly:

- `response`: one narrow question, approximately 1,350 words
- `staple`: durable practical coverage, approximately 2,500 words
- `pillar`: broad authoritative coverage, approximately 3,500 words

Let the user confirm the type. Ideas have no type until this confirmation.

### 3. Confirm title and slug

Read `${CLAUDE_PLUGIN_ROOT}/skills/post-content-guide.md`. Produce a book-title-capitalized title under 60 characters when practical and never over 73.

Derive the slug exactly as the guide specifies. Show the title, type, and slug and obtain confirmation before making changes.

### 4. Allocate the number

Scan only direct children of `{posts_dir}` whose names match `^[0-9]{3}$`. Take the largest numeric value plus one, starting at `001`, and format it as `{nnn}`. Abort if the result exceeds `999`.

### 5. Create branch and worktree

Set:

- branch: `post/{nnn}-{slug}`
- worktree: `../$(basename "$(pwd)")-post-{nnn}-{slug}`

If the worktree path already exists, abort without modifying it. If the branch already exists, abort and report it; do not attach or reset an existing branch automatically.

```bash
git worktree add {worktree_path} -b post/{nnn}-{slug} HEAD
```

### 6. Create post files

Inside the worktree, create `{posts_dir}/{nnn}/{slug}/meta.yaml` using a YAML serializer, not string substitution:

```yaml
title: "{title}"
description: "{concise description}"
type: response | staple | pillar
status: idea
published_at: null
author: "Josh Evensen"
tags: []
```

Create `notes.md` with headings for Topic Summary, Search Intent, Audience, Angle, and Type Rationale. Seed them from the interview. Do not create `outline.md` or `post.md` yet.

### 7. Update the post-list issue

Fetch the current issue body again immediately before editing. Preserve unrelated text and table rows.

- Add `| {nnn} | {title} | idea | — |` to the table matching the confirmed type.
- If promoted from Ideas, remove only the selected idea line.
- Keep rows ordered numerically.

Write the revised body to a temporary file and run:

```bash
gh issue edit {post_list_issue} --repo {owner}/{repo} --body-file {temp_file}
```

If the issue update fails, leave the created worktree intact and report the exact partial state; do not delete user work automatically.

### 8. Report

Report the post number, title, slug, type, branch, and absolute worktree path.
