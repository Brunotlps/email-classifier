from unittest.mock import patch

import pytest

from app.exceptions import InvalidAIResponseError
from app.utils import ai_response


def test_invalid_ai_response_production_log_omits_raw_output():
    raw_response = "malformed model output with private content"

    with (
        patch.object(ai_response.settings, "environment", "production"),
        patch.object(ai_response.logger, "warning") as warning,
        pytest.raises(InvalidAIResponseError, match="resposta inválida") as exc_info,
    ):
        ai_response.raise_invalid_ai_response(
            service="analyzer",
            response=raw_response,
            reason="invalid_json",
            cause=ValueError("synthetic parse failure"),
        )

    log_context = warning.call_args.kwargs
    assert "response_preview" not in log_context
    assert log_context["response_length"] == len(raw_response)
    assert len(log_context["response_hash"]) == 12
    assert raw_response not in str(exc_info.value)
