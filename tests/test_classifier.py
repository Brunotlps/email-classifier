import pytest
from unittest.mock import AsyncMock, patch
from app.services.classifier import EmailClassifier


class TestEmailClassifier:
  """Testes da classe EmailClassifier"""
  
  @pytest.fixture
  def classifier(self):
    """Cria instância do classificador para testes"""
    
    return EmailClassifier()
  
  @pytest.mark.asyncio
  async def test_classify_produtivo_success(self, classifier, sample_produtivo_email):
    """Testa classificação de email produtivo"""
    
    mock_response = """{
        "classification": "produtivo",
        "confidence": 0.95,
        "reasoning": "Email solicita reunião de negócios"
    }"""
      
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      result = await classifier.classify(sample_produtivo_email)
      
      assert result["classification"] == "produtivo"
      assert result["confidence"] == 0.95
      assert "reasoning" in result
      assert isinstance(result["reasoning"], str)
  
  @pytest.mark.asyncio
  async def test_classify_improdutivo_success(self, classifier, sample_improdutivo_email):
    """Testa classificação de email improdutivo"""
    
    mock_response = """{
        "classification": "improdutivo",
        "confidence": 0.98,
        "reasoning": "Email é spam promocional"
    }"""
      
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      result = await classifier.classify(sample_improdutivo_email)
      
      assert result["classification"] == "improdutivo"
      assert result["confidence"] == 0.98
  
  @pytest.mark.asyncio
  async def test_classify_invalid_json_raises_error(self, classifier, sample_produtivo_email):
    """Testa que resposta inválida da IA levanta erro"""
    
    mock_response = "Esta não é uma resposta JSON válida"
    
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="JSON válido"):
        await classifier.classify(sample_produtivo_email)
  
  @pytest.mark.asyncio
  async def test_classify_missing_fields_raises_error(self, classifier, sample_produtivo_email):
    """Testa que resposta sem campos obrigatórios levanta erro"""
    
    mock_response = '{"classification": "produtivo"}'
    
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
        
      with pytest.raises(ValueError, match="ausente"):
        await classifier.classify(sample_produtivo_email)
  
  @pytest.mark.asyncio
  async def test_classify_invalid_classification_value(self, classifier, sample_produtivo_email):
    """Testa que valor de classificação inválido levanta erro"""
    
    mock_response = """{
        "classification": "neutro",
        "confidence": 0.5,
        "reasoning": "Teste"
    }"""
    
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="Classificação inválida"):
        await classifier.classify(sample_produtivo_email)
  
  @pytest.mark.asyncio
  async def test_classify_invalid_confidence_range(self, classifier, sample_produtivo_email):
    """Testa que confiança fora do intervalo 0-1 levanta erro"""
    
    mock_response = """{
        "classification": "produtivo",
        "confidence": 1.5,
        "reasoning": "Teste"
    }"""
    
    with patch.object(classifier.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="entre 0 e 1"):
        await classifier.classify(sample_produtivo_email)
  
  def test_extract_json_from_text(self, classifier):
    """Testa extração de JSON de texto com conteúdo adicional"""
    
    text = 'Aqui está o resultado: {"key": "value"} fim'
    result = classifier._extract_json(text)
    
    assert result == '{"key": "value"}'
  
  def test_build_system_prompt(self, classifier):
    """Testa que system prompt contém instruções esperadas"""
    
    prompt = classifier._build_system_prompt()
    
    assert "classificador" in prompt.lower()
    assert "produtivo" in prompt.lower()
    assert "improdutivo" in prompt.lower()
    assert "json" in prompt.lower()
  
  def test_build_user_prompt(self, classifier):
    """Testa construção do user prompt"""
    
    email = "Teste de email"
    prompt = classifier._build_user_prompt(email)
    
    assert email in prompt
    assert "classifique" in prompt.lower()