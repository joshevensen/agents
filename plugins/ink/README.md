# ink

Editorial workflow for long-form blog posts: brainstorm, develop, write, review, and publish.

Part of the `hexbyte` marketplace. Install:

```
/plugin marketplace add joshevensen/agents
/plugin install ink@hexbyte
```

## Skills

| Skill | What it does |
|---|---|
| `/ink:post-brainstorm` | Research and add ideas to the GitHub Post List issue |
| `/ink:post-create` | Choose type → allocate number → create branch, worktree, and files |
| `/ink:post-develop` | Collaborative research → notes and outline |
| `/ink:post-write` | Draft `post.md` in the author's style |
| `/ink:post-review` | Four sequential review passes → agreed edits |
| `/ink:post-publish` | Finalize metadata → squash merge → clean up worktree |
| `/ink:post-list` | Display the GitHub Post List issue |
| `/ink:post-abandon` | Remove unpublished post work and its list entry |
| `/ink:post-refresh` | Audit published posts for stale or outdated claims |

Pipeline: `post-create → post-develop → post-write → post-review → post-publish`, with `post-brainstorm`, `post-list`, `post-abandon`, and `post-refresh` as supporting operations.

## Versioning

`plugin.json`'s `version` is semver and is the cache key Claude Code uses to decide whether an installed copy needs updating — pushing commits alone does not update anyone already installed. **Bump it in the same PR as any change you want to ship**, and record it in `CHANGELOG.md`. See [Version management](https://code.claude.com/docs/en/plugins-reference#version-management).
