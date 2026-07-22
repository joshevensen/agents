---
name: create
description: Discuss an idea at the product/scope level and produce one or more GitHub issues — no spec-writing. Splits work into separate issues when it's naturally independent. Ends only when every open question is resolved. Interactive and local.
model: sonnet
---

`create` is the human-judgment front of the pipeline. You talk an idea through
at the product and scope level, then produce the GitHub issue(s) that `/orc:plan`
will later spec. It does **not** write specs and it does **not** explore the
codebase for implementation detail — that is `plan`'s job. Its one hard rule:
**it never ends with an unresolved open question.** Ask freely while discussing,
but every issue it creates reads `Open Questions: None.`

## `--dry-run`

`/orc:create --dry-run` runs the full discussion and open-question resolution
normally — nothing there touches GitHub anyway. At step 4, skip the label
self-provisioning and `gh issue create` calls; instead show each issue exactly
as it would be filed (title, body, labels) and stop:
```
DRY RUN — would create {n} issue(s):

  {title} [labels: {labels}]
  {body}
  ...

Re-run without --dry-run to file them.
```

## Steps

### 1. Discuss

Ask what the user wants and why. Read files or grep only enough to ground the
conversation in what exists (does this route/model already exist? is there a
similar feature to point at?) — this is scoping, not spec research. Aim for 2–4
exchanges and capture:

- what should change, from the user's perspective
- why it matters
- scope boundaries — what's explicitly in and out
- constraints and context the plan step will need

Don't over-interview. If the first message is already clear, move on.

### 2. Resolve every open question

As questions surface — scope, priority, expected behavior, edge cases — raise
them and get answers. **The discussion is not finished while any raised question
is unanswered.** This is the same standard `plan`'s spec gate holds specs to,
applied one stage earlier so `plan` inherits a clean scope.

### 3. Decide whether to split

If the discussion reveals genuinely separable pieces of work — independent
deliverables that could ship on their own — create one issue per piece.
Splitting is part of the discussion, not a separate step.

**There is no size threshold that forces a split.** A large but cohesive change
is one issue; `build` handles issues of any size. Split only when the work is
naturally independent, never because a single issue looks "too big."

### 4. Create the issue(s)

For each issue, write a body that captures the discussion at the scope level:
what should change, why, what's in and out of scope, and any constraints `plan`
needs. End the body with an `## Open Questions` section reading `None.` — every
issue leaves discussion fully resolved. Do **not** write a spec; the issue has
no acceptance criteria or file lists yet.

Apply `type:bug` when the work is a defect (so `plan` knows to spec a
reproduction and a regression test). Otherwise no type label.

```bash
# labels self-provision (idempotent)
gh label create "status:draft" -f >/dev/null 2>&1 || true
gh label create "type:bug"     -f >/dev/null 2>&1 || true   # bugs only

# gh issue create has no --json/--jq — it prints only the issue URL, so pull
# the number from that
url=$(gh issue create --title "{title}" --body "{body with Open Questions: None.}" \
  --label "status:draft{,type:bug if a defect}")
number=$(basename "$url")
```

Every issue starts at `status:draft` — it has a resolved scope but no spec yet.

### 5. Report

```
Created {n} issue(s):
  #{number} — {title}
  ...

Next: /orc:plan {number} to research the codebase and write the spec.
```

If several issues were split from one discussion, note the relationship between
them (e.g. "#12 must land before #13") so `plan`/`build` order is clear.
