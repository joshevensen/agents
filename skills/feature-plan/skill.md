---
name: feature-plan
description: Generate detailed phase spec docs from a feature issue. Creates the feature branch, writes phase specs locally, and adds a phase tracker to the issue. Pass a phase number to generate one spec; omit to generate all in parallel.
model: sonnet
---

## Arguments

- `{number}` — the feature issue number (e.g. `42`)
- `[phase-number]` — optional; generate a single phase spec instead of all

---

## Steps

### 1. Load the feature issue

Invoke the `issue-loader` agent. Pass the issue number and `{owner}/{repo}`.

Confirm the returned labels include `feature`. If not, stop:
```
Issue #{number} does not have the `feature` label. Use /feature-create to plan a feature.
```

Derive from the returned metadata:
- `{Name}` — the returned title as-is (e.g. `Storefront`)
- `{slug}` — the returned `slug` field (e.g. `storefront`)

---

### 2. Parse phases

Find the `## Implementation Phases` section in the issue body. Extract each phase:
- Number — from `### Phase {n} — {name}`
- Name
- Description — all body text under that heading until the next `###`

If no `## Implementation Phases` section exists, stop:
```
No "Implementation Phases" section found in issue #{number}.
Add phases to the feature document first with /feature-create {number}.
```

If `{phase-number}` was provided and does not exist in the list, stop:
```
Phase {phase-number} not found in issue #{number}.
Available phases: {comma-separated list of phase numbers}
```

---

### 3. Prepare output directory

```bash
mkdir -p .orc/features/{slug}
```

Write a small config file for downstream skills to reference:
```bash
cat > .orc/features/{slug}/feature.json <<EOF
{
  "issue": {number},
  "name": "{Name}",
  "slug": "{slug}"
}
EOF
```

---

### 4. Create feature branch

Check if `feature/{slug}` already exists:
```bash
git branch -r | grep "origin/feature/{slug}"
```

If it does not exist:
```bash
git branch feature/{slug} origin/main
git push -u origin feature/{slug}
```

If it already exists, skip silently.

---

### 5. Report scope

```
Generating phase spec(s) for #{number} — {Name} → .orc/features/{slug}/
Feature branch: feature/{slug}
```

List each phase that will be generated with its name.

---

### 6. Spawn sub-agent(s)

Spawn one `spec-writer` agent per phase in scope. In all-phases mode, spawn all simultaneously.

Pass each agent a prompt in this structure:

```
## Mode
phase

## Feature document

{full issue body}

## Phase to spec

Phase {n} — {name}

Scope:
{phase description}

## Output path

.orc/features/{slug}/phase-{n}.md
```

---

### 7. Add phase tracker to issue

Build the `## Phases` section from the full phase list (all phases, not just those generated in this run):

```markdown
## Phases

- [ ] Phase 0 — {name}
- [ ] Phase 1 — {name}
- [ ] Phase 2 — {name}
...
```

If the issue body already contains a `## Phases` section, replace it. Otherwise append it to the end of the body.

```bash
gh issue edit {number} --repo {owner}/{repo} --body "{updated-body}"
```

Update status:
```bash
gh issue edit {number} --repo {owner}/{repo} \
  --remove-label "status:draft" \
  --add-label "status:ready"
```

---

### 8. Report

```
Done. {n} phase spec(s) written to .orc/features/{slug}/

  phase-{n}.md — {name}
  ...

Feature branch: feature/{slug}
Phase tracker added to #{number}.

To regenerate a single spec:
  /feature-plan {number} {n}

Run /feature-build .orc/features/{slug}/phase-0.md to start building.
```
