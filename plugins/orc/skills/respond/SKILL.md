---
name: respond
description: Fetch unresolved comments you left on a PR and implement what they ask for directly — no interactive per-item confirmation. Manually triggered, never watches or subscribes to a PR. Never merges. Invoke as /orc:respond [pr].
model: sonnet
---

`respond` is the manual counterpart to watching a PR live: nothing subscribes
to webhooks or polls in the background. You run `/orc:respond` after leaving
comments on your own PR yourself — each one is treated as an instruction to
carry out, not a suggestion to weigh. It implements every unresolved comment
directly, commits, pushes, and stops — no CI check, no mergeability check, no
merge. Use `resume` for CI/mergeability once the comments are settled, and
merge the PR yourself.

## `--dry-run`

`/orc:respond [pr] --dry-run` runs steps 0-2 exactly as normal (read-only).
Step 3 still implements every item and commits locally (inspectable with
`git log`/`git diff`), but skips `git push`, the reply posts, and the resolve
mutations — print what each reply would have said instead. End with:
```
DRY RUN — {n} item(s) implemented locally, not pushed or posted. Re-run
without --dry-run to push and post replies.
```

## Steps

### 0. Resolve target PR

If `{pr}` is given, use it. Otherwise detect it from the current branch:

```bash
pr=$(gh pr view --json number --jq .number 2>/dev/null)
```

If neither yields a number, stop and ask which PR to respond to.

### 1. Sync

```bash
git fetch origin
gh pr checkout {pr}
git fetch origin main
```

### 2. Gather unresolved comments

**Unresolved review threads** (inline comments left via a "Files changed" review):

```bash
owner=$(gh repo view --json owner --jq .owner.login)
repo=$(gh repo view --json name --jq .name)
gh api graphql -f query='
  query($owner:String!, $repo:String!, $pr:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$pr) {
        reviewThreads(first:100) {
          nodes {
            id
            isResolved
            comments(first:50) {
              nodes { id body path line author { login } }
            }
          }
        }
      }
    }
  }' -f owner={owner} -f repo={repo} -F pr={pr} \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'
```

**Unanswered general PR comments** (top-level conversation, not tied to a review):

```bash
me=$(gh api user --jq .login)
gh pr view {pr} --json comments --jq '.comments'
```

Walk the comment list in order. A comment counts as unanswered only if it was
**not** authored by `{me}` and **no comment authored by `{me}` appears later
in the list** — that later comment is treated as your own past reply, even if
informal.

If both sources are empty, report `Nothing unresolved on PR #{pr}.` and stop.

### 3. Implement every item

Treat each unresolved thread and unanswered comment as a direct instruction —
no per-item confirmation. For each, in order:

- **A request for a code change** ("do X", "this should Y", "fix Z"):
  implement it, then commit:
  ```bash
  git commit -am "address review: {brief description of the comment}"
  ```
- **A genuine question** (nothing to change, an answer is what's being
  asked for): reply directly, no code change:
  - General comment: `gh pr comment {pr} --body "{reply}"`
  - Review thread: reply in-thread via GraphQL
    `addPullRequestReviewThreadReply` with the thread `id` and `{reply}` body.
- **Genuinely ambiguous** (conflicting with another comment, or unclear what
  change is wanted): don't guess — reply asking for clarification the same
  way as a question, and leave the thread unresolved.

After implementing or answering a **review thread**, resolve it (skip this
for a thread left open pending clarification):
```bash
gh api graphql -f query='
  mutation($id:ID!) { resolveReviewThread(input:{threadId:$id}) { thread { id } } }
' -f id={thread-id}
```
General comments have no resolve state — a posted reply is the terminus.

### 4. Push

If any commits were made in step 3:
```bash
git push
```

### 5. Report

```
PR #{pr}: {n} implemented and pushed, {m} answered, {k} left open for clarification.
Run /orc:resume {issue-number} for CI/mergeability, or merge yourself when ready.
```
