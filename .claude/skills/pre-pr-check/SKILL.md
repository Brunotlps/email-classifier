---
description: Run BriskMail's pre-PR checklist before opening a pull request into main — tests, diff review, and commit/branch convention checks. Use when the user is about to open a PR or asks whether a branch is ready for a PR.
allowed-tools: Bash, Read
---

# Pre-PR Check

Per `CLAUDE.md`, CI (`fly-deploy.yml`) deploys on push to `main` but does **not** run tests — this checklist is the actual quality gate.

## Steps

1. **Tests** (skip if the branch only touches docs/config and no `app/`/`tests/`/`extension/` files changed):
   ```
   docker exec -it email_classifier_api pytest tests/ -m "not slow and not integration"
   ```
   If the diff touches AI-call paths, note that `test_classify_with_valid_email` / `test_classify_file_with_txt` need Ollama running (the `-m` filter above skips them by default).

2. **Diff review**: `git status --porcelain` and `git diff main...<branch> --stat`. Confirm the file list matches what the task intended — flag anything unexpected (stray `__pycache__`, `.env`, build artifacts, unrelated in-progress changes).

3. **Commit conventions**: `git log main..<branch> --oneline`. Each commit should follow `type(scope): summary` (Conventional Commits). Agent-authored commits should include `Co-Authored-By: Claude <model> <noreply@anthropic.com>`.

4. **Branch naming / direct-to-main**: per `CLAUDE.md`'s Branching section, feature work goes through a PR into `main`. Flag if work happened directly on `main` without an explicit one-off exception the user granted for that change.

5. Report a pass/fail summary with anything that needs the user's attention before opening the PR.
