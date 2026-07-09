---
name: setup
description: Provision task workflow infrastructure, blog post infrastructure, or both in a GitHub repository. Use `/setup` for tasks, `/setup posts` for posts only, or `/setup both` for both workflows. Use `/setup reset-queue` to hard-reset the Global Queue issue and QUEUE.md from open issues. Idempotent — safe to re-run at any time.
model: sonnet
---

## Steps

### 0. Select mode and resolve `{owner}/{repo}`

Run from inside the project directory.

Interpret the first argument as follows:

- no argument or an explicit repository target: `tasks` mode
- `posts`: posts-only mode
- `both`: tasks and posts mode
- `reset-queue`: queue-reset mode — skip to section 3L
- anything else that is not a GitHub URL or `{owner}/{repo}`: stop and show the four valid forms

An optional repository target may follow `posts`, `both`, or `reset-queue`.

- If a full GitHub URL was passed, extract `{owner}/{repo}` from the path.
- If `{owner}/{repo}` was passed directly, use it as-is.
- If no argument was provided, infer from `git remote get-url origin`.

Set `run_tasks` for `tasks` and `both`. Set `run_posts` for `posts` and `both`.

### 1. Check gh CLI

```bash
gh --version
```
If not found: stop and instruct the user to install from https://cli.github.com.

### 2. Check authentication

```bash
gh auth status
```
If not authenticated: stop and instruct `gh auth login`.

### 3. Task setup

Run this section only when `run_tasks` is set. Posts do not require labels or a queue.

#### 3a. Upsert managed labels

```bash
~/.agents/skills/setup/scripts/manage-labels {owner}/{repo}
```

Dynamic labels (`blocked:*`) are created on demand by other skills — do not prune or migrate them.

If `.orc/config/labels` exists, `manage-labels` also treats its `name|color|description` entries as repository-managed labels.

#### 3b. Prune unmanaged labels

```bash
~/.agents/skills/setup/scripts/manage-labels {owner}/{repo} --prune
```

#### 3c. Migrate existing issue labels

```bash
~/.agents/skills/setup/scripts/migrate-labels {owner}/{repo}
```

If the script reports any unrecognized labels, reason about their intent and apply `gh issue edit` manually for those issues.

##### Label completeness check

After migration, re-fetch all open issues and check that every issue has **both** a type label (`feature` or `task`) **and** a `status:*` label. Exclude `queue` issues (the Global Queue), `posts` issues (the Post List), and `post` issues (individual blog posts managed by the post workflow) from this check.

```bash
gh issue list --repo {owner}/{repo} --state open --limit 500 \
  --json number,title,body,labels
```

For each issue missing a type label or `status:*` label (or both), read its title and body to infer the correct label(s):

- **Type inference:** does this look like a large multi-phase body of work → `feature`; otherwise → `task`
- **Status inference:** if there is a branch (`task/{number}-*`) check if a PR is open — if PR open → `status:built`, if branch exists with no PR → `status:progress`, otherwise → `status:ready`

Build a proposed assignment table. For any issue where the inference is unambiguous, add it to the confident batch. For any issue where you are uncertain, ask the user:

```
#{number} — {title}
  Missing: type   status
  Body preview: {first 80 chars of body}

  Type:   (F) feature  (T) task
  Status: (1) ready  (2) progress  (3) built  (4) defective
```

After collecting responses, show the full proposed batch and confirm:

```
Apply label completeness fixes?

  #{number} — {title}  →  task     status:ready
  #{number} — {title}  →  feature  (already has status:progress)
  ...

(y) yes  (n) skip
```

On yes, apply each fix:
```bash
gh issue edit {number} --repo {owner}/{repo} --add-label "{label}"
```

Track count of issues updated in this pass.

#### 3d. Global queue

```bash
~/.agents/skills/setup/scripts/ensure-queue {owner}/{repo}
```

#### 3e. .orc directory

