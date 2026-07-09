# orc

Issue-to-PR automation for a GitHub-issue-driven workflow. You author specs interactively; `build` implements them autonomously — through code, review, and an open PR — stopping at well-defined **gates** whenever it can't safely continue. You do the final merge.

Part of the `hexbyte` marketplace. Install:

```
/plugin marketplace add joshevensen/agents
/plugin install orc@hexbyte
```

## Skills

| Skill | Mode | What it does |
|---|---|---|
| `/orc:create` | local | Discuss an idea, **confirm its type**, then create a task/bug **issue** or a feature **doc** |
| `/orc:plan` | autonomous-capable | Turn a feature doc into ordered task issues (feature-flag setup is always task #1) |
| `/orc:build` | **autonomous** | Take an issue (or feature id) from spec to open PR: implement → verify → review. Never merges |
| `/orc:review` | local | Run the AI review over the current diff and process findings. Called by `build` and `push` |
| `/orc:push` | local | Commit working-tree changes → review → push → open PR (no merge) |
| `/orc:drafts` | local | List `status:draft` issues (waiting for a spec) |
| `/orc:ready` | local | List `status:ready` issues (buildable / ready to `@claude`) |
| `/orc:bump` | local | Review and merge Dependabot grouped PRs when safe |
| `/orc:discuss` | local | Read-only exploration mode — no changes until you say go |
| `/orc:setup` | local | Wire a repo for autonomous mode (Actions workflow, OAuth secret, `AGENTS.md`, PR template) |

## The pipeline

```
             you, locally                          autonomous                 you
  ┌────────────────────────────────┐        ┌──────────────────────┐      ┌───────┐
  create ──▶ issue (status:ready) ──┼──────▶ build ──▶ PR (status:built) ──▶ merge
     │                                        ▲
     └── feature ──▶ .orc/features/F001.md    │
                        │                     │
                        └── plan ──▶ ordered task issues ──┘
```

- **Tasks & bugs** become GitHub issues with a spec comment.
- **Features** become a committed markdown doc under `.orc/features/F###-slug.md` that `plan` fans out into ordered task issues. Features are gated behind a Pennant flag (created as the feature's first task), so each task merges to `main` behind the flag and you flip it when the feature is whole — no long-lived feature branch.

## Autonomy & gates

`build` (and `plan`) run unattended when `ORC_AUTONOMOUS=1` is set — the GitHub Action sets it. In that mode there is no human to answer questions, so every decision point is a **gate**: a checkpoint where, if a condition isn't met, `build` leaves its branch pushed for inspection, posts a `🚧 Build paused` comment explaining why, sets `status:blocked`, and exits. You fix the cause and re-run `build`, which **resets to `origin/main`** and starts fresh.

The seven gates:

| Gate | Trips when |
|---|---|
| Spec | no spec, or acceptance criteria aren't machine-verifiable |
| Confidence | material ambiguity between the spec and the codebase |
| Scope | the change balloons past a single task (≈20+ files) — run `plan` to split |
| Ambiguity | mid-build, a decision the spec doesn't cover |
| Gate/verify | tests or the pre-commit gate fail and can't be safely auto-fixed |
| Review blocker | a review agent raises a BLOCKER that isn't safely auto-fixable (includes destructive-migration risk) |
| Missing infra | no `AGENTS.md` gate, or a feature task with no flag |

## Labels

`status:draft` → `status:ready` → (`status:building`) → `status:blocked` (needs you) or `status:built` (PR open, needs your merge). Type is `type:task` or `type:bug`. Labels self-provision when a skill first needs them.

## Invoking build

- Comment `@claude implement this` on a `status:ready` issue (via the Action), **or**
- `/orc:build 123` — a specific task/bug issue, **or**
- `/orc:build F001` — the next unbuilt task in feature F001.
