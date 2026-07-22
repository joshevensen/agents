## Spec

<!--
The canonical spec for all buildable work. Written onto an issue by /orc:plan
as a comment; consumed by /orc:build.

For the issue to reach status:ready, two things must hold:
  1. Every Acceptance Criterion is machine-verifiable (a test, command, or
     observable outcome proves it).
  2. Open Questions reads "None." — every ambiguity resolved and folded in.
/orc:plan holds the spec to both before setting status:ready, and /orc:build
re-checks both. Do not weaken either to get a spec out the door.
-->

### Problem Statement
{one paragraph: what needs to be built and why, distilled from the issue}

### Reproduction
<!-- Bugs only. Tasks: "N/A". -->
{exact steps to reproduce, observed vs. expected behavior, and where it surfaces}

### Codebase Touchpoints
{existing files the implementer must read first — `path` — one-line note on relevance. Every path here must actually exist.}

### Files to Create
{for each new file: path, purpose, and enough detail to know exactly what goes in it — or "None."}

### Files to Modify
{for each existing file: path, what changes, and why — or "None."}

### Data Models / Migrations
{new tables, columns, indexes, or schema changes with names, types, constraints — or "None."}

### Key Logic
{non-obvious details: edge cases, business rules, integration specifics, sequencing. Do not restate what the file list already makes clear.}

### In Scope
- {item}

### Out of Scope
- {item}

### Acceptance Criteria
<!-- Each must be independently, machine-verifiable. No confidence tiers.
     Bugs MUST include a regression test that fails before the fix, passes after. -->
- [ ] {condition} — verified by: {test / command / observable outcome}

### Open Questions
<!-- MUST read "None." before the issue moves to status:ready. Anything
     unresolved keeps the issue at status:draft. -->
None.

### Notes / Constraints
{technical constraints, dependencies, risks — or "None."}

### Design Rationale
{why this approach over alternatives; rejected alternatives and why — or "N/A"}
