<!--
Posted as a PR comment via `gh pr comment` — never folded into the PR
description. The marker line must be the literal first line, with the full
commit SHA review ran against (after any auto-fixes are committed) and the
overall verdict: PASS if every section below is PASS, BLOCK if any section
is BLOCK, otherwise WARNING. `resume` reads this marker to decide whether a
review already on the PR is still fresh (SHA matches current HEAD) or stale
(HEAD has moved — something changed since, so re-review) — do not omit it or
reorder it after the fact.
-->
<!-- orc:ai-review sha:{full-commit-sha} verdict:{PASS|WARNING|BLOCK} -->
## AI Review

_Parallel agents reviewed correctness, security, quality, impact, and deploy risk against the spec and diff._
_Severity: 🚫 BLOCKER — ⚠️ WARNING — 📝 NOTE_

---

### Correctness
**Status: {PASS | WARNING | BLOCK}**

{findings — or "✓ All acceptance criteria satisfied. No scope drift detected."}

---

### Security
**Status: {PASS | WARNING | BLOCK}**

{findings — or "✓ No security concerns found."}

---

### Code Quality
**Status: {PASS | WARNING | BLOCK}**

{findings — or "✓ No quality concerns found."}

---

### Impact
**Status: {PASS | WARNING | BLOCK}**

{findings — or "✓ No breaking changes or unexpected side effects detected."}

---

### Deploy Risk
**Risk level: {none | low | HIGH}**

{findings — or "✓ No deployment coordination risk detected."}
