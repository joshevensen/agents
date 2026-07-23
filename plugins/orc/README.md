# orc

Issue-to-PR automation for a GitHub-issue-driven workflow, built for Claude Code
on the web. You discuss and spec an issue interactively; `build` implements it
autonomously — through code, review, and an open PR — stopping at well-defined
**gates** whenever it can't safely continue. You do the final merge.

Part of the `hexbyte` marketplace.

### Install — Claude Code CLI (local)

```
/plugin marketplace add joshevensen/hexbyte-plugins
/plugin install orc@hexbyte
```

### Install — Claude Code on the web (cloud sessions)

The interactive `/plugin` command isn't available in web sessions, and plugins must be installed **into the cloud environment** so they load before Claude Code launches. Add the plugin to your environment's **Setup script**:

1. In [claude.ai/code](https://claude.ai/code), open the environment (⋯ → **Update cloud environment**, or the environment picker).
2. In the **Setup script** field, add:

   ```bash
   claude plugin marketplace add joshevensen/hexbyte-plugins
   claude plugin install orc@hexbyte

   # orc drives GitHub through the gh CLI, which isn't preinstalled in web
   # sessions. Install it here; it auto-authenticates via the GH_TOKEN that
   # web environments already expose (no `gh auth login` needed).
   if ! type -p gh >/dev/null; then
     mkdir -p -m 755 /etc/apt/keyrings
     wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       > /etc/apt/keyrings/githubcli-archive-keyring.gpg
     chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
     echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list
     apt-get update && apt-get install -y gh
   fi
   ```

3. **Save changes.** The script runs on each new session, so orc is installed, `gh` is on the PATH and authenticated, and the `/orc:*` skills are available. Existing sessions aren't affected — start a new one.

Requires the environment's network access to reach `github.com` **and `cli.github.com`** (the default **Trusted** policy does). Under a locked-down policy that blocks the `gh` install source, this won't work — orc needs `gh` present, so either allow the install host in your policy or run orc from a Trusted environment.

## Skills

| Skill | What it does |
|---|---|
| `/orc:create` | Discuss an idea at the scope level and produce GitHub issue(s) — no spec |
| `/orc:plan` | Research the codebase and write a build-ready spec onto an issue |
| `/orc:build` | Take a specced issue to an open PR: draft PR on branch, task list → parallel build with live per-wave commits → focused verify → mark ready for review → AI review → merge readiness. Never merges |
| `/orc:resume` | Continue a blocked build whose PR already reached ready-for-review — re-checks review freshness, then CI/mergeability, no rebuild |
| `/orc:push` | Commit working-tree changes → review → push → open PR (no merge) |
| `/orc:respond` | Manually fetch a PR's unresolved review threads/comments and work through them — fix and push, or reply (no subscription, no merge) |
| `/orc:list` | List open issues, optionally filtered by status |
| `/orc:bump` | Review and merge Dependabot grouped PRs when safe |
| `/orc:discuss` | Read-only exploration mode — no changes until you say go |
| `/orc:setup` | Scaffold a repo for orc — labels, `.orc/`, `CLAUDE.md` sections, PR template, CHANGELOG, dependabot |

## The pipeline

```
  create ──▶ issue (status:draft) ──▶ plan ──▶ issue (status:ready) ──▶ build ──▶ PR (status:built) ──▶ you merge
   scope           no spec yet          spec                              one PR, any size
```

Everything is a GitHub issue — no task/feature split, no size threshold.

- **`create`** resolves scope and open questions, then files the issue(s). It
  splits into multiple issues only when the work is genuinely independent, never
  because it looks "too big." Every issue it files reads `Open Questions: None.`
- **`plan`** explores the codebase, picks the technical approach, and writes the
  spec as an issue comment. It's the sole owner of spec-writing, and holds the
  spec to the same bar `build` re-checks: machine-verifiable acceptance criteria
  and `Open Questions: None.`
- **`build`** decomposes the spec into a dependency-ordered task list. Independent
  tasks run in parallel via subagents — each dispatched with the model that fits
  its complexity — while genuinely dependent tasks run in sequence. Any size of
  issue becomes one PR.

## Watching a build live

`build` opens a **draft PR right after branching** (before any code exists)
and commits+pushes after every wave, so the PR's diff fills in as the build
progresses instead of appearing all at once at the end. It's marked **ready
for review** only once implementation is fully done and verified — that
transition is the load-bearing signal both for you (draft = still building,
non-draft = implementation complete) and for `/orc:resume` (see Gates below).
The AI review posts as a **PR comment**, never folded into the description —
that's what lets `resume` tell a fresh review apart from a stale one.

## Focused verification

`build` verifies with **scoped/filtered** test runs — only the tests around what
each task changed — after every wave, right before that wave's commit. The full
suite is left to **CI**, which `build` watches once the PR is ready for review;
a failure there is handled by `ci-debugger` with one fix-and-repush attempt.
Each repo's `CLAUDE.md` carries a standardized **`## Focused Verification`**
section (distinct from `## Verification`) so `build` has a deterministic place
to find the filtered command — the command itself is necessarily
per-repo/per-language. A repo can also declare a **`## CI-Only Verification`**
section for suites too heavy for build's own runs (Playwright/e2e, browser-driven
tests) — `build` never runs those, in any form; `setup` detects and offers to
scaffold it.

