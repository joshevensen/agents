---
name: post-brainstorm
description: Collaboratively research and generate blog topic ideas using editorial strategy, the GitHub post list, current fiber/ISP trends, competitor coverage, and reader questions. Use when adding untyped ideas before creating posts.
model: sonnet
---

## Steps

### 1. Load context

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `post_list_issue` and determine `{owner}/{repo}`.

Fetch the issue body with `gh issue view`. Read `.orc/config/editorial-guidelines.md`; if missing, stop and direct the user to `/setup posts` rather than inventing a strategy.

Summarize existing Ideas and existing post titles/statuses to avoid duplicates and identify coverage gaps.

### 2. Research

Use web research because trend and competitor information is time-sensitive. Search across:

- current fiber, broadband, ISP, and connectivity developments
- competitor posts and gaps in their coverage
- reader questions from search results, forums, support communities, and relevant public discussions

Prefer primary sources for factual claims. Record source URLs and dates internally, but keep the conversation focused on candidate topics rather than producing a research report.

### 3. Collaborate

Present a small set of strong candidates with:

- working title
- one-line angle
- why it fits the editorial strategy
- why it is distinct from existing ideas/posts
- whether it appears timely or evergreen

Invite the user to reject, combine, or redirect candidates. Refine in short rounds until the user explicitly agrees to ideas. Do not assign numbers, slugs, directories, or post types.

### 4. Update Ideas

For each accepted idea, format one line:

```markdown
- {Title} — {one-line description}
```

Fetch the issue body again immediately before editing. Add only non-duplicate lines beneath `## Ideas`, preserving all tables and unrelated content. Write the body to a temporary file and update with `gh issue edit --body-file`.

If no idea is accepted, make no changes. Report the titles added.
