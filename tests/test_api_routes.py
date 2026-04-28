import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


client = TestClient(app)

_VALID_ANALYSIS = {
    "summary": "Carlos is requesting a meeting to discuss contract renewal.",
    "category": "Reunião / Agenda",
    "priority": "normal",
    "action_required": True,
    "suggestions": [
        {"title": "Confirm meeting", "content": "Hi Carlos, Thursday works for me.", "tone": "cordial"},
    ],
}


class TestClassifyEndpoint:
    """Testes do endpoint /api/v1/classify"""

    def test_classify_endpoint_exists(self):
        response = client.post("/api/v1/classify", json={"email_content": "test"})
        assert response.status_code != 404

    def test_classify_with_valid_email(self):
        payload = {
            "email_content": "Olá, gostaria de agendar uma reunião para discutir parceria."
        }
        response = client.post("/api/v1/classify", json=payload, timeout=30.0)
        assert response.status_code == 200
        data = response.json()
        assert "classification" in data
        assert data["classification"] in ["produtivo", "improdutivo"]
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1
        assert "reasoning" in data
        assert "suggestions" in data

    def test_classify_with_short_email_fails(self):
        response = client.post("/api/v1/classify", json={"email_content": "oi"})
        assert response.status_code == 422

    def test_classify_without_email_content_fails(self):
        response = client.post("/api/v1/classify", json={})
        assert response.status_code == 422


class TestAnalyzeEndpoint:
    """Testes do endpoint /api/v1/analyze"""

    def test_analyze_endpoint_exists(self):
        response = client.post("/api/v1/analyze", json={"email_content": "test"})
        assert response.status_code != 404

    def test_analyze_with_short_email_fails(self):
        response = client.post("/api/v1/analyze", json={"email_content": "oi"})
        assert response.status_code == 422

    def test_analyze_without_email_content_fails(self):
        response = client.post("/api/v1/analyze", json={})
        assert response.status_code == 422

    def test_analyze_returns_all_fields(self):
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            response = client.post(
                "/api/v1/analyze",
                json={"email_content": "Olá, podemos marcar uma reunião para discutir o contrato?"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == _VALID_ANALYSIS["summary"]
        assert data["category"] == "Reunião / Agenda"
        assert data["priority"] == "normal"
        assert data["action_required"] is True
        assert len(data["suggestions"]) == 1

    def test_analyze_invalid_email_returns_400(self):
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.side_effect = ValueError("not valid JSON")
            response = client.post(
                "/api/v1/analyze",
                json={"email_content": "Olá, podemos marcar uma reunião para discutir o contrato?"},
            )

        assert response.status_code == 400

    def test_analyze_ai_error_returns_500(self):
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("AI unavailable")
            response = client.post(
                "/api/v1/analyze",
                json={"email_content": "Olá, podemos marcar uma reunião para discutir o contrato?"},
            )

        assert response.status_code == 500

    def test_analyze_no_suggestions_when_not_action_required(self):
        result_no_action = {**_VALID_ANALYSIS, "action_required": False, "suggestions": []}
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.return_value = result_no_action
            response = client.post(
                "/api/v1/analyze",
                json={"email_content": "Newsletter sobre promoções da semana."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["action_required"] is False
        assert data["suggestions"] == []


class TestClassifyFileEndpoint:
    """Testes do endpoint /api/v1/classify-file"""

    def test_classify_file_endpoint_exists(self):
        response = client.post("/api/v1/classify-file")
        assert response.status_code != 404

    def test_classify_file_with_txt(self, sample_txt_file):
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            with open(sample_txt_file, 'rb') as f:
                files = {"file": ("test.txt", f, "text/plain")}
                response = client.post("/api/v1/classify-file", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "category" in data
        assert "priority" in data
        assert "action_required" in data
        assert "suggestions" in data

    def test_classify_file_with_empty_file_fails(self, sample_empty_file):
        with open(sample_empty_file, 'rb') as f:
            files = {"file": ("empty.txt", f, "text/plain")}
            response = client.post("/api/v1/classify-file", files=files)

        assert response.status_code == 400
        assert "vazio" in response.json()["detail"].lower()

    def test_classify_file_with_large_file_fails(self, sample_large_file):
        with open(sample_large_file, 'rb') as f:
            files = {"file": ("large.txt", f, "text/plain")}
            response = client.post("/api/v1/classify-file", files=files)

        assert response.status_code == 400
        assert "grande" in response.json()["detail"].lower()

    def test_classify_file_with_unsupported_extension_fails(self, tmp_path):
        unsupported_file = tmp_path / "test.docx"
        unsupported_file.write_bytes(b"fake docx content")

        with open(unsupported_file, 'rb') as f:
            files = {"file": ("test.docx", f, "application/vnd.openxmlformats")}
            response = client.post("/api/v1/classify-file", files=files)

        assert response.status_code == 400
        assert "suportado" in response.json()["detail"].lower()


class TestHealthEndpoints:
    """Testes dos endpoints de health check"""

    def test_root_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_classification_health_endpoint(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "email-classification"

    def test_test_ai_endpoint(self):
        response = client.get("/test-ai", timeout=30.0)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "provider" in data


class TestSwaggerDocs:
    """Testes da documentação automática"""

    def test_swagger_ui_accessible(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_accessible(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Email Classifier API"
