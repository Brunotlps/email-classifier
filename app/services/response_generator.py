import json
import re
from typing import List, Dict, Any
from app.utils.ai_client import get_ai_client
from app.models.schemas import ResponseSuggestion


class ResponseGenerator:
  """
  Gera sugestões de resposta para emails classificados como produtivos.
  """
  
  def __init__(self):
    self.ai_client = get_ai_client()
  
  async def generate_suggestions(self, email_content: str, num_suggestions: int = 2) -> List[ResponseSuggestion]:
    """
    Gera sugestões de resposta para um email.
    
    Args:
        email_content: Conteúdo do email original
        num_suggestions: Número de sugestões a gerar (padrão: 2)
        
    Returns:
        Lista de ResponseSuggestion
        
    Raises:
        Exception: Se houver erro na geração
    """
    system_prompt = self._build_system_prompt(num_suggestions)
    user_prompt = self._build_user_prompt(email_content)
    
    # Chamar IA
    response = await self.ai_client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    # Parse e criação dos objetos
    suggestions = self._parse_suggestions(response)
    
    return suggestions
  
  def _build_system_prompt(self, num_suggestions: int) -> str:
    """
    Constrói prompt para geração de sugestões de resposta.
    
    Args:
        num_suggestions: Número de sugestões a gerar
    """
    return f"""Você é um assistente especializado em redigir respostas profissionais para emails.
            Sua tarefa é gerar {num_suggestions} sugestões de resposta para o email fornecido.
            Para CADA sugestão, considere:
            - Tom apropriado (formal, cordial, casual, técnico)
            - Contexto do email original
            - Clareza e objetividade
            - Profissionalismo
            IMPORTANTE: Responda APENAS com JSON válido no formato:
            {{
              "suggestions": [
                {{
                  "title": "título curto da resposta",
                  "content": "conteúdo completo da resposta sugerida",
                  "tone": "formal" | "cordial" | "casual" | "técnico"
                }}
              ]
            }}
            NÃO adicione texto antes ou depois do JSON. APENAS o JSON."""
  
  def _build_user_prompt(self, email_content: str) -> str:
    """
    Constrói prompt com o email a ser respondido.
    
    Args:
        email_content: Conteúdo do email
    """
    
    return f"""Gere sugestões de resposta profissional para este email:
            ---
            {email_content.strip()}
            ---
            Gere as sugestões em JSON."""
  
  def _parse_suggestions(self, response: str) -> List[ResponseSuggestion]:
    """
    Faz parse da resposta da IA e cria objetos ResponseSuggestion.
    
    Args:
        response: Resposta bruta da IA
        
    Returns:
        Lista de ResponseSuggestion
        
    Raises:
        ValueError: Se resposta não for válida
    """
    
    try:
        
        response_clean = self._extract_json(response)
        result = json.loads(response_clean)
        
        # Valida estrutura
        if "suggestions" not in result:
            raise ValueError("Campo 'suggestions' não encontrado na resposta")
        
        # Cria objetos ResponseSuggestion
        suggestions = []
        for item in result["suggestions"]:

            self._validate_suggestion(item)
            
            # Normaliza o tom
            tone = self._normalize_tone(item["tone"])
            
            suggestion = ResponseSuggestion(
                title=item["title"],
                content=item["content"],
                tone=tone
            )
            suggestions.append(suggestion)
        
        return suggestions
          
    except json.JSONDecodeError as e:
        raise ValueError(f"Resposta da IA não é JSON válido: {response}") from e
    except Exception as e:
        raise ValueError(f"Erro ao processar sugestões: {str(e)}") from e
  
  def _extract_json(self, text: str) -> str:
    """
    Extrai JSON de uma string que pode conter texto adicional.
    """
    
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()
  
  def _validate_suggestion(self, suggestion: Dict[str, Any]) -> None:
    """
    Valida estrutura de uma sugestão.
    
    Args:
        suggestion: Dicionário com sugestão
        
    Raises:
        ValueError: Se campos obrigatórios estiverem faltando
    """
    required_fields = ["title", "content", "tone"]
    for field in required_fields:
        if field not in suggestion:
            raise ValueError(f"Campo '{field}' ausente na sugestão")
        if not isinstance(suggestion[field], str) or not suggestion[field].strip():
            raise ValueError(f"Campo '{field}' deve ser string não vazia")
  
  def _normalize_tone(self, tone: str) -> str:
    """
    Normaliza o tom para um dos valores aceitos.
    
    Args:
        tone: Tom original da IA
        
    Returns:
        Tom normalizado
    """
    tone_lower = tone.lower().strip()
    
    # Mapeamento de variações
    tone_mapping = {
        "formal": "formal",
        "cordial": "cordial",
        "casual": "casual",
        "técnico": "técnico",
        "tecnico": "técnico",
        "amigável": "cordial",
        "amigavel": "cordial",
        "profissional": "formal",
    }
    
    normalized = tone_mapping.get(tone_lower, "cordial")
    return normalized