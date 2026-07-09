---
name: post-review
description: Review a draft blog post through sequential factual completeness, structural adherence, author-style, and humanization passes, discuss each pass with the user, and apply only agreed edits to post.md. Use with an optional post number after post-write.
model: sonnet
---

## Steps

### 1. Select and load

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `posts_dir` and `post_list_issue` and determine `{owner}/{repo}`.

If no number is supplied, fetch the post-list issue and show only `draft` posts as `{nnn}  {Title}`. Let the user choose. Normalize a supplied number to three digits.

Find exactly one local branch matching `post/{nnn}-*` and derive `{slug}` from it. Require the worktree at `../$(basename "$(pwd)")-post-{nnn}-{slug}` on branch `post/{nnn}-{slug}`, confirming it with `git worktree list --porcelain`. Work only there.

Parse `meta.yaml` and require `status: draft`. Read `post.md`, `outline.md`, `notes.md`, `.orc/config/editorial-guidelines.md`, `.orc/config/writing-style.md`, and `~/.agents/skills/post-content-guide.md`.

### 2. Factual completeness pass

Check that the post delivers every promise in the outline and that material claims are supported, internally consistent, appropriately qualified, and current. Verify uncertain or date-sensitive claims with credible web sources; prefer primary sources. Check that changing claims carry `<!-- REFRESH-CHECK -->`.

Present concrete findings with affected passages and proposed changes. Pause for discussion. Record which edits the user accepts, rejects, or modifies. Do not edit yet.

### 3. Structural adherence pass

Audit the declared post type against the content guide: lead in, concise answer section, read-on transition, detailed answer, more-information sections, scope, paragraph length, formatting, and FAQ rule.

Present findings and proposed changes, then pause for discussion. Record decisions without editing.

### 4. Style-match pass

Compare the draft against `.orc/config/writing-style.md` and editorial guidelines. Flag vocabulary, sentence patterns, tone, framing, and rhetorical habits that do not sound like the author. Do not treat grammatical smoothness as inherently better than an authentic voice.

Present findings and proposed changes, then pause for discussion. Record decisions without editing.

### 5. Humanization pass

Flag overly uniform cadence, generic transitions, repeated section formulas, empty summaries, inflated certainty, excessive symmetry, and sentences that feel polished without sounding natural. Preserve clarity and factual precision.

Present findings and proposed changes, then pause for discussion.

### 6. Apply agreed edits

Summarize the accepted edits across all four passes and obtain final confirmation. Apply only those edits directly to `post.md`. Preserve rejected passages and avoid unrelated rewrites.

Re-read the complete result for contradictions or broken transitions introduced by editing. Keep metadata status as `draft` and do not change the post-list issue. Report the edited path and any unresolved concerns.
