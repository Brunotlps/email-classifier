"""Smoke pós-deploy: respostas controladas, sem rede nem serviços reais."""
from io import BytesIO
from unittest.mock import Mock
from urllib.error import URLError

import pytest

from scripts.ci import public_health


def response(body, status=200):
    result = BytesIO(body)
    result.status = status
    return result


def run_probe(monkeypatch, responses, attempts=1):
    opener = Mock()
    opener.open.side_effect = responses
    monkeypatch.setattr(public_health, "build_opener", lambda *args: opener)
    monkeypatch.setattr(public_health.time, "sleep", Mock())
    result = public_health.check_health("https://example.invalid/health", attempts=attempts)
    return result, opener


def test_healthy_http_200_succeeds(monkeypatch):
    result, opener = run_probe(monkeypatch, [response(b'{"status":"healthy"}')])
    assert result is True
    opener.open.assert_called_once_with("https://example.invalid/health", timeout=10)


@pytest.mark.parametrize("body,status", [
    (b'{"status":"error"}', 200), (b'not json', 200),
    (b'{"status":"healthy"}', 503), (b'{}', 200),
])
def test_unhealthy_or_invalid_response_fails(monkeypatch, body, status):
    result, _ = run_probe(monkeypatch, [response(body, status)])
    assert result is False


def test_transient_network_failure_retries(monkeypatch):
    result, opener = run_probe(monkeypatch, [URLError("timeout"), response(b'{"status":"healthy"}')], attempts=2)
    assert result is True
    assert opener.open.call_count == 2
    public_health.time.sleep.assert_called_once_with(5)


def test_persistent_failure_exhausts_budget(monkeypatch):
    result, opener = run_probe(monkeypatch, [URLError("offline")] * 3, attempts=3)
    assert result is False
    assert opener.open.call_count == 3
    assert public_health.time.sleep.call_count == 2


def test_redirect_is_not_followed():
    assert public_health.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid") is None
