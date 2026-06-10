---
description: Run the code-reviewer agent over one "layer" (module) of BriskMail — API/Schemas, Services, Utils/AI, Extension, Frontend, or Tests. Use for a layered code-review pass, e.g. "revise a camada Services" or "/review-layer extension". Reports findings only — nothing is created until /triage-findings is run.
argument-hint: [layer]
allowed-tools: Agent, Read
---

# Review Layer

BriskMail's review layers map to its module structure:

| Layer | Paths | Focus |
|---|---|---|
| `api` | `app/api/`, `app/models/` | Input validation, HTTP error mapping, rate limiting |
| `services` | `app/services/` | Prompt engineering, caching, Endpoint Status compliance |
| `utils` | `app/utils/` | AI provider abstraction, file parsing |
| `extension` | `extension/` | Manifest V3, DOM scraping, i18n |
| `frontend` | `frontend/` | SPA, API integration |
| `tests` | `tests/` | Coverage, mock conventions |

## Steps

1. If the user didn't specify a layer, or it doesn't match the table above, ask which one to review (or whether they mean something else entirely).
2. Launch the `code-reviewer` subagent (Agent tool, `subagent_type: code-reviewer`) with a prompt that:
   - Names the layer and its path(s) from the table above, and restricts the review to those paths.
   - Tells it to follow its own checklist (CLAUDE.md, docs/DECISIONS.md) but only report findings within the given scope.
3. Present the returned findings to the user, grouped by severity (blocking / suggestion / nit), with `file:line` citations.
4. Do not create issues or make edits in this skill. If the user wants to track findings, point them to `/triage-findings`.
