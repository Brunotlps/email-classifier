---
description: Append a new architecture decision entry to docs/DECISIONS.md, following BriskMail's append-only ADR-lite format. Use when the user wants to record the "why" behind a non-obvious choice, or asks to document a decision.
allowed-tools: Read, Edit
---

# New Decision

`docs/DECISIONS.md` is an append-only log — past entries are never rewritten or removed. If a decision is later reversed, add a new entry that supersedes it and link back to the old one.

## Steps

1. Read `docs/DECISIONS.md` and find the highest existing entry number (`## N. <title>`).
2. If the user hasn't given enough detail, ask for: the decision itself, alternatives considered (if any), the **why** (the non-obvious reasoning — a constraint, incident, or trade-off), and **when to revisit** (if applicable).
3. Append a new `## <N+1>. <Title>` section at the very bottom of the file, after the last entry. Match the tone and structure of existing entries — short prose paragraphs, with **Why**/**When to revisit** as bold inline labels where the existing entries use them.
4. If the new decision relates to or supersedes an existing entry, add one sentence linking back (e.g. "Supersedes entry 3.") — do not edit the old entry itself beyond that.
5. Show the user the new entry before considering the task done. Do not commit unless asked.
