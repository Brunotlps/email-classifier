# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI REST API that classifies emails as **productive** or **unproductive** using LLMs (Ollama in dev, OpenAI in prod), with response suggestion generation and file upload support for `.txt`, `.eml`, and `.pdf`.

**Current roadmap**: See `sprint-fase-1.md` (bug fixes + Fly.io deploy) and `sprint-fase-2.md` (Chrome Extension for Gmail).

---

## Commands

### Running the application
```bash
# Start with Docker Compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after code changes (volumes are commented out in compose)
docker-compose up -d --build

# API available at http://localhost:8001
# Swagger UI at http://localhost:8001/docs
# ReDoc at http://localhost:8001/redoc
```

### Smoke test (run this first to confirm the environment is functional)
```bash
# Verify the container is up and the AI backend is reachable
curl -s http://localhost:8001/health && curl -s http://localhost:8001/test-ai

# Quick classification sanity check
curl -s -X POST http://localhost:8001/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"email_content": "Prezado, gostaria de agendar uma reunião para discutir o projeto."}'
```

### Running tests
```bash
# All tests (inside the container)
docker exec -it email_classifier_api pytest tests/ -v

# With coverage report
docker exec -it email_classifier_api pytest tests/ --cov=app --cov-report=term

# Single test file
docker exec -it email_classifier_api pytest tests/test_classifier.py -v

# Single test function
docker exec -it email_classifier_api pytest tests/test_classifier.py::TestEmailClassifier::test_classify_produtivo_success -v

# Skip slow/integration tests
docker exec -it email_classifier_api pytest tests/ -m "not slow and not integration"
```

### AI provider for local development

**Always use `AI_PROVIDER=ollama` for local development.** Never suggest OpenAI-based code or configurations unless the context is explicitly production or the user asks for it. OpenAI is only used in production (Fly.io).

### Deploy to Fly.io (production backend)
```bash
# Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# Authenticate
fly auth login

# Deploy (fly.toml must exist in project root)
fly deploy

# View live logs
fly logs

# Check machine status
fly status

# Update a secret (env var) without redeploying
fly secrets set KEY=value

# Force redeploy after secrets change
fly deploy
```

### Ollama setup (required for local development)
```bash
# Install and pull the model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b

# Configure Ollama to accept external connections (required for Docker)
sudo systemctl edit ollama
# Add:
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"

sudo systemctl daemon-reload && sudo systemctl restart ollama

# Verify it's listening on all interfaces
sudo systemctl status ollama | grep Listening
# Expected: [::]:11434 or 0.0.0.0:11434
```

### Checking AI connectivity
```bash
# Test AI connection from the running container
curl http://localhost:8001/test-ai

# Check health
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/health
```

---

## Project Structure

```
email-classifier/
├── app/
│   ├── main.py                        # FastAPI app, CORS, rate limiter, request logging middleware
│   ├── config.py                      # Pydantic Settings (reads .env, auto-detects Docker)
│   ├── api/
│   │   └── routes.py                  # REST endpoints with per-route rate limiting
│   ├── models/
│   │   └── schemas.py                 # Pydantic request/response models
│   ├── services/
│   │   ├── classifier.py              # EmailClassifier: cache + retry + prompt engineering
│   │   └── response_generator.py      # ResponseGenerator: suggestion generation + tone normalization
│   └── utils/
│       ├── ai_client.py               # AIClient ABC + OllamaClient + OpenAIClient + factory
│       └── file_parser.py             # FileParser: .txt / .eml / .pdf extraction
├── tests/
│   ├── conftest.py                    # Shared fixtures (sample emails, temp files)
│   ├── test_classifier.py             # Unit tests for EmailClassifier
│   ├── test_response_generator.py     # Unit tests for ResponseGenerator
│   ├── test_file_parser.py            # Unit tests for FileParser
│   └── test_api_routes.py             # Integration tests for HTTP endpoints
├── frontend/
│   ├── index.html                     # SPA with text input and file upload tabs
│   ├── js/app.js                      # API calls + localStorage history
│   └── css/style.css
├── extension/                         # Chrome Extension (Fase 2 — ver sprint-fase-2.md)
│   ├── manifest.json                  # Manifest V3 config
│   ├── content_script.js             # Injetado no Gmail, lê email e injeta UI
│   ├── background.js                 # Service worker — intermedia fetch para a API
│   ├── popup/                        # UI do popup da extensão
│   └── panel/                        # Painel injetado dentro do Gmail
├── docker-compose.yml
├── fly.toml                           # Configuração de deploy no Fly.io
├── Dockerfile                         # Multi-stage build (builder + runtime, non-root user)
├── requirements.txt
├── pytest.ini
├── sprint-fase-1.md                   # Estratégia: bug fixes + deploy Fly.io
├── sprint-fase-2.md                   # Estratégia: Chrome Extension MVP
└── .env.example
```

