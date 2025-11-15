import pytest
from unittest.mock import AsyncMock, patch
from app.services.response_generator import ResponseGenerator
from app.models.schemas import ResponseSuggestion


@pytest.fixture
def generator():
  """Cria instância do gerador para testes"""
  
  return ResponseGenerator()

class TestResponseGenerator:
  """Testes da classe ResponseGenerator"""
    
  @pytest.mark.asyncio
  async def test_generate_suggestions_success(self, generator, sample_produtivo_email):
    """Testa geração de sugestões com sucesso"""
    
    mock_response = """{
        "suggestions": [
            {
                "title": "Resposta cordial",
                "content": "Olá! Agradeço o contato. Podemos agendar para terça-feira às 14h.",
                "tone": "cordial"
            },
            {
                "title": "Resposta formal",
                "content": "Prezado Sr., Em resposta à sua solicitação...",
                "tone": "formal"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      result = await generator.generate_suggestions(sample_produtivo_email, num_suggestions=2)
      
      assert len(result) == 2
      assert all(isinstance(s, ResponseSuggestion) for s in result)
      assert result[0].title == "Resposta cordial"
      assert result[0].tone == "cordial"
      assert result[1].tone == "formal"
  
  @pytest.mark.asyncio
  async def test_generate_suggestions_with_custom_num(self, generator, sample_produtivo_email):
    """Testa geração com número customizado de sugestões"""
    
    mock_response = """{
        "suggestions": [
            {
                "title": "Sugestão 1",
                "content": "Conteúdo 1",
                "tone": "cordial"
            },
            {
                "title": "Sugestão 2",
                "content": "Conteúdo 2",
                "tone": "formal"
            },
            {
                "title": "Sugestão 3",
                "content": "Conteúdo 3",
                "tone": "técnico"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      result = await generator.generate_suggestions(sample_produtivo_email, num_suggestions=3)
      
      assert len(result) == 3
  
  @pytest.mark.asyncio
  async def test_generate_suggestions_invalid_json_raises_error(self, generator, sample_produtivo_email):
    """Testa que resposta JSON inválida levanta erro"""
    
    mock_response = "Isto não é JSON válido"
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="JSON válido"):
        await generator.generate_suggestions(sample_produtivo_email)
  
  @pytest.mark.asyncio
  async def test_generate_suggestions_missing_field_raises_error(self, generator, sample_produtivo_email):
    """Testa que sugestão sem campo obrigatório levanta erro"""
    
    mock_response = """{
        "suggestions": [
            {
                "title": "Resposta",
                "content": "Conteúdo"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="ausente"):
        await generator.generate_suggestions(sample_produtivo_email)
  
  @pytest.mark.asyncio
  async def test_generate_suggestions_empty_field_raises_error(self, generator, sample_produtivo_email):
    """Testa que campo vazio levanta erro"""
    
    mock_response = """{
        "suggestions": [
            {
                "title": "",
                "content": "Conteúdo",
                "tone": "cordial"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      with pytest.raises(ValueError, match="string não vazia"):
        await generator.generate_suggestions(sample_produtivo_email)
  
  def test_normalize_tone_valid_tones(self, generator):
    """Testa normalização de tons válidos"""
    
    assert generator._normalize_tone("formal") == "formal"
    assert generator._normalize_tone("cordial") == "cordial"
    assert generator._normalize_tone("casual") == "casual"
    assert generator._normalize_tone("técnico") == "técnico"
  
  def test_normalize_tone_variations(self, generator):
    """Testa normalização de variações de tom"""
    
    assert generator._normalize_tone("FORMAL") == "formal"
    assert generator._normalize_tone("Cordial") == "cordial"
    assert generator._normalize_tone("tecnico") == "técnico"
    assert generator._normalize_tone("amigável") == "cordial"
    assert generator._normalize_tone("profissional") == "formal"
  
  def test_normalize_tone_unknown_defaults_to_cordial(self, generator):
    """Testa que tom desconhecido usa cordial como padrão"""
    
    assert generator._normalize_tone("desconhecido") == "cordial"
    assert generator._normalize_tone("outro") == "cordial"
  
  def test_extract_json_from_text(self, generator):
    """Testa extração de JSON de texto com conteúdo adicional"""
    
    text = 'Aqui está a resposta: {"suggestions": []} fim'
    result = generator._extract_json(text)
    
    assert result == '{"suggestions": []}'
  
  def test_build_system_prompt(self, generator):
    """Testa que system prompt contém instruções esperadas"""
    
    prompt = generator._build_system_prompt(num_suggestions=2)
    
    assert "2" in prompt
    assert "sugestões" in prompt.lower()
    assert "json" in prompt.lower()
    assert "tone" in prompt.lower()
  
  def test_build_user_prompt(self, generator):
    """Testa construção do user prompt"""
    
    email = "Teste de email"
    prompt = generator._build_user_prompt(email)
    
    assert email in prompt
    assert "sugestões" in prompt.lower()


class TestResponseGeneratorIntegration:
  """Testes de integração com diferentes tipos de email"""
  
  @pytest.mark.asyncio
  async def test_generate_for_business_email(self, generator):
    """Testa geração para email de negócios"""
    
    email = "Prezados, gostaria de solicitar um orçamento para desenvolvimento de software."
    
    mock_response = """{
        "suggestions": [
            {
                "title": "Resposta comercial",
                "content": "Prezado cliente, ficamos felizes com seu interesse...",
                "tone": "formal"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      result = await generator.generate_suggestions(email)
      
      assert len(result) > 0
      assert result[0].tone in ["formal", "cordial", "casual", "técnico"]
  
  @pytest.mark.asyncio
  async def test_generate_for_technical_email(self, generator):
    """Testa geração para email técnico"""
    
    email = "Estou enfrentando erro 500 na API de autenticação. Podem verificar os logs?"
    
    mock_response = """{
        "suggestions": [
            {
                "title": "Resposta técnica",
                "content": "Identificamos o problema no endpoint de auth. Seguem logs...",
                "tone": "técnico"
            }
        ]
    }"""
    
    with patch.object(generator.ai_client, 'generate', new_callable=AsyncMock) as mock_generate:
      mock_generate.return_value = mock_response
      
      result = await generator.generate_suggestions(email)
      
      assert len(result) > 0
      assert result[0].tone == "técnico"