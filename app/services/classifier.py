import json, re, hashlib, structlog

from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache
from typing import Dict, Any
from app.utils.ai_client import get_ai_client


logger = structlog.get_logger()


class EmailClassifier:
  """
  Classifica emails como produtivos ou improdutivos utilizando modelos de IA
  
  - Produtivo: Emails que requerem uma ação ou resposta específica (ex.: solicitações de suporte técnico, atualização sobre casos em aberto, dúvidas sobre o sistema).
  - Improdutivo: Emails que não necessitam de uma ação imediata (ex.: mensagens de felicitações, agradecimentos).
  
  Funcionalidades:
  - Cache TTL: Armazena classificações por 1 hora (TTLCache com 100 entradas) para evitar classificações duplicadas e reduzir custos.
  - Retry automático: Implementa até 3 tentativas com backoff exponencial em caso de falhas na comunicação com o serviço de IA.
  """


  def __init__(self):
    self.ai_client = get_ai_client()
    self.cache = TTLCache(maxsize=100, ttl=3600)


  def _generate_cache_key(self, email_content: str) -> str:
    """
    Gera uma chave de cache única baseada no conteúdo do email.
    
    Utiliza SHA-256 para criar um hash determinístico do conteúdo,
    garantindo que emails idênticos resultem na mesma chave.
    
    Args:
        email_content: Conteúdo do email a ser hashado
        
    Returns:
        String hexadecimal representando o hash SHA-256 do conteúdo
    """
    return hashlib.sha256(email_content.encode()).hexdigest()
  

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
  async def _classify_with_retry(self, prompt: str, system_prompt: str) -> str:
    """
    Executa a chamada ao cliente de IA com mecanismo de retry automático.
    
    Utiliza tenacity para realizar até 3 tentativas com backoff exponencial
    em caso de falhas temporárias na comunicação com o serviço de IA.
    
    Args:
        prompt: Prompt do usuário contendo o email a ser classificado
        system_prompt: Prompt do sistema com instruções de classificação
        
    Returns:
        Resposta em formato string do modelo de IA
        
    Raises:
        Exception: Se todas as 3 tentativas falharem, propaga a última exceção
    """
    return await self.ai_client.generate(prompt, system_prompt)


  async def classify(self, email_content: str) -> Dict[str, Any]:
    """
    Classifica um email e retorna análise detalhada.
    
    Utiliza cache TTL (1 hora) para evitar classificações duplicadas,
    reduzindo custos e melhorando performance.
    
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

    
    cache_key = self._generate_cache_key(email_content)

    if cache_key in self.cache:
       logger.info("cache_hit", key=cache_key[:8])
       return self.cache[cache_key]

    # Variáveis de prompt engineering
    system_prompt = self._build_system_prompt()
    user_prompt = self._build_user_prompt(email_content)

    # Chamada da IA
    response = await self._classify_with_retry(user_prompt, system_prompt)

    # Parse da resposta JSON
    result = self._parse_response(response)

    self.cache[cache_key] = result
    logger.info("cache_saved", key=cache_key[:8])

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
    
  



"""
Pontos fracos:

Sem retry se IA falhar
Sem cache (pode gerar custos repetidos)
"""