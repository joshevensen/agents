---
name: plan
description: Take a draft issue from /orc:create, explore the codebase, choose a technical approach, and write a build-ready spec onto the issue. Sets status:ready when the spec is complete. Invoke as /orc:plan {number}.
model: sonnet
---

`plan` turns a scoped issue into a buildable one. It reads the issue `create`
produced, researches the codebase, decides how to implement it, and writes the
spec as a comment on the issue. It owns all spec-writing — the logic that used
to live in both `create` and the old feature-planning step now lives here alone.

## `--dry-run`

`/orc:plan {number} --dry-run` runs research, spec-writing, and open-question
resolution exactly as normal — `spec-writer` only writes to the local
`.orc/tmp/{number}-spec.md` scratch file, which is safe to leave in place for
inspection (skip the `rm` in step 5 too, so you can read it after). Skip every
`gh issue edit`/`gh issue comment` call in steps 1 and 5. End with:
```
DRY RUN — spec written to .orc/tmp/{number}-spec.md, not posted.
{Open Questions: None. — would set status:ready | still open: {what's open}}
Re-run without --dry-run to post it.
```

## Steps

### 1. Load the issue

Require an issue number (`/orc:plan {number}`). Invoke `issue-loader` with it.
Use the returned title, body, labels, and any existing spec comment.

Set it to `status:draft` while a spec is being written or revised. Create
both labels defensively first — idempotent, a no-op once `/orc:setup` or a
prior run has already made them, but `--add-label` 404s on a label that's
never existed in the repo at all:

```bash
gh label create "status:draft" -f >/dev/null 2>&1 || true
gh label create "status:ready" -f >/dev/null 2>&1 || true
gh issue edit {number} --remove-label "status:ready" --add-label "status:draft" 2>/dev/null || \
  gh issue edit {number} --add-label "status:draft"
```

### 2. Research the codebase

Explore what already exists before choosing an approach. Read `CLAUDE.md` for
conventions and the project's `## Verification` / `## Focused Verification`
commands. Focus on whatever the work touches:

- models, migrations, and schema in scope
- routes, controllers, services, jobs, or integrations in scope
- frontend patterns, if UI is touched
- existing tests that reveal expected behavior of related code

You are choosing the technical approach: what to build on, which conventions to
follow, and every non-obvious constraint the implementer needs.

### 3. Write the spec

Invoke `spec-writer`, passing the issue body (scope and intent from `create`),
whether it's a bug (`type:bug` present), and an output path of
`.orc/tmp/{number}-spec.md`. It fills `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`.

**Every path the spec cites must actually exist** — a phantom path trips
`build`'s confidence gate.

### 4. Resolve open questions

Read the drafted spec and surface its **Open Questions** and any acceptance
criterion that isn't cleanly machine-verifiable. Work through them with the
user, folding answers back into the spec, until **Open Questions reads `None.`**
and every acceptance criterion is tied to a test, command, or observable
outcome. This is the gate — the same one `build` re-checks. Do not weaken it.

### 5. Post the spec and set status

```bash
gh issue comment {number} --body-file .orc/tmp/{number}-spec.md
rm .orc/tmp/{number}-spec.md
```

- **Open Questions is `None.` and every criterion is verifiable**:
  ```bash
  gh label create "status:ready" -f >/dev/null 2>&1 || true
  gh issue edit {number} --remove-label status:draft --add-label status:ready
  ```
- **Anything still open** → leave `status:draft` and tell the user what remains.

### 6. Report

```
#{number} specced — {ready to build | still draft: {what's open}}.
Next: /orc:build {number}.
```
