---
name: create
description: Discuss an idea, confirm whether it's a task, bug, or feature, then produce the right artifact — a task/bug issue with a spec, or a feature plan doc. Interactive and local. Pass /orc:create {number} to re-spec an existing issue.
model: sonnet
---

`create` is the human-judgment front of the pipeline. You talk through an idea; it researches the codebase, **proposes a type and confirms it with you**, then creates either a GitHub issue (task/bug) with a build-ready spec, or a feature plan doc that `/orc:plan` later fans out into tasks. It never guesses the type silently, and it never posts a spec with unresolved questions.

## Steps

### 0. Resolve mode

If a number is passed (`/orc:create {number}`), this is a **re-spec** of an existing issue:
- Load it with `issue-loader`.
- Set it to `status:draft` (a spec is being revised).
- Skip to step 3 (Draft the spec) using its existing type.

Otherwise continue.

### 1. Discuss

Ask what the user wants done. Use Read/Grep/Glob/Bash actively — look up the routes, models, files, or config they mention and surface existing patterns or constraints. Aim for 2–4 exchanges; capture:
- what needs to happen
- why it matters
- constraints, context, and known unknowns

Don't over-interview. If the first message is already clear, move on.

### 2. Classify — and confirm

Propose exactly one type, with a one-line reason, and **wait for confirmation**:

- **task** — a single, bounded change.
- **bug** — something is broken; needs reproduction steps and a regression test.
- **feature** — spans multiple tasks / subsystems. Becomes a plan doc, not an issue.

```
This looks like a {type} — {reason}. Confirm, or tell me otherwise.
```

If the user disagrees, reclassify. On confirmation, branch: **feature → step 5**; task/bug → step 3.

### 3. Draft the spec (task / bug)

Invoke `spec-writer`, passing the type (`task`/`bug`), the discussion context, and an output path of `.orc/tmp/{slug}-spec.md`. It researches and fills `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`.

### 4. Resolve, then post (task / bug)

Read the drafted spec and surface its **Open Questions** and any acceptance criterion that isn't cleanly verifiable. Work through them with the user, folding answers back into the spec, until Open Questions reads `None.`

Then create the issue and attach the spec:

```bash
# labels self-provision (idempotent)
gh label create "type:{type}" -f >/dev/null 2>&1 || true
gh label create "status:draft" -f >/dev/null 2>&1 || true
gh label create "status:ready" -f >/dev/null 2>&1 || true

number=$(gh issue create --title "{title}" --body "{problem statement}" \
  --label "type:{type},status:draft" --json number --jq .number)
gh issue comment $number --body-file .orc/tmp/{slug}-spec.md
```

- **Open Questions is `None.`** → `gh issue edit $number --remove-label status:draft --add-label status:ready`.
- **Questions remain** → leave `status:draft`; tell the user what's still open.

Remove the scratch file (`rm .orc/tmp/{slug}-spec.md`). Report the issue number and whether it's ready to build.

### 5. Feature plan doc

Allocate the next id:
```bash
mkdir -p .orc/features
next=$(ls .orc/features 2>/dev/null | grep -oE '^F[0-9]+' | sort | tail -1)
# F001 if none, else increment and zero-pad to 3 digits
```

Discuss the feature enough to fill `${CLAUDE_PLUGIN_ROOT}/templates/feature-plan.md`: overview, goal, scope/out-of-scope, the Pennant flag key, and a first-cut ordered task list (task #1 is always flag setup). Write it to `.orc/features/{id}-{slug}.md` with `status: draft`.

Report:
```
Feature {id} — {title}
Plan: .orc/features/{id}-{slug}.md
Run /orc:plan {id} when the plan is solid to break it into task issues.
```
