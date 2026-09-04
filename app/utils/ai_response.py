import hashlib
from typing import NoReturn

import structlog

from app.config import settings
from app.exceptions import InvalidAIResponseError


logger = structlog.get_logger()


def raise_invalid_ai_response(
    *,
    service: str,
    response: object,
    reason: str,
    cause: Exception,
) -> NoReturn:
    """Registra diagnóstico seguro e emite um erro upstream sanitizado."""
    response_text = response if isinstance(response, str) else repr(response)
    log_context = {
        "service": service,
        "reason": reason,
        "response_type": type(response).__name__,
        "response_length": len(response_text),
        "response_hash": hashlib.sha256(response_text.encode()).hexdigest()[:12],
        "ai_provider": settings.ai_provider,
        "ai_model": (
            settings.ollama_model
            if settings.ai_provider == "ollama"
            else settings.openai_model
        ),
    }

    if settings.environment != "production":
        log_context["response_preview"] = response_text.strip()[:200]

    logger.warning("ai_response_invalid", **log_context)
    raise InvalidAIResponseError() from cause