Create the `.orc` directory structure if it does not exist:
```bash
mkdir -p .orc/tasks .orc/features .orc/config .orc/guides
```

- `.orc/tasks/` — one folder per in-flight task; deleted by /task-merge after squash-merge. **Gitignored.**
- `.orc/features/` — phase spec files for in-progress features; deleted by /feature-merge when complete. **Gitignored.**
- `.orc/config/` — repo-level skill configuration; committed to git.
- `.orc/guides/` — reference docs, style guides, and context the model reads during builds; committed to git.

Write `.orc/.gitignore` to ignore everything inside `.orc/` except the committed directories and the gitignore file itself:

```
*
!.gitignore
!config/
!config/**
!guides/
!guides/**
```

**Migration:** if the root `.gitignore` contains any of the old individual entries (`.orc/tasks`, `.orc/features`, `.orc/QUEUE.md`, `.orc`), remove them — they are now superseded by `.orc/.gitignore`.

```bash
sed -i '' '/^\.orc\/tasks$/d; /^\.orc\/features$/d; /^\.orc\/QUEUE\.md$/d; /^\.orc$/d' .gitignore
```

If `.orc` already exists: create any missing subdirectories and write `.orc/.gitignore` if absent, skip the rest silently.

#### 3f. CLAUDE.md

Scan the project root for commands to populate missing sections:

**`package.json`** — read the `scripts` block. Surface commands that look like test/lint/build (filter out: `dev`, `watch`, `start`, `preview`).

**`composer.json`** — read the `scripts` block. Surface relevant scripts.

**`artisan`** — if present, note `php artisan test` as available.

**`Makefile`** — if present, list relevant targets (test, lint, build).

**If `CLAUDE.md` does not exist:** build and show the full content, then confirm:
```
CLAUDE.md to be created:
{content}

(y) yes  (e) edit  (n) skip
```

On confirm: write the file.

**If `CLAUDE.md` exists:** read it. Check which of the following sections are present: `## Pre-commit Gate`. For each missing section, append it to the end of the file — do not modify or remove any existing content. If all sections are already present: skip silently.

CLAUDE.md section format:
```markdown
## Pre-commit Gate

{discovered pre-commit/lint commands, one per line — or leave empty}
```

If an `AGENTS.md` file exists in the project root, warn:
```
AGENTS.md found — CLAUDE.md is preferred. Remove AGENTS.md?
(y) yes  (n) no — leave it
```

#### 3h. PULL_REQUEST_TEMPLATE.md

Check for `.github/PULL_REQUEST_TEMPLATE.md` in the repo.

**If it does not exist:** create `.github/` if needed, then copy from `~/.agents/skills/setup/templates/pull-request-template.md`.

**If it already exists:** compare it against `~/.agents/skills/setup/templates/pull-request-template.md`.

- If identical: skip silently.
- If different: show a diff and prompt:
  ```
  PULL_REQUEST_TEMPLATE.md differs from the skill template.
  (u) update to match  (k) keep existing  (v) view full diff
  ```
  On `(v)`: display the full diff, then return to this prompt.

#### 3i. CHANGELOG.md

Check for `CHANGELOG.md` in the project root.

If it does not exist: copy from `~/.agents/skills/setup/templates/changelog.md`, replacing `{owner}` and `{repo}` with the actual values.

If it already exists: skip silently.

#### 3j. dependabot.yml

Check for `.github/dependabot.yml` in the repo.

**If it already exists:** skip silently.

**If it does not exist:** detect the primary package ecosystem from the project root:
- `package.json` present → `npm`
- `composer.json` present → `composer`
- `pyproject.toml` or `requirements.txt` present → `pip`
- None found → omit the first entry, keep only `github-actions`

Copy from `~/.agents/skills/setup/templates/dependabot.yml`, replacing `{package-ecosystem}` with the detected value. If no package ecosystem was found, remove that block entirely.

