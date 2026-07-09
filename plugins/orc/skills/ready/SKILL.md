---
name: ready
description: List open issues at status:ready — specced and buildable right now. Use to see what to @claude implement or /orc:build next.
model: haiku
---

## Steps

### 1. Fetch

```bash
gh issue list --state open --label "status:ready" --json number,title,labels,updatedAt --limit 100
```

### 2. Report

```
Ready to build (n)

#{number}  {title}  [{type:task|type:bug}]  updated {relative time}
...

Comment "@claude implement this" on one, or run /orc:build {number}.
```

If empty: `Nothing ready — check /orc:drafts, or /orc:create something new.`
