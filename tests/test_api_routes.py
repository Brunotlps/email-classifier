import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


client = TestClient(app)


class TestClassifyEndpoint:
  """Testes do endpoint /api/v1/classify"""
  
  def test_classify_endpoint_exists(self):
    """Testa que endpoint existe e aceita POST"""
    
    response = client.post("/api/v1/classify", json={"email_content": "test"})
    # Não deve retornar 404
    assert response.status_code != 404
  
  def test_classify_with_valid_email(self):
    """Testa classificação com email válido"""
    payload = {
        "email_content": "Olá, gostaria de agendar uma reunião para discutir parceria."
    }
    
    # Como usa IA real, pode demorar - adicione timeout maior se necessário
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
    """Testa que email muito curto falha na validação"""
    
    payload = {"email_content": "oi"}  # Menos que 10 caracteres
    
    response = client.post("/api/v1/classify", json=payload)
    
    assert response.status_code == 422  # Validation error
  
  def test_classify_without_email_content_fails(self):
    """Testa que requisição sem email_content falha"""
    
    response = client.post("/api/v1/classify", json={})
    
    assert response.status_code == 422


class TestClassifyFileEndpoint:
  """Testes do endpoint /api/v1/classify-file"""
  
  def test_classify_file_endpoint_exists(self):
    """Testa que endpoint de upload existe"""
    
    response = client.post("/api/v1/classify-file")
    # Não deve retornar 404
    assert response.status_code != 404
  
  def test_classify_file_with_txt(self, sample_txt_file):
    """Testa upload de arquivo .txt"""
    with open(sample_txt_file, 'rb') as f:
      files = {"file": ("test.txt", f, "text/plain")}
      response = client.post("/api/v1/classify-file", files=files, timeout=30.0)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "classification" in data
    assert data["classification"] in ["produtivo", "improdutivo"]
    
    def test_classify_file_with_empty_file_fails(self, sample_empty_file):
      """Testa que arquivo vazio retorna erro"""
      
      with open(sample_empty_file, 'rb') as f:
        files = {"file": ("empty.txt", f, "text/plain")}
        response = client.post("/api/v1/classify-file", files=files)
      
      assert response.status_code == 400
      assert "vazio" in response.json()["detail"].lower()
    
    def test_classify_file_with_large_file_fails(self, sample_large_file):
      """Testa que arquivo muito grande retorna erro"""
      
      with open(sample_large_file, 'rb') as f:
        files = {"file": ("large.txt", f, "text/plain")}
        response = client.post("/api/v1/classify-file", files=files)
      
      assert response.status_code == 400
      assert "grande" in response.json()["detail"].lower()
    
    def test_classify_file_with_unsupported_extension_fails(self, tmp_path):
      """Testa que extensão não suportada retorna erro"""
      
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
    """Testa endpoint raiz /health"""
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
  
  def test_classification_health_endpoint(self):
    """Testa endpoint /api/v1/health"""
    
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "email-classification"
  
  def test_test_ai_endpoint(self):
    """Testa endpoint /test-ai"""
    
    response = client.get("/test-ai", timeout=30.0)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "provider" in data


class TestSwaggerDocs:
  """Testes da documentação automática"""
  
  def test_swagger_ui_accessible(self):
    """Testa que Swagger UI está acessível"""
    response = client.get("/docs")
    
    assert response.status_code == 200
  
  def test_openapi_json_accessible(self):
    """Testa que OpenAPI JSON está acessível"""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "info" in data
    assert data["info"]["title"] == "Email Classifier API"