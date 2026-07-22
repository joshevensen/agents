---
name: setup
description: Wire a repo for orc — labels, .orc directory, CLAUDE.md verification sections, PR template, CHANGELOG, and dependabot. Idempotent — safe to re-run.
model: sonnet
---

The day-to-day loop (`create`, `plan`, `build`, `push`, `list`) self-provisions
its own labels and needs no setup to work in a fresh repo. `setup` handles the
few pieces of idempotent scaffolding that are more reliably done as one command
than a manual checklist — most importantly the `CLAUDE.md` verification sections
that make `build` project-agnostic.

## Steps

### 0. Resolve `{owner}/{repo}`

Run from inside the project directory. Infer from `git remote get-url origin`,
or accept an `owner/repo` argument.

### 1. Preflight

```bash
gh --version
gh auth status
```

If either fails, stop with instructions:
- **Local:** install from https://cli.github.com, or run `gh auth login`.
- **Claude Code on the web:** `gh` isn't preinstalled and must be added to the
  environment's **Setup script** — see the web-install section of the orc README.
  It auto-authenticates via the `GH_TOKEN` web environments already expose, so no
  `gh auth login` is needed once installed.

### 2. Labels

```bash
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/manage-labels {owner}/{repo}
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/manage-labels {owner}/{repo} --prune
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/migrate-labels {owner}/{repo}
```

If migration reports unrecognized labels, reason about intent and apply
`gh issue edit` manually.

**Completeness check:** re-fetch open issues; any missing a `status:*` label gets
one inferred and confirmed with the user before applying.

### 3. `.orc/` directory

```bash
mkdir -p .orc/tmp
```

`.orc/tmp/` holds scratch specs `plan` writes before posting them to an issue.
**Gitignored.** Write `.orc/.gitignore`:
```
tmp/
```

**Migration:** if the root `.gitignore` or `.orc/.gitignore` still lists old
entries (`.orc/tasks`, `.orc/features`, `.orc/QUEUE.md`, a wholesale `.orc`),
remove them. If a `.orc/features/` directory exists from a prior orc version,
note it to the user — features are gone; those docs are no longer read.

### 4. `CLAUDE.md` verification sections

`build` reads two sections from `CLAUDE.md` for its project-specific commands —
this is what makes the plugin project-agnostic:

- **`## Verification`** — the full-suite test/lint/build commands (CI's job, and
  the fallback `build` scopes down from).
- **`## Focused Verification`** — the command shape for running a *filtered*
  subset: only the tests around what changed. `build` prefers this at every
  point (per wave, pre-commit, pre-PR); the full suite is left to CI. The exact
  command is per-repo/per-language — a PHPUnit `--filter`, `pytest -k {expr}`, a
  JS test-path arg — so record the pattern the repo uses, e.g.:
  ```
  ## Focused Verification
  Run only the tests covering changed files:
    php artisan test --filter '{ClassOrMethod}'
  ```

Scan the project root for test/lint/build commands (`package.json` scripts,
`composer.json` scripts, `artisan`, `Makefile`), filtering out
`dev`/`watch`/`start`/`preview`.

**If `CLAUDE.md` doesn't exist:** draft it with the discovered commands under
both sections, show it, and confirm (`y` / `e` edit / `n` skip) before writing.

**If it exists:** append whichever of the two sections is missing, without
touching existing content.

`build` gates on `## Verification` (or `## Focused Verification`) being present;
without them it gates immediately on every issue.

### 5. PR template

Compare `.github/PULL_REQUEST_TEMPLATE.md` against
`${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/pull-request-template.md`. Create
if missing; if different, show a diff and ask `(u) update  (k) keep`.

### 6. CHANGELOG.md

Create from `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/changelog.md` if
absent. Skip silently if present.

### 7. dependabot.yml

Create `.github/dependabot.yml` from
`${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/dependabot.yml` if absent, filling
in the detected ecosystem (`package.json`→npm, `composer.json`→composer,
`pyproject.toml`/`requirements.txt`→pip). Skip silently if present.

### 8. Commit and open a PR

If nothing was created or modified locally, skip to step 9 — GitHub-only changes
(labels) need no commit.

```bash
git status --short
```

Stage only files this setup run touched, then hand off to `/orc:push` with the
message `chore: configure orc` to commit, review, and open the PR. Merge it
yourself.

### 9. Report

```
setup complete for {owner}/{repo}:
{only actions actually completed or reused}
```
