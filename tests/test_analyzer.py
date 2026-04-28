import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.analyzer import EmailAnalyzer


_VALID_RESPONSE = json.dumps({
    "summary": "Carlos is requesting a meeting to discuss contract renewal.",
    "category": "Reunião / Agenda",
    "priority": "normal",
    "action_required": True,
    "suggestions": [
        {"title": "Confirm meeting", "content": "Hi Carlos, Thursday works for me.", "tone": "cordial"},
        {"title": "Propose alternative", "content": "Hi Carlos, could we meet next week instead?", "tone": "formal"},
    ],
})


class TestEmailAnalyzer:
    """Testes unitários para EmailAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        return EmailAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_success_returns_all_fields(self, analyzer, sample_produtivo_email):
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_RESPONSE
            result = await analyzer.analyze(sample_produtivo_email)

        assert result["summary"] == "Carlos is requesting a meeting to discuss contract renewal."
        assert result["category"] == "Reunião / Agenda"
        assert result["priority"] == "normal"
        assert result["action_required"] is True
        assert len(result["suggestions"]) == 2

    @pytest.mark.asyncio
    async def test_analyze_invalid_json_raises_value_error(self, analyzer, sample_produtivo_email):
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = "This is not JSON at all"
            with pytest.raises(ValueError, match="not valid JSON"):
                await analyzer.analyze(sample_produtivo_email)

    @pytest.mark.asyncio
    async def test_analyze_missing_summary_raises_error(self, analyzer, sample_produtivo_email):
        incomplete = json.dumps({
            "category": "Outro",
            "priority": "normal",
            "action_required": False,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = incomplete
            with pytest.raises(ValueError, match="Missing required field"):
                await analyzer.analyze(sample_produtivo_email)

    @pytest.mark.asyncio
    async def test_analyze_missing_category_raises_error(self, analyzer, sample_produtivo_email):
        incomplete = json.dumps({
            "summary": "Test",
            "priority": "normal",
            "action_required": False,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = incomplete
            with pytest.raises(ValueError, match="Missing required field"):
                await analyzer.analyze(sample_produtivo_email)

    @pytest.mark.asyncio
    async def test_analyze_invalid_category_falls_back_to_outro(self, analyzer, sample_produtivo_email):
        response = json.dumps({
            "summary": "Test",
            "category": "InvalidCategory",
            "priority": "normal",
            "action_required": False,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = response
            result = await analyzer.analyze(sample_produtivo_email)

        assert result["category"] == "Outro"

    @pytest.mark.asyncio
    async def test_analyze_invalid_priority_falls_back_to_normal(self, analyzer, sample_produtivo_email):
        response = json.dumps({
            "summary": "Test",
            "category": "Outro",
            "priority": "urgente",
            "action_required": False,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = response
            result = await analyzer.analyze(sample_produtivo_email)

        assert result["priority"] == "normal"

    @pytest.mark.asyncio
    async def test_analyze_missing_suggestions_key_defaults_to_empty_list(self, analyzer, sample_produtivo_email):
        response = json.dumps({
            "summary": "Test",
            "category": "Alerta / Notificação",
            "priority": "baixa",
            "action_required": False,
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = response
            result = await analyzer.analyze(sample_produtivo_email)

        assert result["suggestions"] == []

    @pytest.mark.asyncio
    async def test_analyze_action_required_non_bool_is_coerced_to_bool(self, analyzer, sample_produtivo_email):
        response = json.dumps({
            "summary": "Test",
            "category": "Outro",
            "priority": "normal",
            "action_required": 1,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = response
            result = await analyzer.analyze(sample_produtivo_email)

        assert isinstance(result["action_required"], bool)
        assert result["action_required"] is True

    @pytest.mark.asyncio
    async def test_analyze_extracts_json_from_surrounding_text(self, analyzer, sample_produtivo_email):
        wrapped = f"Here is my analysis:\n{_VALID_RESPONSE}\nThat's all."
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = wrapped
            result = await analyzer.analyze(sample_produtivo_email)

        assert result["category"] == "Reunião / Agenda"

    @pytest.mark.asyncio
    async def test_analyze_cache_hit_skips_second_ai_call(self, analyzer, sample_produtivo_email):
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_RESPONSE
            await analyzer.analyze(sample_produtivo_email)
            await analyzer.analyze(sample_produtivo_email)

        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_different_emails_make_separate_ai_calls(self, analyzer, sample_produtivo_email, sample_improdutivo_email):
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_RESPONSE
            await analyzer.analyze(sample_produtivo_email)
            await analyzer.analyze(sample_improdutivo_email)

        assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_all_valid_priorities(self, analyzer, sample_produtivo_email):
        for priority in ("alta", "normal", "baixa"):
            new_analyzer = EmailAnalyzer()
            response = json.dumps({
                "summary": "Test",
                "category": "Outro",
                "priority": priority,
                "action_required": False,
                "suggestions": [],
            })
            with patch.object(new_analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
                mock.return_value = response
                result = await new_analyzer.analyze(sample_produtivo_email)

            assert result["priority"] == priority

    @pytest.mark.asyncio
    async def test_analyze_newsletter_category(self, analyzer, sample_improdutivo_email):
        response = json.dumps({
            "summary": "Promotional newsletter with no action needed.",
            "category": "Newsletter / Marketing",
            "priority": "baixa",
            "action_required": False,
            "suggestions": [],
        })
        with patch.object(analyzer.ai_client, 'generate', new_callable=AsyncMock) as mock:
            mock.return_value = response
            result = await analyzer.analyze(sample_improdutivo_email)

        assert result["category"] == "Newsletter / Marketing"
        assert result["action_required"] is False
        assert result["suggestions"] == []
