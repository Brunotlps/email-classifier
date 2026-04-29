# BriskMail

> AI-powered email analysis directly inside Gmail — summary, category, priority, and reply suggestions in one click.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Coverage-84%25-green?style=flat)]()
[![Backend](https://img.shields.io/badge/Backend-Fly.io-blueviolet?style=flat)](https://email-classifier-api.fly.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Try it live

**Web app:** [email-classifier-ruddy.vercel.app](https://email-classifier-ruddy.vercel.app/)

**Chrome Extension:** submitted to the Chrome Web Store — link coming soon after review.

---

## About

BriskMail is an AI-powered email analysis tool that integrates directly into Gmail via a Chrome extension. Open any email, click **Analyze Email**, and get:

- **Summary** — what the email is actually about, in 2–3 sentences
- **Category** — Business Proposal, Meeting, Technical Support, Billing, Newsletter, and more
- **Priority** — High, Normal, or Low, based on urgency signals
- **Action required** — whether the email needs a response
- **Reply suggestions** — three ready-to-copy drafts in different tones (formal, cordial, casual)

Supports **Portuguese and English** — switch languages anytime from the extension popup.

---

## Architecture

```
Gmail (Chrome Extension)
    ↓ content_script.js reads email body
    ↓ background.js sends HTTPS request
    ↓
FastAPI backend (Fly.io)
    ↓ EmailAnalyzer: cache → AI call → JSON parse
    ↓
OpenAI (production) / Ollama (local dev)
```

### Project structure

```
email-classifier/
├── app/
│   ├── api/routes.py              # REST endpoints, rate limiting, HTTP error mapping
│   ├── models/schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── analyzer.py            # EmailAnalyzer: summary, category, priority, suggestions
│   │   └── response_generator.py  # Reply suggestion generator
│   ├── utils/
│   │   ├── ai_client.py           # AIClient ABC + OllamaClient + OpenAIClient + factory
│   │   └── file_parser.py         # .txt / .eml / .pdf extraction
│   ├── config.py                  # Pydantic Settings (env-based, Docker-aware)
│   └── main.py                    # FastAPI app, CORS, middleware
├── extension/                     # Chrome Extension (Manifest V3)
│   ├── manifest.json              # Permissions, host_permissions, web_accessible_resources
│   ├── content_script.js          # Gmail DOM injection, MutationObserver, PT/EN UI
│   ├── background.js              # Service worker — intermediates API calls
│   ├── popup/                     # Extension popup (status, PT/EN toggle, how-to)
│   ├── panel/                     # Result panel injected inside Gmail
│   └── assets/                    # Icons 16/48/128px, promo tile
├── frontend/                      # Web SPA (Vercel)
│   ├── index.html
│   ├── js/app.js
│   ├── css/style.css
│   └── privacy.html               # Privacy policy (required for Chrome Web Store)
├── tests/
│   ├── conftest.py
│   ├── test_api_routes.py
│   ├── test_analyzer.py
│   ├── test_response_generator.py
│   └── test_file_parser.py
├── docker-compose.yml
├── Dockerfile
├── fly.toml
└── requirements.txt
```

---

## Key technical decisions

**Provider-agnostic AI layer** — `AIClient` ABC with `OllamaClient` (local, free) and `OpenAIClient` (production). Switch via `AI_PROVIDER` env var — no code changes.

**Language-aware cache** — cache key is `SHA-256(language + email_content)`, so PT and EN analyses for the same email are cached independently.

**Graceful degradation** — if reply suggestion generation fails, classification still returns successfully with `suggestions: []`. The critical path is never blocked.

**Prompt engineering pattern** — both `EmailAnalyzer` and `ResponseGenerator` follow: `_build_system_prompt` → `_build_user_prompt` → AI call → `_extract_json` (regex, tolerates model commentary) → `_parse_response` (validates fields).

**DOM-based Gmail integration** — the extension reads email content via `div.a3s.innerText` and uses `MutationObserver` to detect newly opened emails. No OAuth required for the MVP.

---

## Getting started (local dev)

### Prerequisites

- Docker and Docker Compose
- [Ollama](https://ollama.com/) installed on the host with `qwen2.5:3b` pulled

```bash
git clone https://github.com/Brunotlps/email-classifier.git
cd email-classifier

cp .env.example .env
# Edit .env: set AI_PROVIDER=ollama

ollama pull qwen2.5:3b

docker compose up -d
curl http://localhost:8001/health
```

### Smoke test

```bash
curl -X POST http://localhost:8001/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"email_content": "Prezado, gostaria de agendar uma reunião para discutir o projeto.", "language": "pt"}'
```

### API docs

- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`

### Running tests

```bash
docker exec -it email_classifier_api pytest tests/ -v
docker exec -it email_classifier_api pytest tests/ --cov=app --cov-report=term
docker exec -it email_classifier_api pytest tests/ -m "not slow and not integration"
```

---

## Chrome Extension (local install)

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `extension/` folder
4. Open Gmail and open any email

---

## Project status

| Component | Status |
|---|---|
| FastAPI backend | Live on Fly.io |
| Web frontend | Live on Vercel |
| Chrome Extension | Submitted for Chrome Web Store review |
| PT/EN support | Complete |
| Test coverage | 84% |

---

## Roadmap

**Next (post-store approval)**
- Add Chrome Web Store link to this README
- Collect real user feedback
- Expand test coverage to 90%+

**Medium term**
- Gmail API + OAuth (replace DOM scraping for robustness)
- User-defined categories and thresholds
- API key authentication for external usage

**Long term**
- Support for additional email clients
- Cloud history across devices

---

## About

Built and maintained by **Bruno Teixeira Lopes** — a backend developer from Brazil.

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/Brunotlps)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/brunotlps)
[![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white)](mailto:contatobriskmail@gmail.com)

---

## License

[MIT License](LICENSE)
