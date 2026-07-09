---
name: drafts
description: List open issues at status:draft — created but still missing a build-ready spec. Use to see what needs /orc:create run on it next.
model: haiku
---

## Steps

### 1. Fetch

```bash
gh issue list --state open --label "status:draft" --json number,title,labels,updatedAt --limit 100
```

### 2. Report

```
Drafts — needs a spec (n)

#{number}  {title}  [{type:task|type:bug}]  updated {relative time}
...

Run /orc:create {number} to write the spec.
```

If empty: `No drafts — every open issue has a spec.`
