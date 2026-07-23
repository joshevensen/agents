---
name: respond
description: Fetch a PR's unresolved review threads and unanswered comments and work through them one at a time — fix and push, or reply. Manually triggered, never watches or subscribes to a PR. Never merges. Invoke as /orc:respond [pr].
model: sonnet
---

`respond` is the manual counterpart to watching a PR live: nothing subscribes
to webhooks or polls in the background. You run `/orc:respond` when you've
looked at a PR yourself and decided there's feedback worth acting on. It pulls
whatever is currently unresolved, works through it interactively, pushes any
fixes, and stops — no CI check, no mergeability check, no merge. Use `resume`
for CI/mergeability once comments are settled, and merge the PR yourself.

## `--dry-run`

`/orc:respond [pr] --dry-run` runs steps 0-2 exactly as normal (read-only).
In step 3, still show each item and let you choose `(f)`/`(r)`/`(s)`; for
`(f)` show the diff and commit it locally (inspectable with `git log`/`git
diff`) but skip `git push`; for `(r)` print the reply text instead of posting
it and skip the resolve mutation. End with:
```
DRY RUN — {n} item(s) addressed locally, not pushed or posted. Re-run without
--dry-run to push fixes and post replies.
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

### 2. Gather unaddressed feedback

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

Walk the comment list in order. A comment counts as unaddressed only if it
was **not** authored by `{me}` and **no comment authored by `{me}` appears
later in the list** — that later comment is treated as your reply, even if
informal. This is a simple heuristic, not thread-aware; if it misclassifies
something, the reply step still lets you skip it.

If both sources are empty, report `Nothing unresolved on PR #{pr}.` and stop.

### 3. Work through each item

Present every unresolved thread and unanswered comment, numbered, with its
file/line (threads) or author (general comments) and body. For each, in
order:

**`(f)` — Fix:** make the code change, show the diff, confirm, then commit:
```bash
git commit -am "fix: {brief description of the comment}"
```

**`(r)` — Reply:** draft a short reply explaining the decision (why not
fixed, or a clarifying question), confirm the text, then post it:
- General comment: `gh pr comment {pr} --body "{reply}"`
- Review thread: reply in-thread via GraphQL `addPullRequestReviewThreadReply`
  with the thread `id` and `{reply}` body.

**`(s)` — Skip:** leave it exactly as is, no reply, no resolve. Use this for
anything ambiguous enough that you'd rather handle it yourself outside this
skill.

After a fix or a reply to a **review thread**, resolve it:
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
PR #{pr}: {n} fixed and pushed, {m} replied, {k} skipped.
Comments settled. Run /orc:resume {issue-number} for CI/mergeability, or merge yourself when ready.
```