---

## Architecture

### Layer structure and responsibilities

```
HTTP Request
    ↓
app/api/routes.py          → validates input via Pydantic, calls services, maps exceptions to HTTP codes
    ↓
app/services/classifier.py → SHA-256 cache key → TTLCache lookup → AI call with retry → JSON parse + validate
app/services/response_generator.py → AI call → JSON parse → tone normalization → ResponseSuggestion objects
    ↓
app/utils/ai_client.py     → factory pattern: get_ai_client() returns OllamaClient or OpenAIClient
    ↓
Ollama (dev) / OpenAI (prod)
```

### AI provider switching
`get_ai_client()` in `ai_client.py` returns `OllamaClient` or `OpenAIClient` based on `settings.ai_provider` (`AI_PROVIDER` env var). Both implement the `AIClient` ABC with a single `async generate(prompt, system_prompt) -> str` method. Switching providers requires only an env var change — no code changes.

### Caching and retry
`EmailClassifier` uses `TTLCache(maxsize=100, ttl=3600)` keyed by `SHA-256(email_content)`. Cache hits return immediately without any AI call. The AI call itself is decorated with `@retry(stop_after_attempt(3), wait_exponential(multiplier=1, min=1, max=10))` from tenacity. `ResponseGenerator` has no cache — only `EmailClassifier` caches.

### Suggestion generation is non-blocking
In `routes.py`, if `ResponseGenerator.generate_suggestions()` throws, the exception is caught and `suggestions=[]` is returned. Classification results are never blocked by suggestion failures.

### Prompt engineering pattern
Both `EmailClassifier` and `ResponseGenerator` follow the same pattern:
1. `_build_system_prompt()` — defines role, criteria, and strict JSON-only output format
2. `_build_user_prompt(email_content)` — wraps the email between `---` delimiters
3. `_extract_json(response)` — uses `re.search(r'\{.*\}', text, re.DOTALL)` to strip any non-JSON text the model adds
4. `_parse_response()` / `_parse_suggestions()` — validates required fields and value ranges

### Docker networking for Ollama
The `docker-compose.yml` hardcodes `OLLAMA_BASE_URL=http://172.21.0.1:11434` (the Docker bridge gateway IP) because `localhost` inside the container refers to the container itself, not the host. `config.py` has `_adjust_ollama_url()` that auto-swaps `localhost` ↔ `host.docker.internal`, but this is overridden by the hardcoded IP in compose. **If the Docker bridge gateway IP changes on a new machine, update `OLLAMA_BASE_URL` in `docker-compose.yml`.**

### Pydantic schemas
- `EmailClassifyRequest`: `email_content: str` with `min_length=10` (enforced at the HTTP layer — returns 422 for short emails)
- `ResponseSuggestion`: `tone` is a `Literal["formal", "cordial", "casual", "técnico"]`
- `EmailClassifyResponse`: `suggestions` defaults to `[]` via `default_factory=list`

---

## Code Style

- **Indentation**: 4-space indentation (PEP 8 standard)
- **Class methods**: use `self` for instance methods; `FileParser` uses `@staticmethod` for all methods (no instance state)
- **Async**: all AI calls and HTTP endpoint handlers are `async def`; helper/parsing methods are sync
- **Logging**: use `structlog.get_logger()` — never `print()` in service/util code (some `print()` calls exist in routes as tech debt)
- **Error handling**: services raise `ValueError` for invalid input/response; routes catch `ValueError` → HTTP 400, `Exception` → HTTP 500
- **Comments in Portuguese**: docstrings and inline comments are in Portuguese throughout the codebase

