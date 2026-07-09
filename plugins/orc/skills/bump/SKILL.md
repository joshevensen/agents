---
name: bump
description: Review open Dependabot grouped PRs for security and breaking changes, then merge if safe. Run after Dependabot opens its monthly grouped update PR.
model: sonnet
---

## Steps

### 1. Identify the repo

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

Store as `{owner}/{repo}`.

---

### 2. Find Dependabot PRs

```bash
gh pr list --repo {owner}/{repo} --state open --limit 20 \
  --json number,title,author,headRefName,baseRefName
```

Filter to PRs where `author.login` is `app/dependabot`.

If none found:
```
No open Dependabot PRs in {owner}/{repo}.
```
Stop.

List all found PRs (there will typically be one per ecosystem — packages and github-actions). Process each one.

---

### 3. For each PR: security checks

Fetch the PR diff:
```bash
gh pr diff {pr} --repo {owner}/{repo}
```

Parse all changed package entries from the diff — look for version bumps in `package.json`, `composer.json`, `package-lock.json`, `composer.lock`, or equivalent.

For each package, extract `{package}`, `{old_version}`, `{new_version}`, and `{ecosystem}` (npm, packagist, github-actions, etc.).

#### OSV vulnerability check

For each package:
```bash
curl -sf https://api.osv.dev/v1/query \
  -H "Content-Type: application/json" \
  -d '{"package": {"name": "{package}", "ecosystem": "{ecosystem}"}, "version": "{new_version}"}'
```

Flag any package where the response contains `vulns`.

#### Publish recency (npm only)

```bash
curl -sf "https://registry.npmjs.org/{package}/{new_version}" | jq -r '.publish_time // empty'
```

Flag any package published less than 48 hours ago as a suspicious publish.

#### Major version bumps

Flag any package where the major version number increased (e.g. `1.x` → `2.x`) — these are potential breaking changes.

---

### 4. For each PR: parallel AI review

Invoke `review-security` and `review-impact` in parallel. Pass each the full diff and the list of packages with their old/new versions and any flags from step 3.

**`review-security`** — look for: packages with known CVEs, suspicious version patterns, supply chain concerns, dependency confusion risks.

**`review-impact`** — look for: major version bumps with breaking API changes, removed exports or methods, changed behavior that could affect the app at runtime.

---

### 5. Surface findings

If no flags from step 3 and no BLOCKERs or WARNINGs from step 4: proceed directly to step 6.

Otherwise present a summary for each PR:

```
PR #{pr} — {title}

SECURITY FLAGS
- {package} {old} → {new}: {reason}

BLOCKERS
- [Security] {finding}
- [Impact] {finding}

WARNINGS
- [Security] {finding}

(m) merge anyway  (s) skip this PR  (d) defer — leave open
```

`(m)` proceeds to step 6 for this PR. `(s)` skips it entirely. `(d)` leaves the PR open and moves to the next.

---

### 6. CI check and merge

```bash
gh pr checks {pr} --repo {owner}/{repo} --watch --timeout 600
```

If CI passes: merge:
```bash
gh pr merge {pr} --repo {owner}/{repo} --squash --delete-branch
```

If any check fails, enter CI fix mode:

1. Fetch logs for the first failing check:
   ```bash
   gh run view {run-id} --repo {owner}/{repo} --log-failed
   ```
2. Get the diff:
   ```bash
   gh pr diff {pr} --repo {owner}/{repo}
   ```
3. Invoke the `ci-debugger` agent. Pass the failing check name, log output, and diff.
4. Evaluate the proposed fix:
   - **Apply silently** if confidence is high and the fix is clearly safe (missing import, type error, test fixture).
   - **Stop and report** if the fix touches logic beyond a trivial correction. Wait for direction.
5. Apply, commit (`fix: resolve CI failure in dependency bump`), push.
6. Re-watch CI and repeat until all checks pass, then merge.

---

### 7. Report

```
{merged_count} Dependabot PR(s) merged, {skipped_count} skipped, {deferred_count} deferred.
{if skipped or deferred} Skipped/deferred: {list each with reason}
```
