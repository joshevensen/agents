---
name: post-list
description: Fetch and display the repository's GitHub Post List issue in a readable terminal format, including idea descriptions and numbered post titles, statuses, and publication dates. Use when the user wants to see the editorial post inventory.
model: haiku
---

## Steps

### 1. Load configuration

Require `.orc/config/posts.config.json`; otherwise stop with: `Post infrastructure is not configured. Run /setup posts first.` Parse `post_list_issue` with a JSON parser and determine `{owner}/{repo}`.

### 2. Fetch

```bash
gh issue view {post_list_issue} --repo {owner}/{repo} --json title,body,url
```

If the issue is missing or inaccessible, report the configured number and the GitHub error. Do not scan local post directories as a silent fallback because the issue is the canonical list.

### 3. Display

Parse the body sections and render:

- Ideas as title plus one-line description.
- Response, Staple, and Pillar posts as number, Title, status, and publication date when present.
- Empty sections explicitly as `None`.

Display titles from the issue, never raw slugs. Preserve zero-padded numbers. End with the issue URL. Do not modify files or the issue.
