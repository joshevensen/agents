# Skills

Skills are slash commands that run inside Claude Code. Each skill lives in its own directory with a `SKILL.md` that defines its steps.

## Quick Reference

| Skill | Trigger | What it does |
|---|---|---|
| `/task-create` | Starting a new idea | Interview → create issue → spec → status:ready |
| `/task-create [number]` | Existing issue needs a spec | Research codebase → generate spec → post → status:ready |
| `/task-build [number]` | Issue is `status:ready` | Implement → AI review → PR → process feedback |
| `/task-merge [number]` | PR is open | Check CI → fix failures → conflict check → squash merge → clean up |
| `/feature-create` | Planning a feature | Discussion → GitHub issue → iterate until ready for `/feature-plan` |
| `/feature-plan [number]` | Breaking a feature into phases | Creates feature branch → phase spec files → phase tracker on issue |
| `/feature-build` | Executing a phase spec | Implement phase → PR into feature branch → CI → update tracker |
| `/feature-merge [number]` | All phases done | Merge main in → pre-commit gate → PR → CI → squash into main → close issue |
| `/queue` | Checking work status | Display all open tasks and bugs in queue order |
| `/queue-push` | Changing priorities | Push reordered .orc/QUEUE.md to the GitHub Queue issue |
| `/post-create` | Starting a blog post | Choose type → allocate number → create branch, worktree, and files |
| `/post-brainstorm` | Generating topics | Research and add ideas to the GitHub Post List issue |
| `/post-develop [number]` | Developing a topic | Collaborative research → notes and outline |
| `/post-write [number]` | Drafting an outlined post | Write `post.md` in the author's style |
| `/post-review [number]` | Reviewing a draft | Four sequential review passes → agreed edits |
| `/post-publish [number]` | Publishing a draft | Finalize metadata → squash merge → clean up worktree |
| `/post-list` | Checking editorial status | Display the GitHub Post List issue |
| `/post-abandon [number]` | Discarding a post | Remove unpublished post work and its list entry |
| `/post-refresh` | Auditing published posts | Find old posts and stale marked claims |
| `/discuss [topic]` | Exploring before committing | Read-only exploration mode — no changes until "green light" |
| `/setup` | New repo onboarding | Labels → global queue → AGENTS.md → PR template → CHANGELOG.md |

---

## The Pipeline

The main workflow is a linear pipeline. Each skill hands off to the next.

```
/task-create  →  /task-build  →  /task-merge
```

To re-spec an existing issue or fix a defective spec: `/task-create {number}` → `/task-build {number}`

### `/task-create [number]`

**Without a number:** interviews you about what you want done, creates a GitHub issue, generates a complete spec via the **`spec-writer`** agent, reviews it with you, and posts it as a comment. Leaves the issue at `status:ready`. Also handles queue placement.

**With a number:** loads the existing issue, skips creation and queue steps, and runs the same research → generate → review → post flow. Use this to re-spec after a failed build or when the spec needs refinement. Resets the issue to `status:draft` during revision, then back to `status:ready` when done.

### `/task-build [number]`

Takes an issue at `status:ready` (with a Spec comment) and takes it all the way to an open, reviewed PR. Steps in order:

1. **Implement** — scans the codebase, scores confidence (0–100), executes the spec, runs verification and pre-commit gates, commits, and pushes the branch.
2. **AI review** — runs four agents in parallel, surfaces blockers and warnings for resolution.
3. **Docblocks + changelog** — writes file-level docblocks and updates `CHANGELOG.md` automatically.
4. **PR** — opens the PR, posts the AI review summary as a comment, waits for Copilot review, and works through all unresolved threads one by one.

Supports `--dry-run` to plan without executing.

**On failure:** reverts changes, resets to `origin/main`, logs to `impl-notes.md`, moves to `status:defective`. Run `/task-create {number}` to fix the spec, then `/task-build {number}` to rebuild.

