---
name: queue-push
description: Push the local .orc/QUEUE.md order to the GitHub Queue issue. Edit the table rows in .orc/QUEUE.md first, then run /queue-push to make it the new canonical order.
model: haiku
---

## Steps

### 1. Read local queue

Read `.orc/QUEUE.md`. If it does not exist:
```
No local queue found. Run /queue-sync to generate one first.
```
Stop.

Parse the table rows to extract an ordered list of issue numbers and titles. Skip the header and separator rows. Strip any whitespace from each cell.

---

### 2. Find the Queue issue

```bash
gh issue list --repo {owner}/{repo} --state open --label "queue" \
  --json number,title,body --jq '.[] | select(.title == "Global Queue")'
```

If not found, stop:
```
Global Queue issue not found. Run /setup to create it.
```

---

### 3. Push to GitHub

Rebuild the `## Queue` section as a padded table (same format as `QUEUE.md`). Compute column widths from the longest value in each column including the header, then pad every cell to that width:

```
## Queue

| #   | Name                            | Status   | Type    |
| --- | ------------------------------- | -------- | ------- |
| 42  | Add user authentication         | ready    | task    |
| 51  | Storefront                      | draft    | feature |
...
```

The Status and Type columns come from the current rows in `.orc/QUEUE.md` — preserve whatever values are already there.

Update the Queue issue:
```bash
gh issue edit {queue-issue-number} --repo {owner}/{repo} --body "{updated-body}"
```

---

### 4. Report

```
Queue updated — {n} items pushed to #{queue-issue-number}.
```
