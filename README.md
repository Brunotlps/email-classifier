# Email Classifier
 
> An AI-powered REST API that classifies emails as **productive** or **unproductive** and generates context-aware reply suggestions, built with FastAPI and LLMs.
 
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Coverage-79%25-green?style=flat)]()
[![Status](https://img.shields.io/badge/Backend-Migrating%20to%20VPS-yellow?style=flat)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
 
---
 
## 🔗 Try it live
 
**Frontend:** [email-classifier-ruddy.vercel.app](https://email-classifier-ruddy.vercel.app/)
 
> ⚠️ The backend is currently offline while being migrated from Railway to a self-managed VPS. The frontend is fully navigable, and the full classification flow will be available again once the migration is complete.
 
---
 
## About the Project
 
**Email Classifier** is an AI-powered service that automatically classifies incoming emails as **productive** (meaningful business communication that deserves attention) or **unproductive** (promotional, automated, or low-priority messages), along with a confidence score and automatically generated reply suggestions when appropriate.
 
The project started as a technical challenge for **AutoU**, and I decided to rebuild it from scratch as my own product — with better architecture, more mature engineering practices, and a clear path toward becoming a real tool people can use in their daily workflow. The long-term vision is to turn it into an integration for existing email clients (starting with a Gmail plugin) so that classification and reply suggestions happen directly where users read their emails.
 
---
 
## What it does
 
- **Classifies emails** into `produtivo` or `improdutivo` with a confidence score
- **Generates reply suggestions** for productive emails in multiple tones (`formal`, `cordial`, `casual`, `técnico`)
- **Accepts multiple input formats**: raw text, `.txt`, `.eml`, and `.pdf` file uploads
- **Supports two LLM providers** — Ollama (local, free) for development and OpenAI for production — switchable via a single environment variable
- **Caches repeated requests** to avoid paying twice for the same classification
- **Retries failed AI calls** with exponential backoff
- **Exposes a clean REST API** documented automatically via Swagger and ReDoc
 
---
 
## Project Status
 
🚧 **In active development** — feature-complete and deployed, currently between infrastructure environments.
 
### What's done
 
- Full classification pipeline (input → AI → validated response)
- Reply suggestion generator with tone normalization
- File upload and parsing for `.txt`, `.eml`, and `.pdf`
- Dual AI provider support (Ollama / OpenAI) via factory pattern
- In-memory TTL cache keyed by content hash
- Retry logic with exponential backoff on AI calls
- Rate limiting per route
- Structured logging with `structlog`
- Test suite with **79% overall coverage** (98% on core services)
- Multi-stage Docker build with non-root user
- Frontend SPA (text input + file upload) with local history
 
### What's next
 
- 🟡 **VPS migration** — moving backend from Railway to a self-managed Ubuntu VPS (in progress). The frontend will continue on Vercel.
- 🟡 **Email client integration** — next major milestone after the migration: building a Gmail plugin (or equivalent integration) so classification happens where users actually read their email.
- 🟢 **Customization** — allowing users to define their own categories and thresholds beyond the default productive/unproductive split.
 
---
 
## Tech Stack
 
**Backend**
- FastAPI
- Pydantic (request/response validation and settings)
- `structlog` (structured logging)
- `tenacity` (retry logic)
- `cachetools` (in-memory TTL cache)
 
**AI Providers**
- Ollama with `qwen2.5:3b` (local development)
- OpenAI with `gpt-3.5-turbo` (production)
 
**File Handling**
- `.txt`, `.eml`, and `.pdf` parsing
 
**Testing & Quality**
- `pytest`, `pytest-asyncio`, `pytest-cov`
- Unit tests with mocked AI clients
- Integration tests hitting real AI endpoints
 
**Infrastructure**
- Docker multi-stage build (builder + non-root runtime)
- Docker Compose for local orchestration
- Railway (backend, previous) → VPS (backend, in progress)
- Vercel (frontend, active)
 
---
 
## Architecture Overview
 
The codebase follows a clean layered architecture with clear responsibilities at each level.
 
```
HTTP Request
     ↓
app/api/routes.py              → Pydantic validation, per-route rate limiting, HTTP error mapping
     ↓
app/services/classifier.py     → SHA-256 cache key → TTLCache lookup → AI call with retry → JSON parse
app/services/response_generator.py → AI call → JSON parse → tone normalization → suggestions
     ↓
app/utils/ai_client.py         → Factory pattern: returns OllamaClient or OpenAIClient
     ↓
Ollama (dev) / OpenAI (prod)
```
 
### Project structure
 
```
email-classifier/
├── app/
│   ├── api/
│   │   └── routes.py                  # REST endpoints, rate limiting, HTTP error mapping
│   ├── models/
│   │   └── schemas.py                 # Pydantic request/response models
│   ├── services/
│   │   ├── classifier.py              # EmailClassifier: cache + retry + prompt engineering
│   │   └── response_generator.py      # ResponseGenerator: reply suggestions
│   ├── utils/
│   │   ├── ai_client.py               # AIClient ABC + OllamaClient + OpenAIClient + factory
│   │   └── file_parser.py             # Multi-format file extraction
│   ├── config.py                      # Pydantic Settings (env-based, Docker-aware)
│   └── main.py                        # FastAPI app, CORS, middleware
├── frontend/
│   ├── index.html                     # SPA with text input and file upload tabs
│   ├── js/app.js                      # API calls + localStorage history
│   └── css/style.css
├── tests/
│   ├── fixtures/                      # Sample emails for testing
│   ├── conftest.py                    # Shared fixtures
│   ├── test_api_routes.py             # Integration tests (real AI)
│   ├── test_classifier.py             # Unit tests (mocked AI)
│   ├── test_response_generator.py     # Unit tests (mocked AI)
│   └── test_file_parser.py            # Synchronous file parser tests
├── docker-compose.yml
├── Dockerfile                         # Multi-stage, non-root user
├── requirements.txt
├── pytest.ini
└── .env.example
```
 
---
 
## Technical Highlights
 
A few decisions behind this codebase that go beyond "just make it work":
 
### Provider-agnostic AI layer
The `AIClient` abstract base class defines a single async interface (`generate(prompt, system_prompt) -> str`), with concrete `OllamaClient` and `OpenAIClient` implementations. Switching between a free local model and a paid cloud model requires changing a single environment variable — **no code changes**. This is what allows development to be free and production to be robust, without branching the codebase.
 
### Cache-first classification
`EmailClassifier` computes a SHA-256 hash of the email content and checks a `TTLCache` (max 100 entries, 1-hour TTL) before calling the AI. Cache hits return in microseconds and cost nothing. In a production scenario with repeated similar emails, this directly translates to saved money on LLM calls.
 
### Retry with exponential backoff
AI calls are wrapped with `tenacity`'s `@retry(stop_after_attempt(3), wait_exponential(...))`. Transient failures (network blips, provider rate limits) don't crash user requests.
 
### Graceful degradation on partial failure
When the reply suggestion generator fails, the API still returns a successful classification with an empty suggestions list — classification is never blocked by a downstream failure. This is a small piece of code that reflects a real product mindset: protect the critical path.
 
### Systematic prompt engineering pattern
Both the classifier and the suggestion generator follow the same four-step pattern: `_build_system_prompt`, `_build_user_prompt`, `_extract_json` (regex-based, tolerates models that add commentary around JSON), and `_parse_response` (validates fields and value ranges). This makes the prompt logic consistent, testable, and easy to evolve.
 
### Defensive Docker setup
The `Dockerfile` is a multi-stage build — a builder stage installs dependencies, and a slim runtime stage copies only what's needed and runs as a non-root user. Small image, reduced attack surface, standard industry practice applied from the start.
 
### Tests at two levels
Unit tests mock the AI client via `patch.object(... new_callable=AsyncMock)` so they run fast and deterministically. A smaller set of integration tests uses `fastapi.testclient.TestClient` and hits a real Ollama instance for end-to-end verification. Core services (`classifier.py`, `response_generator.py`) sit at 98% coverage; overall project coverage is 79%.
 
---
 
## Getting Started
 
### Prerequisites
 
- Docker and Docker Compose
- (For local AI) [Ollama](https://ollama.com/) installed on the host with the `qwen2.5:3b` model pulled
 
### Running locally with Ollama
 
```bash
# Clone the repository
git clone https://github.com/Brunotlps/email-classifier.git
cd email-classifier
 
# Set up environment variables
cp .env.example .env
# Edit .env — ensure AI_PROVIDER=ollama
 
# Pull the local model (only once)
ollama pull qwen2.5:3b
 
# Start the API
docker compose up -d
 
# Verify everything is up
curl http://localhost:8001/health
curl http://localhost:8001/test-ai
```
 
### Smoke test
 
```bash
curl -X POST http://localhost:8001/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"email_content": "Prezado, gostaria de agendar uma reunião para discutir o projeto."}'
```
 
### API documentation
 
Once the API is running, interactive docs are available at:
 
- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`
 
### Running tests
 
```bash
# All tests
docker exec -it email_classifier_api pytest tests/ -v
 
# With coverage report
docker exec -it email_classifier_api pytest tests/ --cov=app --cov-report=term
 
# Skip slow/integration tests (no real AI calls)
docker exec -it email_classifier_api pytest tests/ -m "not slow and not integration"
```
 
---
 
## Roadmap
 
### Short term
- Complete VPS migration (Ubuntu server with Docker + Nginx + SSL)
- Bring backend back online with the new infrastructure
- Remove known tech debt in `app/api/routes.py` (replace residual `print()` calls with structured logging)
 
### Medium term
- **Gmail plugin** — integrate directly with an existing email client so classification and reply suggestions happen where users actually read their email
- Expand test coverage from 79% to 90%+
- Add authentication / API keys for external usage
 
### Long term
- User-defined categories and confidence thresholds
- Fine-tuning with real user feedback to improve classification quality over time
- Support for additional email clients beyond Gmail
 
---
 
## About the Author
 
Built and maintained by **Bruno Teixeira Lopes** — a backend developer from Brazil focused on building real, maintainable systems. Email Classifier is where I explore the intersection of traditional backend engineering and modern LLM-powered features: how to integrate AI into a product responsibly, with caching, retries, fallbacks, and cost awareness built in.
 
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/Brunotlps)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/brunotlps)
[![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white)](mailto:brunoteixlps@gmail.com)
 
---
 
⭐ *This is an active personal project. Feedback, ideas, and questions are welcome — open an issue or reach out directly.*

---

## License

This project is licensed under the [MIT License](LICENSE) — see the file for details.