---

## Tests

### Strategy
- **Unit tests** (`test_classifier.py`, `test_response_generator.py`): mock the AI client with `patch.object(instance.ai_client, 'generate', new_callable=AsyncMock)`. Never make real AI calls in unit tests.
- **Integration tests** (`test_api_routes.py`): use `fastapi.testclient.TestClient` with a real app instance. The `test_classify_with_valid_email` and `test_classify_file_with_txt` tests call the real AI (Ollama must be running) — these need `timeout=30.0`.
- **File parser tests** (`test_file_parser.py`): fully synchronous, no mocking needed.

### Fixtures (conftest.py)
| Fixture | Description |
|---|---|
| `sample_produtivo_email` | Business email requesting a meeting |
| `sample_improdutivo_email` | Spam/promotional email |
| `sample_txt_file` | Temp `.txt` file via `tmp_path` |
| `sample_empty_file` | Empty `.txt` for validation tests |
| `sample_large_file` | ~6MB `.txt` to trigger size limit |
| `fixtures_dir` | Path to `tests/fixtures/` directory |

### Coverage by module
| Module | Coverage |
|---|---|
| `schemas.py` | 100% |
| `classifier.py` | 98% |
| `response_generator.py` | 98% |
| `main.py` | 86% |
| `config.py` | 85% |
| **Total** | **79%** |

### asyncio configuration
`pytest.ini` sets `asyncio_mode = auto` — all `async def test_*` functions are automatically treated as async tests without needing `@pytest.mark.asyncio` (though the existing tests include it explicitly for clarity).

---

## Tech Debt

Known issues to fix — do not perpetuate these patterns when writing new code:

| Location | Issue | What to do instead | Status |
|---|---|---|---|
| `app/api/routes.py` | `print()` calls used for logging | Use `structlog.get_logger()` like services do | Pendente (Fase 1) |
| `app/utils/ai_client.py` | `OpenAIClient` instancia `OpenAI` síncrono com `await` — TypeError em runtime | Trocar para `AsyncOpenAI` do mesmo pacote | Pendente (Fase 1) |

> When touching any of these files, fix the tech debt in the same PR if the change is small. Otherwise, leave a `# TODO:` comment referencing this section.

---

## Environment Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OPENAI_API_KEY` | `` | Required only when `AI_PROVIDER=openai`. Must start with `sk-` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Auto-adjusted for Docker (see Docker networking section) |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Ollama model name |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated CORS origins |
| `MAX_TOKENS` | `500` | Max tokens for AI responses |
| `TEMPERATURE` | `0.7` | AI generation temperature |

### Production (Fly.io + Vercel)
- Backend on **Fly.io** (`fly.toml` in project root, deploy via `fly deploy`)
- Frontend on **Vercel** (`frontend/vercel.json` present, auto-deploy on push)
- Set via `fly secrets set`: `ENVIRONMENT=production`, `AI_PROVIDER=openai`, `OPENAI_API_KEY`, `ALLOWED_ORIGINS`
- `ALLOWED_ORIGINS` must include the Vercel frontend URL and (after Fase 2) the Chrome extension origin: `chrome-extension://EXTENSION_ID`
- `frontend/js/app.js` has `API_BASE_URL` pointing to `https://email-classifier-api.fly.dev` for non-localhost hostnames
- `frontend/js/app.js` has `MAINTENANCE_MODE` flag — set to `false` when backend is live

### Chrome Extension (Fase 2)
- Lives in `extension/` directory — see `sprint-fase-2.md` for full strategy
- Uses Manifest V3 with a service worker (`background.js`) that intermediates all API calls
- Content script (`content_script.js`) reads Gmail email body via DOM and injects the result panel
- Requires the Chrome extension origin to be in `ALLOWED_ORIGINS` on Fly.io
- Published to Chrome Web Store (one-time $5 developer fee)
