---
name: task-create
description: Interview → create issue → research codebase → generate spec → review → post. Leaves the issue at status:ready for /task-build. Pass /task-create {number} to re-spec an existing issue.
model: sonnet
---

## Steps

### 0. Resolve mode

If an issue number was passed as an argument:

- Load the issue using the `issue-loader` agent. Pass the issue number and `{owner}/{repo}`.
- Set `{number}`, `{title}`, `{description}`, `{owner}`, and `{repo}` from the returned metadata.
- Update status to signal the spec is being revised:
  ```bash
  gh issue edit {number} --repo {owner}/{repo} \
    --remove-label "status:ready" \
    --add-label "status:draft"
  ```
- Skip steps 1–5 and continue from **step 6 (Generate spec)**.

Otherwise, continue to step 1.

---

### 1. Interview

Ask the user to describe what they want done. Use your tools (Read, Grep, Glob, Bash) actively during the interview — look up relevant code, routes, models, or configuration when the user mentions specific files or functionality. Surface constraints or existing patterns that affect what needs to be done before asking follow-up questions.

Use follow-up questions to capture enough to write a clear, buildable task description. Aim for 2–4 exchanges — stop when you have:

- What needs to happen
- Why it matters (even briefly)
- Any constraints, context, or known unknowns worth preserving

Do not over-interview. If the first message is already clear enough, move straight to step 2.

---

### 2. Draft and save locally

Derive a short action-oriented title (73 characters max) and write a one-to-three paragraph description.

```bash
mkdir -p .orc/tasks
```

Write to `.orc/tasks/{slug}.md` (slug = lowercase title, spaces replaced with `-`, non-alphanumeric stripped) using `${CLAUDE_PLUGIN_ROOT}/skills/task-create/templates/task-draft.md` as the structure, filling in `{title}`, `{type}`, and `{description}`.

Report:
```
Draft saved: .orc/tasks/{slug}.md
Say "post" when it's ready to create.
```

Wait for the user. Discuss or revise as needed. When the user says "post", read `.orc/tasks/{slug}.md` for the final title, type, and description, then continue.

---

### 3. Create issue

```bash
gh issue create --repo {owner}/{repo} \
  --title "{title}" \
  --body "{description}" \
  --label "status:draft,task"
```

Note the issue number. Delete the local draft:
```bash
rm .orc/tasks/{slug}.md
```

---

### 4. Queue placement

```
Add to queue?
(t) top
(b) bottom
(a) after a specific item — show me the queue
(n) skip
```

On `(a)`: display the current global queue with numbered lines and ask `Insert after which item?`.

On `(t)`: prepend. On `(b)`: append. On `(n)`: skip.

Queue entry format:
```
- [ ] #{number} — {title}
```

---

### 5. Queue sync

Invoke the `queue-sync` agent in the background. Pass `{owner}/{repo}`. Do not wait for it to complete.

---

### 6. Generate spec

Create the output directory:
```bash
mkdir -p .orc/tasks/{number}-{slug}
```

Invoke the `spec-writer` agent. Pass the following prompt:

```
## Mode
task

## Issue
#{number} — {title}

## Description
{issue body}

## Output path
.orc/tasks/{number}-{slug}/spec.md
```

The agent researches the codebase and writes the spec directly to the output path.

---

### 7. Review

Read `.orc/tasks/{number}-{slug}/spec.md`. Output a structured review:

```
Spec: .orc/tasks/{number}-{slug}/spec.md

SUMMARY
{1–2 sentences: what the spec is asking for and why}

CODEBASE CONTEXT
{key files from the Codebase Touchpoints section — confirm these are the right areas}
{any constraint or pattern the user should validate}

NEEDS YOUR INPUT
{every assumption, ambiguity, or LOW-confidence criterion needing confirmation — or "None."}
```

If any LOW-confidence criteria or open questions exist, do not suggest posting until addressed.

Wait for the user. Discuss or revise as needed. When the user says "post", continue.

---

### 8. Post spec

```bash
gh issue comment {number} --repo {owner}/{repo} \
  --body-file .orc/tasks/{number}-{slug}/spec.md
```

---

### 9. Update status

```bash
gh issue edit {number} --repo {owner}/{repo} \
  --remove-label "status:draft" \
  --add-label "status:ready"
```

---

### 10. Report

```
Task #{number} — {title}
Spec posted. Issue is status:ready.

Run /task-build {number} to implement.
```
