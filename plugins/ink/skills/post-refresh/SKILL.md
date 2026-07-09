---
name: post-refresh
description: Audit published posts for staleness using publication age and REFRESH-CHECK claims, verify flagged claims with current web research, and rank posts needing attention. Use when planning content refresh work.
model: sonnet
---

## Steps

### 1. Load configuration

Run from the repository root. Require `.orc/config/posts.config.json`; otherwise stop with:

```text
Post infrastructure is not configured. Run /setup posts first.
```

Parse the file with a JSON parser and require a non-empty string `posts_dir`. Resolve it relative to the repository root. Reject an absolute path or a path that escapes the repository. If the configured directory does not exist, stop and report its resolved path.

### 2. Load published posts

Scan only paths matching `{posts_dir}/[0-9][0-9][0-9]/*/meta.yaml`, where the number directory contains exactly three digits and the metadata is exactly one slug level beneath it. Sort by post number.

Parse each file with a YAML parser and retain only `status: published`. For each retained post, capture its zero-padded number, title, slug, metadata path, publication date, and adjacent `post.md` path.

Require `published_at` to be a valid `YYYY-MM-DD` calendar date and `post.md` to exist and be readable. Record malformed published entries separately rather than silently skipping or treating them as current. If there are no published posts, report `No published posts found.` and stop.

### 3. Run both detection modes

Run the age-based and content-based checks for every valid published post. Do not skip marker checks for newer posts or age checks for posts without markers.

#### 3a. Age-based check

Use today's local calendar date. Subtract six calendar months to create the cutoff date, clamping to the last valid day when necessary. Flag a post only when `published_at` is earlier than that cutoff; a post published exactly six months ago is not older than six months.

Record the publication date, cutoff date, and age in whole months. Age is a maintenance signal, not proof that content is wrong.

#### 3b. Content-based check

Scan every `post.md` for the exact marker `<!-- REFRESH-CHECK -->`. For each marker, capture the complete sentence or table row immediately associated with it plus the nearest preceding Markdown heading. If the marker cannot be associated with a clear claim, classify it as `uncertain` and report the location.

Perform a focused web search for every marked claim. Search for the named entity and the specific changing fact rather than the whole sentence. Use current sources and compare source publication or update dates where available.

Prefer primary and authoritative sources such as provider pages, standards bodies, regulators, official datasets, and product documentation. Record source URLs and access dates. Classify each marker:

- `current`: evidence supports the claim
- `stale`: evidence contradicts or materially changes it
- `uncertain`: reliable current evidence is insufficient

Use `stale` only when current evidence materially contradicts the post. Use `uncertain` when sources conflict, the claim is too vague, or authoritative evidence is unavailable. Clearly label inferences. Do not rewrite posts during this skill.

### 4. Rank results

Include a post in the attention list when it has an age flag, a stale claim, or an uncertain claim. Rank posts in this order:

1. stale claims with material reader impact
2. multiple stale or uncertain claims
3. age over six months plus marked claims
4. age alone

Break ties by number of stale claims, then oldest publication date, then post number.

Display:

```text
POSTS NEEDING ATTENTION

1. 003  What Is Fiber Internet?
   Published: 2025-01-10
   Reasons: age, stale claim
   - "{claim summary}" — stale
     Evidence: {source URL} (checked YYYY-MM-DD)
```

Use only these reason labels: `age`, `stale claim`, and `uncertain claim`. Include concise affected-claim summaries and source links. Do not list `current` claims as reasons, but include aggregate counts in the audit summary.

After the ranked list, show totals for published posts scanned, markers checked, current claims, stale claims, uncertain claims, and age flags. List malformed published entries in a separate `COULD NOT AUDIT` section with exact file paths and errors.

If nothing needs attention, say so explicitly and still report the audit totals and malformed entries.

### 5. Handoff

Ask the user which ranked post to refresh. After they choose, report the exact command for a new session:

```text
/post-develop {number}
```

Explain briefly whether it was selected for age, stale claims, or both. Do not invoke development automatically and do not change status, metadata, the GitHub post-list issue, branches, worktrees, or post files during this audit.
