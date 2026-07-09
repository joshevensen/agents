---
name: discuss
description: Enter discussion mode: explore a topic freely using read-only tools, but make no code or file changes until the user explicitly says they are ready.
model: sonnet
---

## Behavior for the rest of this conversation

**Allowed:**
- Reading files
- Running read-only shell commands (`ls`, `cat`, `grep`, `git log`, `git diff`, `find`, etc.)
- Asking clarifying questions
- Sharing opinions, tradeoffs, and recommendations

**Not allowed until the user says they are ready:**
- Editing or writing files
- Running commands that create, delete, or modify anything
- Installing packages or changing configuration

When the user says **"green light"**, exit discussion mode and act normally.

---

## Steps

1. If a topic was provided, acknowledge it, mention that saying **"green light"** will exit discussion mode, and start the discussion.
2. If no topic was provided, ask what the user wants to explore, and mention that saying **"green light"** will exit discussion mode when ready.
