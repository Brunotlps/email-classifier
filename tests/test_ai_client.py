from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.schemas import EMAIL_ANALYSIS_JSON_SCHEMA
from app.utils.ai_client import OllamaClient, OpenAIClient


@pytest.mark.asyncio
async def test_ollama_sends_the_structured_output_schema():
    response = Mock()
    response.json.return_value = {"response": '{"summary":"ok"}'}
    http_client = Mock()
    http_client.post = AsyncMock(return_value=response)

    client = object.__new__(OllamaClient)
    client.base_url = "http://ollama.test"
    client.model = "test-model"
    client.client = http_client

    result = await client.generate("prompt", "system", EMAIL_ANALYSIS_JSON_SCHEMA)

    assert result == '{"summary":"ok"}'
    payload = http_client.post.await_args.kwargs["json"]
    assert payload["format"] == EMAIL_ANALYSIS_JSON_SCHEMA
    assert payload["stream"] is False


@pytest.mark.asyncio
async def test_ollama_keeps_plain_text_callers_without_a_schema():
    response = Mock()
    response.json.return_value = {"response": "Olá!"}
    http_client = Mock()
    http_client.post = AsyncMock(return_value=response)

    client = object.__new__(OllamaClient)
    client.base_url = "http://ollama.test"
    client.model = "test-model"
    client.client = http_client

    result = await client.generate("prompt", "system")

    assert result == "Olá!"
    assert "format" not in http_client.post.await_args.kwargs["json"]


@pytest.mark.asyncio
async def test_openai_sends_strict_json_schema():
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"summary":"ok"}'))]
        )
    )
    client = object.__new__(OpenAIClient)
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    result = await client.generate("prompt", "system", EMAIL_ANALYSIS_JSON_SCHEMA)

    assert result == '{"summary":"ok"}'
    kwargs = create.await_args.kwargs
    assert kwargs["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "email_analysis",
            "strict": True,
            "schema": EMAIL_ANALYSIS_JSON_SCHEMA,
        },
    }
