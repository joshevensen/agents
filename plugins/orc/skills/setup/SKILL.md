---
name: setup
description: Wire a repo for orc — labels, .orc directory, AGENTS.md gate sections, PR template, CHANGELOG, dependabot, and (the main event) the GitHub Actions workflow + OAuth secret that make @claude implement work. Idempotent — safe to re-run.
model: sonnet
---

The day-to-day loop (`create`, `build`, `push`, `drafts`, `ready`) self-provisions its own labels and needs no setup to work in a fresh repo. `setup` exists for the one thing that can't self-provision: turning on **autonomous builds** — the `@claude` comment trigger, wired through GitHub Actions to your Claude subscription.

## Steps

### 0. Resolve `{owner}/{repo}`

Run from inside the project directory. Infer from `git remote get-url origin`, or accept an `owner/repo` argument.

### 1. Preflight

```bash
gh --version
gh auth status
```

If either fails, stop with instructions (install from https://cli.github.com, or run `gh auth login`).

### 2. Labels

```bash
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/manage-labels {owner}/{repo}
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/manage-labels {owner}/{repo} --prune
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/migrate-labels {owner}/{repo}
```

If migration reports unrecognized labels, reason about intent and apply `gh issue edit` manually.

**Completeness check:** re-fetch open issues; any missing a `type:*` or `status:*` label gets one inferred (a large multi-file body reads as a candidate for a feature plan rather than a task — flag it instead of guessing) and confirmed with the user before applying.

### 3. `.orc/` directory

```bash
mkdir -p .orc/features .orc/tmp
```

- `.orc/features/` — feature plan docs. **Committed** — this is the feature tracker.
- `.orc/tmp/` — scratch specs `create`/`plan` write before posting to an issue. **Gitignored.**

Write `.orc/.gitignore`:
```
tmp/
```

**Migration:** if the root `.gitignore` has old entries (`.orc/tasks`, `.orc/features`, `.orc/QUEUE.md`, a wholesale `.orc`), remove them — `.orc/features` must be trackable now, and `.orc/.gitignore` supersedes the rest.

### 4. `AGENTS.md`

`/orc:build` and `/orc:push` read `## Verification` and `## Pre-commit Gate` from `AGENTS.md` for every project-specific command — this is what makes the plugin project-agnostic. Without it, `build` gates immediately on every issue.

Scan the project root for test/lint/build commands (`package.json` scripts, `composer.json` scripts, `artisan`, `Makefile`), filtering out `dev`/`watch`/`start`/`preview`.

**If `AGENTS.md` doesn't exist:** draft it with the discovered commands under both sections, show it, and confirm (`y`/`e` edit/`n` skip) before writing.

**If it exists:** append any of the two sections that are missing, without touching existing content.

If `CLAUDE.md` exists and `AGENTS.md` doesn't, offer to symlink `AGENTS.md → CLAUDE.md` rather than duplicating — build only needs the sections to resolve from `AGENTS.md`.

### 5. PR template

Compare `.github/PULL_REQUEST_TEMPLATE.md` against `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/pull-request-template.md`. Create if missing; if different, show a diff and ask `(u) update  (k) keep`.

### 6. CHANGELOG.md

Create from `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/changelog.md` if absent. Skip silently if present.

### 7. dependabot.yml

Create `.github/dependabot.yml` from `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/dependabot.yml` if absent, filling in the detected ecosystem (`package.json`→npm, `composer.json`→composer, `pyproject.toml`/`requirements.txt`→pip). Skip silently if present.

### 8. GitHub Actions — autonomous builds

This is the step that turns on `@claude implement this`.

#### 8a. Workflow file

Copy `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/github-actions-workflow.yml` to `.github/workflows/orc-build.yml` if it doesn't already exist. Replace `{marketplace_owner}/{marketplace_repo}` with the actual marketplace repo (ask if not inferable from `git remote`).

The template's `steps:` has a placeholder comment marking where to add this project's dependency-install and environment-prep steps (composer/npm/pip install, `.env` setup, asset build — whatever the project needs). Find the project's own CI workflow (commonly `.github/workflows/ci.yml`) and mirror its proven setup steps there, inserted between `checkout` and the `claude-code-action` step. Skipping this leaves `build`'s Verification/Pre-commit Gate commands running against a bare checkout with no installed dependencies — they will fail immediately on every autonomous run.

#### 8b. Claude GitHub App

Check whether the Claude GitHub App is installed on `{owner}/{repo}`:
```bash
gh api repos/{owner}/{repo}/installation 2>/dev/null
```
If not, instruct the user to run `/install-github-app` in a local Claude Code session, or install manually from the GitHub App settings.

#### 8c. OAuth token secret

Ask whether `CLAUDE_CODE_OAUTH_TOKEN` is already set:
```bash
gh secret list --repo {owner}/{repo} | grep -q CLAUDE_CODE_OAUTH_TOKEN
```

If missing, instruct:
```
Run locally (not here — this prints a token you must copy):
  claude setup-token

Then store it:
  gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo {owner}/{repo}

This authenticates the Action against your Claude subscription — no API key, no per-token billing.
```

Do not attempt to run `claude setup-token` or handle the token value yourself.

### 9. Commit and open a PR

If nothing was created or modified locally, skip to step 10 — GitHub-only changes (labels) need no commit.

```bash
git status --short
```

Stage only files this setup run touched, then hand off to `/orc:push` with the message `chore: configure orc workflow` to commit, review, and open the PR. Merge it yourself.

### 10. Report

```
setup complete for {owner}/{repo}:
{only actions actually completed or reused}
```

If step 8 is fully wired (workflow file + App + secret): `@claude implement this` is now live on any status:ready issue. Otherwise list what's still needed.
