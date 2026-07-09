# Changelog

Tracks the `orc` plugin's `version` in `.claude-plugin/plugin.json`. Bump that field with every change you want installed copies to receive — Claude Code caches plugins by version, so pushing commits alone does not update anyone already on a pinned version. Follow [semver](https://semver.org): MAJOR for breaking changes, MINOR for new features, PATCH for fixes.

## [0.1.0]

Full rewrite of the dev workflow around one autonomous skill.

### Added
- `create` — interactive: discuss an idea, confirm task/bug/feature, produce an issue+spec or a feature plan doc
- `plan` — feature doc → ordered task issues (Pennant flag setup always first)
- `build` — the one autonomous skill; implements a spec, runs the shared review, opens a PR, checks CI/mergeability. Runs unattended under `ORC_AUTONOMOUS=1`, stopping at one of seven gates (spec, confidence, scope, missing infra, ambiguity, gate/verify, review blocker) rather than guessing
- `review` — shared AI review (4 review agents + `deploy-risk-scanner` + `/code-review`), invoked by both `build` and `push`
- `push` — manual-edit path: commit, review, push, open PR — no merge
- `drafts` / `ready` — live `status:draft` / `status:ready` issue lists
- Shared `templates/spec.md` and `templates/feature-plan.md` — canonical spec shape read by `spec-writer`, `create`, `plan`, and `build`'s spec-gate
- `setup` scaffolds the GitHub Actions workflow and walks through `CLAUDE_CODE_OAUTH_TOKEN` so `@claude implement this` runs against a Claude subscription, not a metered API key

### Changed
- `merge` renamed to `push`; Copilot review removed entirely in favor of `review`
- Label schema: `type:task`/`type:bug`, `status:draft/ready/building/blocked/built`

### Removed
- `task-create`, `task-build`, `task-merge`, `feature-create`, `feature-plan`, `feature-build`, `feature-merge`, `bug`, `queue-push` — folded into `create`/`plan`/`build`
- `queue-sync`, `spec-researcher` agents (unused)
- Global Queue issue / `QUEUE.md` — replaced by `drafts`/`ready`
