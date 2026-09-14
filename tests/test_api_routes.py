from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch
from app.api import routes
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


class TestRemovedLegacyEndpoint:
    """Testes da remoção do endpoint legado."""

    def test_classify_returns_404(self):
        response = client.post(
            "/api/v1/classify",
            json={"email_content": "Olá, podemos marcar uma reunião amanhã?"},
        )

        assert response.status_code == 404


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

    @pytest.mark.asyncio
    async def test_analyze_forwards_english_language(self):
        email_content = "Hello, can we schedule a meeting to discuss the contract?"
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
                response = await async_client.post(
                    "/api/v1/analyze",
                    json={"email_content": email_content, "language": "en"},
                )

        assert response.status_code == 200
        mock.assert_awaited_once_with(email_content, "en")

    def test_analyze_service_validation_error_returns_400(self):
        with patch("app.api.routes.analyzer.analyze", new_callable=AsyncMock) as mock:
            mock.side_effect = ValueError("invalid email content")
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

    @pytest.mark.asyncio
    async def test_analyze_invalid_ai_response_returns_sanitized_502(self):
        raw_response = "malformed model output with private content"
        with patch.object(routes.analyzer.ai_client, "generate", new_callable=AsyncMock) as mock:
            mock.return_value = raw_response
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
                response = await async_client.post(
                    "/api/v1/analyze",
                    json={"email_content": "Valid unique email content for invalid AI output."},
                )

        assert response.status_code == 502
        assert response.json() == {
            "detail": "O serviço de IA retornou uma resposta inválida. Tente novamente."
        }
        assert raw_response not in response.text

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

    @pytest.mark.parametrize("filename,extended_filename,expected_status", [
        ("email.exe", "email.txt", 400),
        ("email.txt", "email.exe", 200),
    ])
    def test_upload_uses_plain_filename_when_extended_parameter_conflicts(
        self, filename, extended_filename, expected_status
    ):
        # GHSA-vffw-93wf-4j4q: filename* não pode trocar a extensão validada.
        content = b"Please schedule our project meeting for next week."
        body = (
            b"--upload-boundary\r\n"
            + f'Content-Disposition: form-data; name="file"; filename="{filename}"; '
              f"filename*=UTF-8''{extended_filename}\r\n".encode()
            + b"Content-Type: text/plain\r\n\r\n" + content
            + b"\r\n--upload-boundary--\r\n"
        )
        with patch.object(routes.analyzer, "analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            response = client.post(
                "/api/v1/classify-file", content=body,
                headers={"Content-Type": "multipart/form-data; boundary=upload-boundary"},
            )

        assert response.status_code == expected_status
        if expected_status == 200:
            mock.assert_awaited_once_with(content.decode())
        else:
            mock.assert_not_awaited()

    @pytest.mark.parametrize("boundary,extra_headers", [
        ("upload-boundary", b"X-Extra: value\r\n" * 10),
        ("upload-boundary", b"X-Extra: " + b"a" * 5000 + b"\r\n"),
        ("b" * 257, b""),
    ], ids=["too-many-headers", "oversized-header", "oversized-boundary"])
    def test_upload_rejects_excessive_multipart_metadata(self, boundary, extra_headers):
        # Entradas limitadas: reproduzem a ausência de limites sem um teste de carga.
        body = (
            f"--{boundary}\r\n".encode()
            + b'Content-Disposition: form-data; name="file"; filename="email.txt"\r\n'
            + extra_headers + b"\r\nPlease review this project email.\r\n"
            + f"--{boundary}--\r\n".encode()
        )
        with patch.object(routes.analyzer, "analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            response = client.post(
                "/api/v1/classify-file", content=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )

        assert response.status_code == 400
        mock.assert_not_awaited()

    def test_upload_without_multipart_boundary_is_rejected(self):
        with patch.object(routes.analyzer, "analyze", new_callable=AsyncMock) as mock:
            response = client.post(
                "/api/v1/classify-file", content=b"invalid multipart body",
                headers={"Content-Type": "multipart/form-data"},
            )
        assert response.status_code == 400
        mock.assert_not_awaited()

    def test_classify_file_with_eml_preserves_extracted_content(self):
        content = (
            b"From: sender@example.com\r\nSubject: Meeting\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            b"Please schedule our meeting."
        )
        with patch.object(routes.analyzer, "analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            response = client.post(
                "/api/v1/classify-file",
                files={"file": ("email.eml", content, "message/rfc822")},
            )
        assert response.status_code == 200
        mock.assert_awaited_once_with(
            "De: sender@example.com\nAssunto: Meeting\n\nPlease schedule our meeting."
        )

    def test_classify_file_with_pdf_preserves_extracted_content(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        # PDF real e pequeno em memória; somente a chamada de IA é simulada.
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        page = writer.pages[0]
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        })
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 20 200 Td (Please schedule our meeting.) Tj ET")
        page[NameObject("/Contents")] = stream
        pdf = BytesIO()
        writer.write(pdf)

        with patch.object(routes.analyzer, "analyze", new_callable=AsyncMock) as mock:
            mock.return_value = _VALID_ANALYSIS
            response = client.post(
                "/api/v1/classify-file",
                files={"file": ("email.pdf", pdf.getvalue(), "application/pdf")},
            )
        assert response.status_code == 200, response.text
        mock.assert_awaited_once_with("Please schedule our meeting.")

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

    @pytest.mark.asyncio
    async def test_classify_file_invalid_ai_response_returns_502(self):
        raw_response = "malformed file-analysis output with private content"
        with patch.object(routes.analyzer.ai_client, "generate", new_callable=AsyncMock) as mock:
            mock.return_value = raw_response
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
                response = await async_client.post(
                    "/api/v1/classify-file",
                    files={
                        "file": (
                            "email.txt",
                            b"Valid unique file content for invalid AI output.",
                            "text/plain",
                        )
                    },
                )

        assert response.status_code == 502
        assert response.json() == {
            "detail": "O serviço de IA retornou uma resposta inválida. Tente novamente."
        }
        assert raw_response not in response.text


class TestHealthEndpoints:
    """Testes dos endpoints de health check"""

    def test_root_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_analysis_health_endpoint(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "email-analysis",
            "analyzer": "operational",
        }

    def test_test_ai_endpoint(self):
        with patch("app.utils.ai_client.get_ai_client") as factory:
            factory.return_value.generate = AsyncMock(return_value="Olá!")
            response = client.get("/test-ai")

        factory.return_value.generate.assert_awaited_once_with(
            prompt="Me diga olá em uma frase curta",
            system_prompt="Você é um assistente útil",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["provider"] == "ollama"
        assert data["response"] == "Olá!"

    def test_test_ai_unavailable_provider_returns_error_body(self):
        with patch("app.utils.ai_client.get_ai_client") as factory:
            factory.return_value.generate = AsyncMock(side_effect=RuntimeError("AI unavailable"))
            response = client.get("/test-ai")

        assert response.status_code == 200
        assert response.json() == {"status": "error", "error": "AI unavailable"}


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
        assert data["info"]["title"] == "BriskMail API"

    def test_openapi_exposes_only_active_analysis_endpoints(self):
        paths = client.get("/openapi.json").json()["paths"]

        assert "/api/v1/classify" not in paths
        assert "/api/v1/analyze" in paths
        assert "/api/v1/classify-file" in paths

    @pytest.mark.asyncio
    async def test_ai_endpoints_document_invalid_response_as_502(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            response = await async_client.get("/openapi.json")

        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "502" in paths["/api/v1/analyze"]["post"]["responses"]
        assert "502" in paths["/api/v1/classify-file"]["post"]["responses"]
