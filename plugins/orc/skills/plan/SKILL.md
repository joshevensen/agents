---
name: plan
description: Turn a feature plan doc into ordered task issues, each with a build-ready spec. Feature-flag setup is always task #1. Runs autonomously when the doc's Open Questions are resolved. Invoke as /orc:plan F001.
model: sonnet
---

`plan` fans a feature doc out into the task issues that `/orc:build` will implement one at a time. It writes the issue numbers back into the doc, which stays the feature's tracker. It runs unattended when the plan is complete — but stops rather than invent scope.

## Steps

### 0. Load the feature

Require a feature id (`F###`). Read `.orc/features/{id}-*.md`. Parse the frontmatter (`flag`, `status`) and the **Tasks (in order)** list.

### 1. Detect mode

```bash
echo "${ORC_AUTONOMOUS:-0}"
```

### 2. Readiness check

If **Open Questions** is not `None.`:
- **Interactive:** work through them with the user and update the doc.
- **Autonomous:** stop. Report that `{id}` has unresolved Open Questions and cannot be planned unattended. (Features have no issue to comment on — this is reported, not gated onto an issue.)

Confirm task #1 is the `{flag}` feature-flag setup. If missing, insert it.

### 3. Generate specs (parallel)

For each task in the list **that does not yet have an issue number** (fresh runs: all of them; re-runs: only new ones), invoke `spec-writer` in parallel. Pass each:
- **Type:** `task`
- **Context:** the full feature doc + this task's line/scope. For task #1, the context is "register the `{flag}` Pennant flag" — a small, mechanical spec.
- **Output:** `.orc/tmp/{id}-{i}-spec.md`

### 4. Create the issues

For each generated task, in order:

```bash
gh label create "type:task" -f >/dev/null 2>&1 || true
n=$(gh issue create --title "{task title}" \
  --body "Part of feature {id}. {one-line intent}" \
  --label "type:task,status:ready" --json number --jq .number)
gh issue comment $n --body-file .orc/tmp/{id}-{i}-spec.md
```

If a task's spec still has Open Questions, create it `status:draft` instead of `status:ready` and note it.

### 5. Update the tracker

Write each new issue number into the doc's **Tasks (in order)** checklist (`- [ ] #{n} — {title}`), set frontmatter `status: planned`, and remove the scratch specs (`rm .orc/tmp/{id}-*-spec.md`).

### 6. Report

```
Feature {id} planned — {k} task issues created.
Build them in order: /orc:build {id} (repeats to pick up the next after each merge).
```
