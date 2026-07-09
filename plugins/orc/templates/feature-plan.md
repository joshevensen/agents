---
id: F000
title: {feature title}
flag: {pennant-flag-key}
status: draft
---
<!--
Feature plan — lives at .orc/features/F###-slug.md. Authored by /orc:create,
fanned out into task issues by /orc:plan, and read by /orc:build (F### picks
the next unbuilt task). Features have no GitHub issue of their own; this doc
is the tracker. status: draft → planned → building → done.
-->

# {feature title}

## Overview
{a few sentences: what the feature is and the value it delivers}

## Goal / Why
{the outcome this feature achieves and who it's for}

## Scope
- {what the feature includes}

## Out of Scope
- {explicitly excluded, to stop drift as tasks are built}

## Feature Flag
`{pennant-flag-key}` — created by task #1 below. Every task merges to `main`
behind this flag; flip it on once all tasks are done.

## Tasks (in order)
<!-- /orc:plan fills in issue numbers. Task 1 is ALWAYS flag setup.
     /orc:build F### builds the first still-open task in this list. -->
1. [ ] #{n} — Set up the `{pennant-flag-key}` feature flag
2. [ ] #{n} — {task title}
3. [ ] #{n} — {task title}

## Open Questions
<!-- Must read "None." before /orc:plan runs autonomously. -->
None.
