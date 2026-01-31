"""
Cliente unificado para trabalhar com diferentes provedores de IA
Suporta: OpenAI e Ollama
"""
import httpx, json, structlog

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.config import settings
from openai import OpenAI, RateLimitError, AuthenticationError, APIError


logger = structlog.getLogger()

def _mask_api_key(key: str) -> str:

    if not key or len(key) < 10:
        return "***INVALID***"
    return f"{key[:7]}...{key[-4:]}"


class AIClient(ABC):
    """Classe abstrata para clientes de IA"""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Gera resposta a partir de um prompt"""
        pass


class OllamaClient(AIClient):
    """Cliente para Ollama (rodando localmente)"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        
        # Configuração de timeout granular
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=60.0,
                write=5.0,
                pool=5.0
            )
        )
        
        logger.info("ollama_client_initialized",
                    base_url=self.base_url,
                    model=self.model)
    
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Gera resposta usando Ollama
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Instruções do sistema
            
        Returns:
            Resposta do modelo
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,  # Desabilita streaming
            "options": {
                "temperature": settings.temperature,
                "num_predict": settings.max_tokens
            }
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise Exception(f"Erro ao chamar Ollama: {str(e)}")


class OpenAIClient(AIClient):
    """Cliente para OpenAI API"""
    
    def __init__(self):
        
        
        self._validate_api_key() 
        self.client = OpenAI(api_key=settings.openai_api_key)
        logger.info("openai_client_initialized", model=settings.openai_model, key=_mask_api_key(settings.openai_api_key))  
    
        # self.api_key = settings.openai_api_key
        # self.model = settings.openai_model
        # self.base_url = "https://api.openai.com/v1/chat/completions"
    
    
    def _validate_api_key(self):
        """
        Valida a chave da API OpenAI
        
        Verifica se a chave está configurada e se possui o formato correto
        (deve começar com 'sk-'). Registra informações de validação no log.
        
        Raises:
            ValueError: Se a chave não estiver configurada ou for inválida
        """


        if not settings.openai_api_key or settings.openai_api_key == "":
            raise ValueError("OpenAI API key não configurada (env: OPENAI_API_KEY)")    
        if not settings.openai_api_key.startswith("sk-"):
            raise ValueError("OpenAI API key inválida (deve começar com 'sk-')") 

        logger.info("openai_api_key_validated", 
            key_prefix=settings.openai_api_key[:7],  # Mostra só "sk-proj"
            key_length=len(settings.openai_api_key))


    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Gera resposta usando OpenAI
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Instruções do sistema
            
        Returns:
            Resposta do modelo
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            return response.choices[0].message.content
        
        except RateLimitError as e:
            logger.error("openai_rate_limit_exceeded", error=str(e))
            raise ValueError(
                "Rate limit da OpenAI excedido. "
                "Aguarde alguns segundos e tente novamente."
            )
        
        except AuthenticationError as e:
            logger.error("openai_authentication_failed", 
                         key=_mask_api_key(settings.openai_api_key))
            raise ValueError(
                "Autenticação OpenAI falhou. "
                "Verifique se sua API key está correta e ativa."
            )
        
        except APIError as e:
            logger.error("openai_api_error", error=str(e), status_code=e.status_code)
            raise Exception(f"Erro na API da OpenAI: {str(e)}")
        
        except Exception as e:
            logger.error("openai_unexpected_error", error=str(e))
            raise


    


def get_ai_client() -> AIClient:
    """
    Factory function: retorna o cliente correto baseado na configuração
    
    Returns:
        Instância do cliente de IA (Ollama ou OpenAI)
    """
    if settings.ai_provider == "ollama":
        return OllamaClient()
    elif settings.ai_provider == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"Provedor de IA inválido: {settings.ai_provider}")
    
