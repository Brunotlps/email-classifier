---
description: Turn code-review findings (e.g. from a recent /review-layer run) into a batch of GitHub issue drafts using .github/ISSUE_TEMPLATE/bug_report.md, let the user approve/edit the whole batch, then create the approved ones via gh issue create. Use after a code review when the user wants to track findings as issues.
allowed-tools: Read, Bash
---

# Triage Findings

## Steps

1. Identify the findings to triage from the recent conversation (a `/review-layer` output, or any review/diagnosis just discussed). If it's unclear which findings to use, ask.
2. For each finding the user wants tracked, draft an issue using `.github/ISSUE_TEMPLATE/bug_report.md`'s sections (Summary, Steps to reproduce, Expected/Actual behavior, Affected files `path:line`, Additional context — reference the relevant CLAUDE.md section, e.g. Endpoint Status or Architecture).
   - Title format: `fix(scope): short description` (or `feat(scope):` / `chore(scope):` as appropriate).
   - Skip "nit"-severity findings unless the user explicitly asks to include them.
3. Present the full batch as a numbered list (title + short body summary each) for the user to approve, edit, drop individual items, or reorder. Make no GitHub calls yet.
4. On confirmation, create each approved issue with `gh issue create --title "..." --body "..." --label bug`, in order.
5. Report back the created issue numbers/URLs as a summary list.
