from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):

  environment: str = "development" 

  ai_provider: Literal["openai", "ollama"] = "ollama"

  # Modelo para prod
  openai_api_key: str = ""
  openai_model: str = "gpt-3.5-turbo"

  # Modelo para dev
  ollama_base_url: str =  "http://localhost:11434"
  ollama_model: str = "qwen2.5:3b"

  max_tokens: int = 500
  temperature: float = 0.7

  class Config:
    
    env_file = ".env"
    case_sensitive = False 

settings = Settings()
