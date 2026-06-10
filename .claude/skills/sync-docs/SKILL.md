---
description: Audit whether the project structure trees in CLAUDE.md and README.md match the actual repo. Use after adding, removing, or moving files, or before a docs review.
allowed-tools: Bash, Read, Edit
---

# Sync Docs

`CLAUDE.md` and `README.md` each contain a "Project structure" tree (fenced code block). Both should reflect what a fresh `git clone` actually contains — gitignored/local-only files (e.g. `archive/`, `docs/harness-audit/`) should NOT appear in either tree.

## Steps

1. Get the ground truth: `git ls-files | sort` (tracked files only — this is what a fresh clone has).
2. Read the "Project structure" tree in `CLAUDE.md` and in `README.md`.
3. Compare: for each tree, list (a) paths in the tree that no longer exist or aren't tracked, (b) tracked paths/directories missing from the tree, (c) inconsistencies between the two trees (e.g. one shows `extension/_locales/` and the other doesn't).
4. Present the discrepancies to the user before editing. Keep inline `#` annotations consistent in style with neighboring lines.
5. On confirmation, apply the edits to both files, keeping the trees as close to identical as their differing scope allows (`CLAUDE.md` is more complete/agent-facing, `README.md` is a trimmed human-facing version).