```bash
mkdir -p .github
cp ~/.agents/skills/setup/templates/dependabot.yml .github/dependabot.yml
# (then edit in place to set the correct ecosystem)
```

#### 3k. QUEUE.md

Add `.orc/QUEUE.md` to `.gitignore` if not already present:

Generate the initial queue file by invoking the `queue-sync` agent. Pass `{owner}/{repo}`.

#### 3L. Queue reset (reset-queue mode only)

Skip this section unless `reset-queue` mode is active. In `reset-queue` mode, run only this section and then jump to section 6 (Report).

##### 3L-1. Find the Global Queue issue

```bash
gh issue list --repo {owner}/{repo} --state open --label "queue" \
  --json number,title,body --jq '.[] | select(.title == "Global Queue")'
```

If not found, stop:
```
Global Queue issue not found. Run /setup first to create it.
```

##### 3L-2. Fetch all open task and feature issues

```bash
gh issue list --repo {owner}/{repo} --state open --limit 500 \
  --json number,title,labels
```

Filter to issues that have a `task` or `feature` label. Exclude any issue with a `queue`, `posts`, or `post` label.

For each issue, extract:
- issue number
- title
- type: `task` or `feature`
- status: the value of the `status:*` label (strip `status:` prefix); if none, use `ready`

##### 3L-3. Sort by priority

Sort issues into the following priority tiers, then by issue number ascending within each tier:

1. `progress` — actively being worked
2. `built` — PR open, awaiting merge
3. `defective` — PR has issues to fix
4. `ready` — queued and ready to start
5. `draft` — spec not yet written

For feature issues, prefix the status with `feature/` (e.g. `feature/progress`, `feature/draft`). Apply the same tier ordering based on the underlying status value.

##### 3L-4. Show the proposed order and confirm

Display the sorted list:

```
Proposed queue order:

  42  Add user authentication         progress
  38  Fix login redirect bug           ready
  51  Storefront                       feature/draft
  ...

Reset the Global Queue issue and QUEUE.md to this order? (y/n)
```

Stop on anything other than a clear confirmation.

##### 3L-5. Rebuild the Queue issue

Compute column widths from the longest value in each column (including the header), then pad every cell to that width. Build the table:

```
## Queue

| #   | Name                            | Status          |
| --- | ------------------------------- | --------------- |
| 42  | Add user authentication         | progress        |
| 38  | Fix login redirect bug          | ready           |
| 51  | Storefront                      | feature/draft   |
```

Replace the entire body of the Global Queue issue with this content:

```bash
gh issue edit {queue-issue-number} --repo {owner}/{repo} --body-file {temp_file}
```

##### 3L-6. Write QUEUE.md

Write the same padded table to `.orc/QUEUE.md`, creating `.orc/` if it does not exist.

Report the number of issues written and the queue issue URL.

---

### 4. Post setup

Run this section only when `run_posts` is set.

#### 4a. Ensure configuration directory

```bash
mkdir -p .orc/config
```

If `.orc` is ignored wholesale, replace that exact ignore entry with `.orc/tasks` so `.orc/config` can be committed. Do not add `.orc/tasks` to `.gitignore` in posts-only mode unless `.orc/tasks` exists.

#### 4b. Choose the posts directory

If `.orc/config/posts.config.json` exists, parse it with a JSON parser and show the current `posts_dir`. Ask whether to keep it or change it. Default to keeping it.

Otherwise, ask for a repository-relative posts directory, suggesting `platform/resources/posts` only as an example. Reject absolute paths and paths containing `..`. Normalize away leading `./` and trailing `/`. Create the directory if it does not exist.

Do not write the final config until the Post List issue number is known.

#### 4c. Create editorial guidelines

If `.orc/guides/editorial-guidelines.md` already exists and is non-empty, preserve it. Offer to review or update it, but do not overwrite it silently.

Otherwise, conduct a brief interview of two or three exchanges covering:

