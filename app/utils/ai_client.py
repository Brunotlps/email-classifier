"""
Cliente unificado para trabalhar com diferentes provedores de IA
Suporta: OpenAI e Ollama
"""
import httpx
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.config import settings


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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            except httpx.HTTPError as e:
                raise Exception(f"Erro ao chamar Ollama: {str(e)}")


class OpenAIClient(AIClient):
    """Cliente para OpenAI API"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Gera resposta usando OpenAI
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Instruções do sistema
            
        Returns:
            Resposta do modelo
        """
        if not self.api_key or self.api_key == "sua-chave-aqui":
            raise Exception("OpenAI API key não configurada. Configure OPENAI_API_KEY no .env")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                raise Exception(f"Erro ao chamar OpenAI: {str(e)}")


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