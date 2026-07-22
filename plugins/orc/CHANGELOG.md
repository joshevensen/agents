# Changelog

Tracks the `orc` plugin's `version` in `.claude-plugin/plugin.json`. Bump that field with every change you want installed copies to receive — Claude Code caches plugins by version, so pushing commits alone does not update anyone already on a pinned version. Follow [semver](https://semver.org): MAJOR for breaking changes, MINOR for new features, PATCH for fixes.

## [0.4.0]

### Added
- `build` opens a **draft PR right after branching** (step 5) and commits+pushes after every wave, instead of one commit at the end and a PR opened only once everything is done — the diff now fills in live as the build progresses. If a previous run left a draft PR on this branch, it's reused (and re-drafted if needed) rather than recreated
- `build` marks the PR **ready for review** immediately before the AI review step (step 9) — the exact signal that separates "still implementing" from "implementation done, only review/CI/mergeability left"
- The AI review now posts as a **PR comment** (`gh pr comment`) with a `sha:`/`verdict:` marker, never folded into the PR description — this is what makes a stale review distinguishable from a fresh one
- `/orc:resume` now only acts once a PR is ready for review, never against a draft PR (implementation still in question there — a full `/orc:build` rebuild is correct, not a resume). Before touching CI/mergeability, it checks the AI-review comment's `sha:` marker against current HEAD: a fresh `PASS` skips straight to the merge-readiness tail, a fresh `BLOCK` stops and asks you to actually fix it, and a stale comment (HEAD moved) triggers a real re-review rather than trusting old output
- A new, optional `## CI-Only Verification` section in `CLAUDE.md`: suites listed there (Playwright/e2e, anything too heavy for build's own scoped runs) are never run by `build`, in any form — always left to CI. `setup` detects heavy-suite signals (`playwright.config.*`, `cypress.config.*`, e2e-ish script names) and offers to scaffold it

### Changed
- `push` now opens its PR before running review (steps 6 and 7 swapped) so review has something to comment on, matching the new "review is a comment, never the description" rule
- `deploy-risk-scanner` and `changelog-writer`'s descriptions no longer assume a fixed PR-existence timing, since that now differs between `build`, `push`, and `bump`
- `push`'s description reworded away from "changes you made by hand" / "local sibling of build" — that framing describes a local-IDE pattern (hand-editing outside Claude's view) that doesn't occur on Claude Code web. Its actual value — reviewing and PR'ing changes made directly in conversation without the create/plan/build ceremony — applies equally to both, so the wording now says that instead

## [0.3.0]

### Added
- `/orc:resume` — continues a `build` that stopped after its PR was already open (an infra flake or a fix already applied at the CI/mergeability tail), re-running only that tail instead of rebuilding from scratch. `build`'s gate procedure now recommends `resume` or `build` depending on whether a PR already exists
- `--dry-run` on every GitHub-writing skill (`create`, `plan`, `build`, `push`, `bump`, `resume`, `setup`): local git commits and local file writes still happen for inspection, but `git push` and every GitHub-mutating `gh` call are skipped and printed instead. `manage-labels`/`migrate-labels` support it natively
- A structural CI lint (`.github/workflows/lint-orc.yml`) over the orc plugin: frontmatter validity and model names, `${CLAUDE_PLUGIN_ROOT}` paths resolve, every `Invoke`d agent is defined, and `plugin.json`'s version was bumped whenever `plugins/orc/**` changed

### Fixed
- `bump` had no mergeability check before merging — unlike `build`/`push`, which both check and handle `CONFLICTING`. It now checks first and skips (rather than force-merging into) a conflicting PR, reporting it for the next Dependabot run to resolve

## [0.2.1]

### Changed
- `deploy-risk-scanner` and `conflict-classifier` now run on `sonnet` instead of `haiku` — both make semantic judgments feeding gates (deploy-risk's `HIGH` is a hard blocker; a misclassified conflict can trigger a bad auto-resolve), so the cheapest model was a false-negative risk
- `changelog-writer` now matches the target repo's existing changelog convention (Unreleased-style or versioned) instead of always emitting a Keep-a-Changelog `## [Unreleased]` block, and returns a `Placement:` line telling `build` exactly where to insert the entry
- Web install now provisions the `gh` CLI in the environment setup script — orc drives GitHub through `gh`, which isn't preinstalled in web sessions; it auto-authenticates via the `GH_TOKEN` those environments already expose. Documented in the README and referenced from `setup`'s preflight

### Fixed
- `changelog-writer` now reads the full branch diff (`git diff origin/main...HEAD`) instead of `git diff HEAD~1`, which captured only the last commit and dropped most of a multi-commit build from the changelog
- `deploy-risk-scanner` now leads with the branch diff (`git diff origin/main...{branch}`) instead of `gh pr diff {pr_number}` — during build/push review, the case it's used for most, no PR exists yet, so a PR number was never available
- `issue-loader`'s status example listed a non-existent `progress` label; corrected to `building`, matching the real `status:*` vocabulary
- `bump`'s OSV vulnerability check sent lowercase ecosystem names (`packagist`, `github-actions`); OSV's real identifiers are `Packagist` and `GitHub Actions` (case- and spelling-exact), so every non-npm query was silently returning zero results — verified against the live API with a package carrying known CVEs
- `bump`'s npm publish-recency check read `.publish_time` from the per-version registry endpoint, which has no such field; the timestamp only exists on the root package document under `.time["{version}"]` — verified against the live registry. The check always returned empty and never fired
- `create`'s issue-creation command passed `--json`/`--jq` to `gh issue create`, which doesn't support either flag and errors — verified against the CLI reference. It now reads the issue number from the printed URL instead
- `push`'s PR-creation command had the same `gh pr create --json` problem; same fix
- `build` and `push` diffed for review against the local `main` branch instead of `origin/main`, risking a stale base since nothing keeps local `main` current; both now fetch and diff against `origin/main`. `push` additionally never fetched before its mergeability rebase, risking a stale ref there too
- `build` set `status:built` before its CI/mergeability gate (step 13) ran; if that gate then tripped, the shared gate procedure's label swap had nothing to remove (`status:building` was already gone), leaving `status:built` and `status:blocked` on the issue at once. The label now flips to `status:built` only after CI is green and the PR is mergeable

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
