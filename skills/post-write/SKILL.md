---
name: post-write
description: Write a complete blog draft from an outlined post using its research, editorial guidelines, author writing style, and shared content guide, then mark it draft in metadata and the GitHub post list. Use with an optional post number after post-develop.
model: sonnet
---

## Steps

### 1. Select and locate

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `posts_dir` and `post_list_issue` and determine `{owner}/{repo}`.

If no number is given, fetch the post-list issue and show only `outlined` posts as `{nnn}  {Title}`. Let the user choose. Normalize a supplied number to three digits.

Find exactly one local branch matching `post/{nnn}-*` and derive `{slug}` from it. Require the worktree at `../$(basename "$(pwd)")-post-{nnn}-{slug}` on branch `post/{nnn}-{slug}`, confirming it with `git worktree list --porcelain`. If missing, abort with the exact `git worktree add` command. Work only inside that worktree.

### 2. Load requirements

Parse `meta.yaml` and require `status: outlined`. Read `notes.md`, `outline.md`, `.orc/config/editorial-guidelines.md`, `.orc/config/writing-style.md`, and `~/.agents/skills/post-content-guide.md`.

If the writing-style file is missing or contains only its setup placeholder, stop and explain that `/post-write` depends on populated writing samples. Do not substitute a generic voice.

### 3. Protect an existing draft

If `post.md` exists and contains non-whitespace content, ask the user to choose: overwrite it, abort, or rename it to `post-v1.md`. If `post-v1.md` already exists, choose the next unused `post-vN.md`. Do not modify the existing draft before the user chooses.

### 4. Write

Write the complete draft to `post.md` as pure Markdown prose with no frontmatter. Follow the approved outline and content guide, matching the author style and editorial constraints.

Target approximately 1,350 words for response, 2,500 for staple, or 3,500 for pillar. Favor completeness over padding. Fulfill every promise in the outline, use specific entities and verified facts, and place `<!-- REFRESH-CHECK -->` beside every date-sensitive claim.

Draft the Answer Section last, then position it after the lead in. Omit FAQ for response posts, use it only when useful for staple posts, and require it for pillar posts.

### 5. Validate and update

Check that `post.md` has no YAML frontmatter, follows the declared type, and is reasonably near its target length. Use a YAML parser to set `status: draft` without changing other fields.

Fetch the current post-list issue body, locate the row by `{nnn}`, update only its status to `draft`, and write it back using `gh issue edit --body-file`.

Report the draft path and approximate word count.
