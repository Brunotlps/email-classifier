---
description: File a GitHub issue for BriskMail (API, extension, or web frontend) using .github/ISSUE_TEMPLATE/bug_report.md as the skeleton. Use when the user wants to report, track, or write up a bug as a GitHub issue.
allowed-tools: Read, Bash
---

# File a Bug Report

## Steps

1. Read `.github/ISSUE_TEMPLATE/bug_report.md` for the required sections: Summary, Steps to reproduce, Expected behavior, Actual behavior, Affected files, Additional context.
2. Fill each section from the conversation/investigation so far. "Affected files" must use `path:line` citations. "Additional context" should reference the relevant `CLAUDE.md` section (Endpoint Status / Architecture) when applicable.
3. Title format matches commit convention: `fix(scope): short description` (or `feat(scope): ...` if it's a missing-feature report).
4. Show the drafted issue (title + body) to the user for confirmation before creating it.
5. On confirmation, create it with `gh issue create --title "..." --body "..." --label bug`.