**Review agents (run in parallel):**

| Agent | Focus |
|---|---|
| `review-correctness` | Acceptance criteria, scope drift, logic errors |
| `review-security` | Injection vectors, auth gaps, data exposure, insecure defaults |
| `review-quality` | Complexity, pattern consistency, test coverage |
| `review-impact` | Breaking changes, side effects, performance regressions |

### `/task-merge [number]`

Takes an open PR and merges it. Checks CI first — if checks are failing, invokes the **`ci-debugger`** agent with the log output and diff, then applies the fix, pushes, and re-watches. Checks for merge conflicts and deploy risks (migrations, env var changes, external API changes) before proceeding. Checks off the task in the queue, squash-merges the PR, deletes the branch, switches back to `main`, and cleans up the task folder.

---

## Supporting Skills

### Post workflow

Posts use a separate branch and worktree per post. The GitHub Post List issue is the shared index, while post files live under the configured `posts_dir` as `{nnn}/{slug}/`. The normal path is `/post-create` → `/post-develop` → `/post-write` → `/post-review` → `/post-publish`. Use `/post-brainstorm`, `/post-list`, `/post-abandon`, and `/post-refresh` as supporting operations.

### Feature pipeline

```
/feature-create  →  /feature-plan {number}  →  /feature-build (×n)  →  /feature-merge {number}
```

`/feature-create` runs a back-and-forth discussion and posts the result as a GitHub issue with a `feature` label. The issue body is the living feature document — subsequent rounds of `/feature-create {number}` update it directly. When ready, run `/feature-plan {number}` to create the feature branch (`feature/{slug}`), generate phase spec files locally in `.orc/features/{slug}/`, and add a phase tracker to the issue.

`/feature-build` implements one phase at a time. Each phase gets its own branch off the feature branch, a PR that targets the feature branch (not main), and a CI check before merging. After merging, it checks off that phase in the issue tracker.

`/feature-merge {number}` is run once all phases are complete. It merges latest main into the feature branch, resolves any conflicts, runs the pre-commit gate, opens a PR from the feature branch into main, waits for CI, squash-merges, closes the feature issue, deletes the branch, and removes the local `.orc/features/{slug}/` directory.

### `/queue`

Displays all open tasks and bugs in queue order. Bugs are listed at the end (they are never in the queue). Accepts an optional filter: `/queue tasks` or `/queue bugs`.

If `.orc/QUEUE.md` exists in the project root, it is refreshed after every display.

### `/queue-push`

Pushes the local `.orc/QUEUE.md` order to the GitHub Queue issue. Edit the table rows in `.orc/QUEUE.md` first to reorder, then run `/queue-push` to make it the new canonical order.

### `/discuss [topic]`

Enters read-only exploration mode. All file reads and shell commands are available, but no files or state can be modified until the user says **"green light"**. Useful for understanding a codebase or thinking through an approach before committing to a direction.

---

## Setup

### `/setup`

Provisions a GitHub repo for the skill system. Idempotent — safe to re-run at any time.

What it does:

1. Upserts all managed labels (`status:*`, `type:*`) and prunes unmanaged ones
2. Migrates existing issue labels to the skill system schema
3. Checks every open issue has both a `type:*` and `status:*` label — prompts for any that are ambiguous
4. Ensures the Global Queue issue exists
5. Creates the `.orc/` directory structure and gitignores `.orc/tasks`
6. Scaffolds `AGENTS.md` (with pre-commit gate and verification sections) and symlinks `CLAUDE.md` to it
7. Copies `PULL_REQUEST_TEMPLATE.md` into `.github/` if not present
8. Initializes `CHANGELOG.md` if not present
9. Configures `dependabot.yml` for the detected package ecosystem
10. Generates `.orc/QUEUE.md` and adds it to `.gitignore`
11. Opens a `chore: setup scaffold` PR, waits for Copilot review, and squash-merges it

Run once when connecting a new repo to the skill system.
