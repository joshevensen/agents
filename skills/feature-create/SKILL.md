---
name: feature-create
description: Plan a feature through back-and-forth discussion, building a detailed feature document iteratively. Posts the document as a GitHub issue when done. Run /feature-plan {number} when ready to break it into phases.
model: opus
---

## Purpose

`feature-create` is a sustained conversation that produces a thorough feature planning document. Rounds can span multiple sessions — the GitHub issue is updated after each exchange. Run `/feature-plan {number}` when the document is ready to generate phase specs.

---

## Steps

### 1. Open or continue

**If an argument was passed:**

If the argument is numeric, treat it as a feature issue number. Invoke the `issue-loader` agent passing the number and `{owner}/{repo}`. Confirm the returned labels include `feature`. Use the returned body as the current document and say:
```
Continuing feature #{number} — {title}.
Current sections: {list of H2 headings}.

What would you like to add or refine?
```

If the argument is a name or slug, search for a matching open issue:
```bash
gh issue list --repo {owner}/{repo} --label "feature" --state open \
  --json number,title --jq '.[] | select(.title | ascii_downcase | contains("{slug}"))'
```
If found, load it as above. If not found, check for a local working draft at `.orc/features/{slug}/{Name}.md`. If found, continue from the local file. If neither exists, start fresh with that name.

**If no argument was passed:**

Ask: `What feature do you want to plan? (Or give me the number of an existing feature issue to continue.)`

---

### 2. Discuss

Ask the user to describe what they want to build. After their initial response, invoke the `spec-researcher` agent — pass the feature name as the title and the user's description as the body.

Surface the key findings before asking follow-up questions:

```
Found in codebase:
- {relevant existing models, routes, components, or patterns}
- {constraints or integration points the feature must work within}
- {anything already built that this feature touches or reuses}
```

Use these findings to ground all follow-up questions. Reference specific files and existing patterns when asking about edge cases, constraints, or phase ordering.

Use targeted follow-up questions to pull out what is still unclear:

- What is the goal? What problem does this solve?
- Who uses this and how do they interact with it?
- What are the key concepts, states, or entities involved? (anchor to discovered models/tables)
- What are the rules, constraints, or edge cases that matter?
- Any third-party services or internal systems it integrates with? (anchor to discovered integrations)
- Known non-goals or things explicitly deferred?
- How does the work break down into ordered phases? (informed by what already exists vs what must be built)

Do not ask all questions at once. Ask the most important follow-up given what the codebase revealed. Keep going until you have enough to write something meaningful.

When you understand the scope well enough, say so and move to step 3.

---

### 3. Write or update the feature document

**Working with a local draft (new feature not yet posted to GitHub):**

Derive names:
- `{Name}` — the feature's proper title, title-cased (e.g. `Storefront`, `Wholesale`, `Analytics`)
- `{slug}` — `{Name}` lowercase, spaces → `-` (e.g. `storefront`, `wholesale`, `analytics`)

```bash
mkdir -p .orc/features/{slug}
```

Write or update `.orc/features/{slug}/{Name}.md`.

**Updating an existing feature issue:**

Build the updated document in memory. Do not write a local file — the issue is the source of truth. Update the issue body directly (step 5).

---

### 4. Document structure

The feature document is a rich narrative. Include only sections that have been discussed — do not add placeholder sections for topics not yet covered. Common sections to draw from (use judgment, not a checklist):

- Opening paragraph — what this feature is and why it exists
- `## What It Is` — concept, scope, and the core mental model
- `## [Key Domain Concepts]` — named for the feature's main entities and rules (e.g. `## States`, `## Payments`, `## Shipping`, `## Discounts`)
- `## Platform Pages` — if there are management pages in the platform
- `## [External Service Name]` — one section per significant third-party integration
- `## Emails` or `## Notifications` — if transactional communications are involved
- `## What's Deferred` — explicitly out of scope for v1 but worth capturing
- `## Implementation Phases` — ordered phase breakdown; add once the user has talked through sequencing. Each phase: `### Phase {n} — {Name}` followed by a short description of what it covers.

---

### 5. Report and invite more

**If updating an existing issue:**
```bash
gh issue edit {number} --repo {owner}/{repo} --body "{updated-body}"
```

Report:
```
Updated: #{number} — {title}
Sections: {comma-separated list of current H2 headings}
```

**If working from a local draft:**

Report:
```
Updated: .orc/features/{slug}/{Name}.md
Sections: {comma-separated list of current H2 headings}
```

Then ask the most useful follow-up question based on what's still thin or unexplored. Continue the discussion, refining existing sections or adding new ones. Repeat steps 2–5 as many times as needed.

---

### 6. Done

When the user says they are done (e.g. "that's good", "ship it", "ready for phases", "done"):

**If working from a local draft:** post to GitHub:

```bash
gh issue create --repo {owner}/{repo} \
  --title "{Name}" \
  --label "feature,status:draft" \
  --body "$(cat .orc/features/{slug}/{Name}.md)"
```

Note the issue number. Delete the local file and directory:
```bash
rm -rf .orc/features/{slug}
```

**If updating an existing issue:** already saved in step 5 — nothing more to do.

**Queue placement** (new features only — skip when updating an existing issue):

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
- [ ] #{number} — {Name}
```

Invoke the `queue-sync` agent in the background. Pass `{owner}/{repo}`. Do not wait for it to complete.

Report:
```
Feature #{number} — {Name}
{issue-url}

Run /feature-plan {number} to generate phase specs and create the feature branch.
```
