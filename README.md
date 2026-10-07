# BriskMail

> AI-powered email analysis directly inside Gmail — summary, category, priority, and reply suggestions in one click.

[![CI](https://github.com/Brunotlps/email-classifier/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Brunotlps/email-classifier/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Backend](https://img.shields.io/badge/Backend-Fly.io-blueviolet?style=flat)](https://email-classifier-api.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Try it live

**Web app:** [email-classifier-ruddy.vercel.app](https://email-classifier-ruddy.vercel.app/)

**Chrome Extension:** submitted to the Chrome Web Store — link coming soon after review. Meanwhile, you can [load it unpacked](#chrome-extension-local-install).

**Privacy policy:** [email-classifier-ruddy.vercel.app/privacy.html](https://email-classifier-ruddy.vercel.app/privacy.html)

---

## About

BriskMail is an AI-powered email analysis tool that integrates directly into Gmail via a Chrome extension. Open any email, click **Analyze Email**, and get:

- **Summary** — what the email is about and what is expected from you, in 1–2 sentences
- **Category** — one of 10 fixed categories: Business Proposal, Meeting / Schedule, Technical Support, Billing / Payment, Newsletter / Marketing, Feedback, Personal, Alert / Notification, Application / HR, or Other
- **Priority** — High, Normal, or Low, based on deadlines, financial impact, and urgency signals
- **Action required** — whether the email needs a response
- **Reply suggestions** — 2–3 ready-to-send drafts when a reply is needed, each with a different approach (e.g. accept / decline / ask for details) and tone (formal, cordial, casual, or technical), referencing the specifics of the email

Supports **Portuguese and English** — switch languages anytime from the extension popup. The web app also accepts `.txt`, `.eml`, and `.pdf` uploads (up to 5 MB).

---

## Architecture

```
Gmail (Chrome Extension)                      Web app (Vercel)
  content_script.js reads the email body        text → POST /api/v1/analyze
  background.js → POST /api/v1/analyze          file → POST /api/v1/classify-file
                 ↘                              ↙
               FastAPI backend (Fly.io)
                 routes.py      → input validation, HTTP error mapping
                 FileParser     → .txt / .eml / .pdf extraction (≤ 5 MB)
                 EmailAnalyzer
                   1. language-aware TTL cache (100 entries, 1 h)
                   2. AI call with the shared JSON schema
                      (transport retry: 3 attempts, exponential backoff)
                   3. strict JSON parse + validation
                   4. up to 2 repair calls with safe structural feedback
                 ↓
               OpenAI Structured Outputs (production) / Ollama `format` (local dev)
```

### Project structure

```
email-classifier/
├── app/
│   ├── api/routes.py              # REST endpoints and HTTP error mapping
│   ├── models/schemas.py          # Pydantic models + shared analysis JSON schema
│   ├── services/
│   │   └── analyzer.py            # EmailAnalyzer: cache → AI call → bounded repair → validation
│   ├── utils/
│   │   ├── ai_client.py           # AIClient ABC + OllamaClient + OpenAIClient + factory
│   │   ├── ai_response.py         # Sanitized diagnostics and repair feedback for invalid AI responses
│   │   └── file_parser.py         # .txt / .eml / .pdf extraction (pypdf)
│   ├── config.py                  # Pydantic Settings (env-based, Docker-aware)
│   ├── exceptions.py              # Domain exceptions for upstream AI failures
│   └── main.py                    # FastAPI app, CORS, request logging middleware
├── extension/                     # Chrome Extension (Manifest V3)
│   ├── manifest.json              # Permissions, host_permissions, web_accessible_resources
│   ├── content_script.js          # Gmail DOM injection, MutationObserver, PT/EN UI
│   ├── background.js              # Service worker — intermediates API calls
│   ├── popup/                     # Extension popup (status, PT/EN toggle, how-to)
│   ├── panel/                     # Styles for the result panel injected inside Gmail
│   └── assets/                    # Icons 16/48/128px, promo tile
├── frontend/                      # Web SPA (Vercel)
│   ├── index.html
│   ├── js/app.js
│   ├── css/style.css
│   ├── privacy.html               # Privacy policy (required for Chrome Web Store)
│   ├── vercel.json                # Vercel deploy config
│   └── assets/icon.png            # Brand icon
├── tests/
│   ├── conftest.py                # Fixtures + offline network guard
│   ├── test_analyzer.py
│   ├── test_ai_client.py
│   ├── test_ai_response.py
│   ├── test_api_routes.py
│   ├── test_file_parser.py
│   ├── test_deploy_health.py      # Public health smoke script
│   ├── test_deploy_workflow.py    # CI/CD and rollback policy checks
│   ├── test_security_workflows.py # Dependabot / CodeQL / dependency review checks
│   └── extension_background.test.js  # Node test for the extension service worker
├── scripts/ci/                    # Container smoke, public health probe, rollback image validator
├── docs/                          # Decisions log, CI/CD, deploy/rollback and security runbooks
├── .github/workflows/             # ci.yml (quality gates + deploy), fly-rollback.yml, codeql.yml, dependency-review.yml
├── docker-compose.yml
├── Dockerfile                     # Multi-stage build, non-root runtime user
├── fly.toml                       # Fly.io app config + /health service check
└── requirements.txt
```

---

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Analyzes raw email text. Used by the Chrome extension and the web app |
| `POST` | `/api/v1/classify-file` | Analyzes an uploaded `.txt`, `.eml`, or `.pdf` file (multipart, field `file`, ≤ 5 MB) |
| `GET` | `/health` | Liveness check (`{"status":"healthy"}`) — used by Fly service checks and CI smoke tests |
| `GET` | `/api/v1/health` | Analysis service health |
| `GET` | `/test-ai` | Manual connectivity check against the configured AI provider (not a health check) |

**Request**

```json
POST /api/v1/analyze
{
  "email_content": "Oi João, a reunião do projeto Alpha foi movida para sexta às 14h. Confirme sua presença. Abs, Maria.",
  "language": "pt"
}
```

`email_content` requires at least 10 characters; `language` is `"pt"` (default) or `"en"`.

**Response**

```json
{
  "summary": "Maria informa que a reunião do projeto Alpha foi reagendada para sexta às 14h e pede confirmação.",
  "category": "Reunião / Agenda",
  "priority": "normal",
  "action_required": true,
  "suggestions": [
    {
      "title": "Confirmar presença",
      "content": "Oi Maria, confirmado! Estarei presente na sexta às 14h. Abs, João.",
      "tone": "cordial"
    }
  ]
}
```

`category`, `priority` (`alta` / `normal` / `baixa`), and `tone` (`formal` / `cordial` / `casual` / `técnico`) are fixed enums. `suggestions` is empty when no reply is needed.

**Errors**

| Status | When |
|---|---|
| `400` | Invalid upload (empty, over 5 MB, unsupported extension, malformed multipart), or the AI provider rejected the call (e.g. OpenAI authentication or rate limit) |
| `422` | Request body fails schema validation (e.g. `email_content` too short, unknown `language`) |
| `502` | The AI provider returned a response that could not be validated, even after repair attempts. The detail is sanitized — raw model output is never exposed |
| `500` | Unexpected server error |

Interactive docs: Swagger UI at `/docs`, ReDoc at `/redoc`.

---

## Key technical decisions

The full, append-only log lives in [`docs/DECISIONS.md`](docs/DECISIONS.md).

**Provider-agnostic AI layer** — `AIClient` ABC with `OllamaClient` (local, free) and `OpenAIClient` (production). Switch via the `AI_PROVIDER` env var — no code changes.

**Provider-native structured output** — the same canonical JSON schema is sent to both providers: Ollama receives it through `format`, OpenAI through strict `response_format.json_schema`. The analyzer accepts only a complete JSON object; text wrappers are rejected instead of being extracted with a regular expression.

**Bounded repair loop** — if parsing or validation fails, `EmailAnalyzer` makes at most 2 additional calls, repeating the original request plus a safe structural diagnostic (e.g. a missing field). Raw model output is never fed back, logged in production, or returned to clients. This logical repair is separate from the transport retry handled by tenacity, and only validated results are cached.

**Language-aware cache** — cache key is `SHA-256(language + email_content)`, so PT and EN analyses for the same email are cached independently.

**DOM-based Gmail integration** — the extension reads email content via `div.a3s.innerText` and uses `MutationObserver` to detect newly opened emails. No OAuth required for the MVP.

**Focused API surface** — text analysis uses `POST /api/v1/analyze`; file uploads use `POST /api/v1/classify-file` with the same `EmailAnalyzer` response contract. The legacy binary `/api/v1/classify` flow was removed and now returns 404.

---

## Getting started (local dev)

Local development uses **Ollama**; OpenAI is only used in production.

### Prerequisites

- Docker and Docker Compose
- [Ollama](https://ollama.com/) installed on the host with `qwen2.5:3b` pulled
- Python 3.11 and Node 24 (only needed to run the test suite outside Docker)

### 1. Prepare Ollama

```bash
ollama pull qwen2.5:3b
```

The API container reaches Ollama on the host through the Docker bridge, so Ollama must listen on all interfaces:

```bash
sudo systemctl edit ollama
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

`docker-compose.yml` sets `OLLAMA_BASE_URL=http://172.21.0.1:11434` (the bridge gateway on the original dev machine). If your gateway differs, check it after the first `docker compose up` and update the compose file:

```bash
docker network inspect email-classifier_default --format '{{(index .IPAM.Config 0).Gateway}}'
```

### 2. Run the API

```bash
git clone https://github.com/Brunotlps/email-classifier.git
cd email-classifier

docker compose up -d --build
curl http://localhost:8001/health
curl http://localhost:8001/test-ai
```

Compose already sets `AI_PROVIDER=ollama` and the model. The source is baked into the image (no volumes), so rebuild with `docker compose up -d --build` after code changes.

### 3. Smoke test

```bash
curl -X POST http://localhost:8001/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"email_content": "Prezado, gostaria de agendar uma reunião para discutir o projeto.", "language": "pt"}'
```

API docs: **Swagger UI** at `http://localhost:8001/docs` · **ReDoc** at `http://localhost:8001/redoc`

### Configuration

To run outside Docker, copy `.env.example` to `.env`; the settings are read by `app/config.py`.

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` disables response previews in invalid-AI-response logs |
| `AI_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | `localhost` ↔ `host.docker.internal` is auto-adjusted; overridden by `docker-compose.yml` |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Ollama model name |
| `OPENAI_API_KEY` | — | Required only when `AI_PROVIDER=openai`; must start with `sk-` |
| `OPENAI_MODEL` | `gpt-4o-mini` (in `.env.example`) | Must support Structured Outputs (`response_format: json_schema`) — set it explicitly, the code fallback `gpt-3.5-turbo` does not |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated CORS origins |
| `MAX_TOKENS` | `500` | Max tokens per AI response |
| `TEMPERATURE` | `0.7` | AI generation temperature |

---

## Testing

The test suite is fully offline: `tests/conftest.py` selects an unreachable Ollama URL, clears the OpenAI key, and blocks IP connections and DNS resolution, so every AI call must be mocked. The Docker image contains only `app/`, so run the tests from a local environment — the same commands CI uses:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python -m pytest                                     # full Python suite
python -m pytest --cov=app --cov-report=term         # with coverage
python -m pytest tests/test_analyzer.py -v           # single file

node --test tests/extension_background.test.js       # extension service worker
```

Container smoke test (offline, `--network none`):

```bash
docker build --tag briskmail-ci:local .
bash scripts/ci/container-smoke.sh briskmail-ci:local
```

See [CI quality gates](docs/ci-quality-gates.md) for the full set of local checks, including `actionlint`.

---

## CI/CD and security

- **Quality gates** — [`ci.yml`](.github/workflows/ci.yml) runs on every PR to `main` and every push to `main`, with no path filters: Python tests (3.11), extension checks (Node 24 tests, JS syntax, manifest parsing), and a Docker build + offline `/health` smoke. A `ci-gate` job passes only when all three succeed and is the required check on `main`.
- **Gated production deploy** — on pushes to `main`, the deploy job runs only after `ci-gate` passes, for the same commit SHA, and waits for manual approval of the `Production` environment. Images are tagged with the commit SHA and verified with a public `/health` smoke after release. See [Fly production delivery](docs/fly-production-deploy.md).
- **Rollback** — the manual **Fly Rollback** workflow redeploys a previously successful SHA-tagged image without rebuilding, behind an explicit confirmation and the same `Production` approval. The runbook is in [Fly production delivery](docs/fly-production-deploy.md#rollback-runbook-28).
- **Supply chain** — Dependabot (weekly, `pip` and `github-actions`), dependency review on PRs (fails on high/critical vulnerabilities), and CodeQL for Python and JavaScript. All actions are pinned to full commit SHAs. See [supply chain security](docs/security-supply-chain.md) and the [multipart upload fix](docs/multipart-security-fix.md).

---

## Chrome Extension (local install)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. Open Gmail, open any email, and click **Analyze Email**

The unpacked extension calls the production API (`https://email-classifier-api.fly.dev`).

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decisions log (ADR-lite, append-only) |
| [`docs/ci-quality-gates.md`](docs/ci-quality-gates.md) | CI jobs, local equivalents, offline test boundary |
| [`docs/fly-production-deploy.md`](docs/fly-production-deploy.md) | Gated deploy, rollback runbook, health checks, token rotation |
| [`docs/security-supply-chain.md`](docs/security-supply-chain.md) | Dependabot, dependency review, CodeQL, alert triage (PT-BR) |
| [`docs/multipart-security-fix.md`](docs/multipart-security-fix.md) | `python-multipart` upgrade and upload hardening |

---

## Project status

| Component | Status |
|---|---|
| FastAPI backend | Live on Fly.io |
| Web frontend | Live on Vercel |
| Chrome Extension | v1.2.1 — submitted to the Chrome Web Store, publication pending |
| PT/EN support | Complete |
| CI/CD | Required `ci-gate`, approval-gated Fly deploy, manual rollback |
| Supply chain security | Dependabot, dependency review, and CodeQL active |

---

## Roadmap

**Next**
- Add the Chrome Web Store link to this README after approval
- Collect real user feedback
- Split runtime and development dependencies and pin them with a lockfile

**Medium term**
- Gmail API + OAuth (replace DOM scraping for robustness)
- Per-user rate limiting
- Batch classification (requires the Gmail API)
- User-defined categories and thresholds
- API key authentication for external usage

**Long term**
- Support for additional email clients
- Cloud history across devices
- Staging environment for pre-production validation

---

## About

Built and maintained by **Bruno Teixeira Lopes** — a backend developer from Brazil.

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/Brunotlps)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/brunotlps)
[![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white)](mailto:contatobriskmail@gmail.com)

---

## License

[MIT License](LICENSE)