## Gates

`build` runs unattended and never guesses. At any decision point it can't safely
pass, it **gates**: commits and pushes its branch for inspection, comments the
reason on the issue, sets `status:blocked`, and stops. The recovery command
depends on whether the PR reached **ready for review** (see above), not
whether a PR merely exists — a draft PR always exists from just after
branching:

- **PR is ready for review** — the gate is downstream of a complete,
  implemented build (a review finding, a CI flake, a merge conflict).
  `/orc:resume {number}` picks up from there: it re-checks whether the AI
  review is still fresh before re-running anything, then CI/mergeability.
  Nothing gets rebuilt.
- **PR is still draft** — implementation itself is incomplete or in question
  (ambiguity, a mid-wave verification failure). `/orc:build {number}` resets
  to `origin/main` and rebuilds from scratch, reusing (and re-drafting) the
  same PR rather than creating a new one.

| Gate | Trips when |
|---|---|
| Spec | no spec, acceptance criteria aren't machine-verifiable, or Open Questions ≠ `None.` |
| Confidence | material ambiguity between the spec and the codebase (not a size check) |
| Ambiguity | mid-build, a decision the spec doesn't cover |
| Gate/verify | focused tests or CI fail and can't be safely auto-fixed |
| Review blocker | a review agent raises a BLOCKER that isn't safely auto-fixable (includes destructive-migration risk) |
| Missing infra | `CLAUDE.md` has no `## Verification` / `## Focused Verification` section |

There is **no scope gate** — issue size never stops a build.

## `--dry-run`

Every skill that writes to GitHub or pushes (`create`, `plan`, `build`,
`push`, `bump`, `resume`, `setup`) accepts a trailing `--dry-run`. Local
git commits and local file writes still happen — so you can inspect real
output with `git log`/`git diff` — but `git push` and every GitHub-mutating
`gh` call (issue/PR/label create, edit, comment, merge) are skipped and
printed instead. Each skill documents its exact boundary at the top of its
`SKILL.md`.

## Labels

`status:draft` (scoped, needs a spec) → `status:ready` (specced, buildable) →
`status:building` → `status:blocked` (needs you) or `status:built` (PR open,
needs your merge). Bugs additionally carry `type:bug`. Labels self-provision
when a skill first needs them.

## Versioning

`plugin.json`'s `version` is semver and is the cache key Claude Code uses to
decide whether an installed copy needs updating — pushing commits alone does not
update anyone already installed. **Bump it in the same PR as any change you want
to ship**, and record it in `CHANGELOG.md`. See
[Version management](https://code.claude.com/docs/en/plugins-reference#version-management).