- brand or publication purpose
- target audience and reader problems
- primary topics and desired outcomes
- tone, boundaries, and subjects or claims to avoid

Draft `.orc/guides/editorial-guidelines.md` with concise sections for Brand Purpose, Audience, Content Priorities, Voice and Tone, Editorial Standards, and Avoid. Show the draft and let the user confirm or revise it before writing.

#### 4d. Create writing-style placeholder

If `.orc/guides/writing-style.md` does not exist, create it with:

```markdown
# Writing Style

<!-- Add representative writing samples and notes about sentence structure, voice, vocabulary, pacing, and recurring habits before running /post-write. -->
```

If the file already exists, preserve it exactly. Never replace populated writing samples with the placeholder.

#### 4e. Ensure the Post List issue

If the existing config contains `post_list_issue`, verify that issue exists in `{owner}/{repo}` and its title is `Post List`. Reuse it when valid.

If no valid configured issue exists, search open and closed issues for an exact `Post List` title. If exactly one exists, ask whether to reuse it. If multiple exist, show their numbers and let the user choose. Do not create a duplicate without confirmation.

When creating a new issue, use the empty body at `~/.agents/skills/setup/templates/post-list.md`:

```bash
gh issue create --repo {owner}/{repo} \
  --title "Post List" \
  --body-file ~/.agents/skills/setup/templates/post-list.md
```

Capture the issue number from the command output or re-fetch the exact issue. Do not add task or post labels.

#### 4f. Write posts config

Write `.orc/config/posts.config.json` through a JSON serializer with exactly:

```json
{
  "posts_dir": "{posts_dir}",
  "post_list_issue": {issue_number}
}
```

Use two-space indentation and a trailing newline. Preserve an existing valid issue number when reusing its issue.

### 5. Commit and PR

If no local files were created or modified during this run: skip to step 6. GitHub-only changes, such as creating the Post List issue, do not require an empty commit.

#### 5a. Branch

```bash
git checkout -b setup
```

If the branch already exists locally, use it.

#### 5b. Stage and commit

```bash
git status --short
git add {only files created or modified by this setup run}
git commit -m "chore: configure skill workflows"
git push -u origin setup
```

Do not stage unrelated user changes. Include `.orc/config/posts.config.json`, `.orc/guides/editorial-guidelines.md`, and `.orc/guides/writing-style.md` when posts setup created or changed them.

#### 5c. Open PR

```bash
gh pr create --repo {owner}/{repo} \
  --base main \
  --head setup \
  --title "chore: setup scaffold" \
  --body "## Summary

Automated setup via \`/setup {mode}\`:
{include only completed task setup actions when run_tasks is set}
{include posts directory, editorial guidelines, writing style, and Post List issue when run_posts is set}

_Generated by /setup_"
```

#### 5d. Wait for Copilot review

```bash
~/.agents/skills/task-build/scripts/wait-for-pr-review {owner}/{repo} {pr} --interval 15 --timeout 180
```

If timed out (exit 1): proceed to merge.

If a review is found: apply simple, safe fixes silently (formatting, wording, obvious config corrections) and commit (`fix: address Copilot review feedback`), push. **Stop and report** if any comment touches logic or has unclear intent — wait for direction before merging.

#### 5e. Merge

```bash
gh pr merge {pr} --repo {owner}/{repo} --squash
git checkout main
git branch -D setup
git pull origin main
```

---

### 6. Report

```
setup complete for {owner}/{repo}:
```

Report the selected mode and only actions actually completed or reused. In posts or both mode, include:

- configured `posts_dir`
- Post List issue number and URL
- paths to `posts.config.json`, `editorial-guidelines.md`, and `writing-style.md`
- whether each file was created, updated, or preserved

Always end posts or both mode with:

```text
Before running /post-write, replace the placeholder in .orc/guides/writing-style.md with representative writing samples. Draft quality depends on this file.
```
