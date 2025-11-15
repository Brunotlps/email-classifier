import json
import re
from typing import Dict, Any
from app.utils.ai_client import get_ai_client

class EmailClassifier:
  """
  Classifica emails como produtivos ou improdutivos utilizando modelos de IA
  
  - Produtivo: Emails que requerem uma ação ou resposta específica (ex.: solicitações de suporte técnico, atualização sobre casos em aberto, dúvidas sobre o sistema).
  - Improdutivo: Emails que não necessitam de uma ação imediata (ex.: mensagens de felicitações, agradecimentos).
  """

  def __init__(self):
    self.ai_client = get_ai_client()

  async def classify(self, email_content: str) -> Dict[str, Any]:
    """
    Classifica um email e retorna análise detalhada.
    
    Args:
        email_content: Conteúdo do email a ser classificado
        
    Returns:
        Dict contendo:
            - classification: "produtivo" ou "improdutivo"
            - confidence: float entre 0 e 1
            - reasoning: explicação da classificação
            
    Raises:
        Exception: Se houver erro na comunicação com a IA
    """

    # Variáveis de prompt engineering
    system_prompt = self._build_system_prompt()
    user_prompt = self._build_user_prompt(email_content)

    # Chamada da IA
    response = await self.ai_client.generate(
      prompt=user_prompt,
      system_prompt=system_prompt
    )

    # Parse da resposta JSON
    result = self._parse_response(response)

    return result

  def _build_system_prompt(self) -> str:
    """
    Constrói o prompt do sistema com instruções de classificação.
    
    Este prompt define:
    - O papel da IA
    - Critérios de classificação
    - Formato de resposta esperado
    """

    return """
      Você é um classificador especialista de emails corporativos.

      Sua tarefa é analisar emails e classificá-los como:

      **PRODUTIVO**: 
      - Solicitações de informação legítimas
      - Oportunidades de negócio
      - Pedidos de reunião/orçamento
      - Questões que requerem resposta
      - Comunicações profissionais importantes
      - Emails que requerem uma ação ou resposta específica (ex.: solicitações de suporte técnico, atualização sobre casos em aberto, dúvidas sobre o sistema).

      **IMPRODUTIVO**:
      - Spam ou phishing
      - Marketing não solicitado
      - Newsletters genéricas
      - Promoções não relacionadas
      - Emails automatizados sem valor
      - Emails que não necessitam de uma ação imediata (ex.: mensagens de felicitações, agradecimentos).

      IMPORTANTE: Responda APENAS com JSON válido no formato:
      {
        "classification": "produtivo" ou "improdutivo",
        "confidence": número entre 0.0 e 1.0,
        "reasoning": "explicação breve e objetiva (máximo 2 frases)"
      }

      NÃO adicione texto antes ou depois do JSON. APENAS o JSON."""

  def _build_user_prompt(self, email_content: str) -> str:
    """
    Constrói o prompt do usuário com o email a ser classificado.
    
    Args:
        email_content: Conteúdo do email
        
    Returns:
        Prompt formatado
    """
    return f"""Analise e classifique este email:
            
            ---
            {email_content.strip()}
            ---
            
            Classifique como produtivo ou improdutivo e retorne o JSON."""

  def _parse_response(self, response: str) -> Dict[str, Any]:
    """
    Faz parse da resposta da IA e valida o formato.
    
    Args:
        response: Resposta bruta da IA
        
    Returns:
        Dicionário com classificação parseada
        
    Raises:
        ValueError: Se resposta não for JSON válido
    """

    try:
      response_clean = self._extract_json(response)

      result = json.loads(response_clean)

      self._validate_classification(result)

      return result
    
    except json.JSONDecodeError as e:
      raise ValueError(f"Resposta da IA não é um JSON válido: {response}") from e
    
  def _extract_json(self, text: str) -> str:
    """
    Extrai JSON de uma string que pode conter texto adicional.
    
    Args:
        text: Texto que contém JSON
        
    Returns:
        String JSON limpa
    """
    
    # Tenta encontrar JSON entre chaves usando regex
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()
  
  def _validate_classification(self, result: Dict[str, Any]) -> None:
    """
    Valida se o resultado da classificação tem os campos corretos.
    
    Args:
        result: Dicionário com resultado
        
    Raises:
        ValueError: Se campos obrigatórios estiverem faltando ou inválidos
    """
    
    required_fields = ["classification", "confidence", "reasoning"]
    
    # Verifica campos obrigatórios
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Campo obrigatório '{field}' ausente na resposta")
    
    # Valida classificação
    if result["classification"] not in ["produtivo", "improdutivo"]:
        raise ValueError(f"Classificação inválida: {result['classification']}")
    
    # Valida confiança
    confidence = result["confidence"]
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        raise ValueError(f"Confiança deve ser entre 0 e 1, recebeu: {confidence}")
    
    # Valida reasoning
    if not isinstance(result["reasoning"], str) or not result["reasoning"].strip():
        raise ValueError("Reasoning deve ser uma string não vazia")