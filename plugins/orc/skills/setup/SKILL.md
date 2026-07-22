---
name: setup
description: Wire a repo for orc — labels, .orc directory, CLAUDE.md verification sections, PR template, CHANGELOG, and dependabot. Idempotent — safe to re-run.
model: sonnet
---

The day-to-day loop (`create`, `plan`, `build`, `resume`, `push`, `list`)
self-provisions its own labels — each defensively `gh label create`s a bare
version of any `status:*` label right before it's first needed — and needs no
setup to work in a fresh repo. That self-provisioning is intentionally minimal
(no color or description); `setup` still owns the canonical color/description
for the full managed set, so it's worth running even on a repo where every
label already exists — it upgrades bare, defensively-created labels to the
real thing rather than leaving them as whatever GitHub's default looks like.
`setup` also handles the few pieces of idempotent scaffolding that are more
reliably done as one command than a manual checklist — most importantly the
`CLAUDE.md` verification sections that make `build` project-agnostic.

## `--dry-run`

`/orc:setup --dry-run` still writes every local file it would normally write
— `CLAUDE.md` sections, the PR template, `CHANGELOG.md`, `dependabot.yml`,
`.orc/` — since previewing exactly those files is the point, and none of it
is pushed. Pass `--dry-run` through to both label scripts in step 2 (they
support it directly and print what would change instead of calling `gh
label`). Skip step 8 entirely — nothing gets committed, pushed, or handed to
`/orc:push`. End with:
```
DRY RUN — files written for review: {list}. Labels: see step 2 output above.
Nothing committed or pushed. Re-run without --dry-run to commit and open a PR.
```

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
${CLAUDE_PLUGIN_ROOT}/skills/setup/scripts/migrate-labels {owner}/{repo}
```

Upsert and migrate are safe to run every time — both only ever create, edit,
or remap, never delete. **Don't run `manage-labels --prune` as part of this
default flow** — it deletes any label outside the managed set (anything you
added yourself included; only `blocked:*` and `github-actions` are exempt),
and doing that unconditionally on every `/orc:setup` run would silently eat a
custom label the moment someone adds one. If the user explicitly asks to
clean up unmanaged labels, run `--prune` then, as its own deliberate step —
never bundle it into a routine setup run.

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

**If `CLAUDE.md` already has a `## CI-Only Verification` section, skip this
entirely** — same rule as the two sections above, never re-propose or touch
something already there. Otherwise, while scanning, also check for heavy/slow
suites — `playwright.config.*`, `cypress.config.*`, or script names containing
`e2e`/`playwright`/`cypress`/`browser`. If found, propose a third, optional
section (same show/confirm flow; skip silently if declined or nothing heavy is
found — `build` doesn't gate on this one):
```
## CI-Only Verification
Suites listed here are never run by `build`, not even scoped — CI is the
only place they execute:
  - Playwright end-to-end tests (`npm run test:e2e`) — slow, browser-driven
```
Note in the final report (step 9) that repos pushing per-wave commits to a
draft PR (see `build` step 5) may want their CI workflow to skip these heavy
jobs while the PR is draft (`if: github.event.pull_request.draft == false`)
— but don't edit the repo's CI workflow files to add this; that's much more
invasive than a `CLAUDE.md` section and varies too much by provider to do
safely from here.

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
