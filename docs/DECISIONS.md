# Architecture Decisions

Append-only log of durable architectural decisions for BriskMail. Each entry explains a "why" that isn't obvious from the code alone. Add new entries at the bottom; do not rewrite or remove past entries — if a decision is later reversed, add a new entry that supersedes it and link back.

---

## 1. Backend deploys to Fly.io, frontend to Vercel

The backend (FastAPI) is deployed to **Fly.io** (`fly.toml`, `.github/workflows/fly-deploy.yml`), and the web frontend SPA to **Vercel** (`frontend/vercel.json`, auto-deploy on push). An earlier deployment target (Railway) was migrated away from during Fase 1.

`fly-deploy.yml` runs `flyctl deploy --remote-only --depot=false`. The `--depot=false` flag is required because Fly's Depot build network had intermittent connectivity failures reaching PyPI — without it, deploys fail with `ConnectionResetError`.

## 2. Chrome Extension MVP uses Gmail DOM scraping, not the Gmail API/OAuth

The extension reads email content via `div.a3s.innerText` and detects new emails with a `MutationObserver` (`extension/content_script.js`), rather than using the official Gmail API with OAuth.

**Why**: avoids Google's OAuth verification process for sensitive scopes, which would significantly slow down shipping the MVP. No user authentication is required.

**When to revisit**: if a Gmail UI update breaks the DOM selectors, or if v2 features that require OAuth (see entry 3) become a priority.

## 3. Features deliberately deferred to v2

The following were considered for the MVP and explicitly deferred:

| Feature | Reason deferred | Revisit when |
|---|---|---|
| Gmail API + OAuth | Auth complexity, Google review for sensitive scopes | DOM scraping breaks with a Gmail update, or v2 features below are prioritized |
| Cloud history across devices | Requires a database + user authentication | There's an active user base requesting it |
| Batch classification | Requires Gmail API with OAuth | After OAuth migration |
| Per-user rate limiting | Premature — no user base yet | Before scaling beyond the current IP-based rate limits |

## 4. `/api/v1/classify` and its services are unused by current clients

`POST /api/v1/classify` (`app/services/classifier.py` + `app/services/response_generator.py`, binary `produtivo`/`improdutivo` classification) is **not called by the Chrome extension or the web frontend**. Both clients use `/api/v1/analyze` (primary) or `/api/v1/classify-file` (file upload — also backed by `EmailAnalyzer`, unrelated to `EmailClassifier`).

`/api/v1/classify` is kept alive only by `tests/test_api_routes.py::TestClassifyEndpoint`, `tests/test_classifier.py`, and `tests/test_response_generator.py`.

**Implication**: this endpoint and its two services are candidates for removal, but removing them is a deliberate product decision (drop the test suites, update coverage figures, confirm no external consumer depends on `/classify`) — not something to bundle into an unrelated change. See `CLAUDE.md`'s Endpoint Status table.

## 5. Manifest V3 implementation constraints (Chrome Extension)

A few non-obvious constraints shape `extension/` code:

- **`web_accessible_resources`**: any asset accessed via `chrome.runtime.getURL()` from a content script (e.g., the brand icon in the result panel) must be explicitly declared in `manifest.json`'s `web_accessible_resources`, or Chrome blocks the load.
- **Toolbar injection**: the "Analisar Email" button is inserted via `insertBefore(toolbar, div.a3s)` on the email body's parent — using `container.prepend()` instead conflicts with Gmail's flexbox layout and misplaces the button.
- **Language propagation**: the PT/EN preference flows `popup.js` → `chrome.storage.sync` (`briskmail_language`) → `content_script.js` → `background.js` → API request body's `language` field. All five links must stay in sync when adding new translatable strings.

## 6. Cache key includes language

`EmailAnalyzer`'s cache key is `sha256(f"{language}:{email_content}")` (`app/services/analyzer.py`), so PT and EN analyses of the same email content are cached independently and don't collide. This differs from the legacy `EmailClassifier`, whose cache key is `sha256(email_content)` only (no language dimension — it predates PT/EN support).
