"""
Configurações da aplicação usando Pydantic Settings.
Lê automaticamente do arquivo .env
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente"""
    
    # Configurações gerais
    environment: str = "development"
    
    # CORS - domínios permitidos (separados por vírgula)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Provider de IA
    ai_provider: Literal["openai", "ollama"] = "ollama"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    
    # Configurações de geração
    max_tokens: int = 500
    temperature: float = 0.7
    
    class Config:
        # Nome do arquivo de variáveis de ambiente
        env_file = ".env"
        # Case insensitive (OPENAI_API_KEY = openai_api_key)
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detecta se está rodando em Docker
        self._adjust_ollama_url()
    
    def _adjust_ollama_url(self):
        """Ajusta URL do Ollama baseado no ambiente"""
        # Verifica se está rodando em container Docker
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER', False)
        
        if is_docker and 'localhost' in self.ollama_base_url:
            # Dentro do Docker, troca localhost por host.docker.internal
            self.ollama_base_url = self.ollama_base_url.replace('localhost', 'host.docker.internal')
            print(f"🐳 Docker detectado! URL do Ollama ajustada para: {self.ollama_base_url}")
        elif not is_docker and 'host.docker.internal' in self.ollama_base_url:
            # Fora do Docker, troca host.docker.internal por localhost
            self.ollama_base_url = self.ollama_base_url.replace('host.docker.internal', 'localhost')
            print(f"💻 Ambiente local detectado! URL do Ollama ajustada para: {self.ollama_base_url}")


# Instância global das configurações
settings = Settings()