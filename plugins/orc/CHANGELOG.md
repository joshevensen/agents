# Changelog

Tracks the `orc` plugin's `version` in `.claude-plugin/plugin.json`. Bump that field with every change you want installed copies to receive — Claude Code caches plugins by version, so pushing commits alone does not update anyone already on a pinned version. Follow [semver](https://semver.org): MAJOR for breaking changes, MINOR for new features, PATCH for fixes.

## [0.2.1]

### Changed
- `deploy-risk-scanner` and `conflict-classifier` now run on `sonnet` instead of `haiku` — both make semantic judgments feeding gates (deploy-risk's `HIGH` is a hard blocker; a misclassified conflict can trigger a bad auto-resolve), so the cheapest model was a false-negative risk

## [0.2.0]

Redesign around a three-skill core (`create` → `plan` → `build`) for the
Claude-Code-on-the-web workflow. Everything is a GitHub issue — the task/feature
distinction is gone.

### Added
- `plan` — the sole owner of spec-writing: takes a scoped issue from `create`, researches the codebase, chooses the approach, and writes the spec onto the issue (sets `status:ready`)
- `build` now decomposes a spec into a dependency-ordered task list and runs independent tasks in parallel via subagents, each dispatched with the model matching its complexity; dependent tasks run in sequence
- Focused verification: `build` defaults to scoped/filtered test runs (per wave, pre-commit, pre-PR) and leaves the full suite to CI. `setup` scaffolds a standardized `## Focused Verification` section in `CLAUDE.md`
- `list` — one status-filterable issue listing, replacing `drafts` and `ready`

### Changed
- `create` is now discussion-only — it resolves scope and open questions and files issue(s) with no spec, splitting only when work is genuinely independent (no size threshold)
- `review` folded into `build` (and `push`) as an inline final step instead of a separately invocable skill
- Skills and agents read/write `CLAUDE.md` only; `AGENTS.md` is no longer used
- Build branches are named `issue/{number}-{slug}`

### Removed
- The `@claude` issue-comment trigger, and the GitHub Actions workflow + `CLAUDE_CODE_OAUTH_TOKEN` setup that supported it — the only entry point is Claude Code on the web
- The `ORC_AUTONOMOUS` dual-mode; `build` has a single pause-and-comment gate behavior
- The scope gate — an issue of any size builds in one run
- The task/feature distinction: `type:task`/`type:feature` labels, the `F\d+` feature id, `.orc/features/`, and `templates/feature-plan.md`
- The standalone `review`, `drafts`, and `ready` skills

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
