from pydantic import BaseModel, Field
from typing import List, Literal


class EmailClassifyRequest(BaseModel):
    """Request para classificar email"""
    email_content: str = Field(
        ..., 
        min_length=10,
        description="Conteúdo do email a ser classificado",
        examples=["Olá, gostaria de saber sobre os serviços da empresa..."]
    )


class ResponseSuggestion(BaseModel):
    """Sugestão de resposta para email produtivo"""
    title: str = Field(..., description="Título/tema da resposta")
    content: str = Field(..., description="Conteúdo sugerido da resposta")
    tone: Literal["formal", "cordial", "casual", "técnico"] = Field(..., description="Tom da resposta")


class EmailClassifyResponse(BaseModel):
    """Response da classificação"""
    classification: Literal["produtivo", "improdutivo"] = Field(
        ..., 
        description="Classificação do email"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confiança da classificação (0-1)"
    )
    reasoning: str = Field(
        ..., 
        description="Explicação da classificação"
    )
    suggestions: List[ResponseSuggestion] = Field(
        default_factory=list,
        description="Sugestões de resposta (apenas para emails produtivos)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "classification": "produtivo",
                "confidence": 0.92,
                "reasoning": "Email solicita informações sobre serviços, demonstra interesse comercial",
                "suggestions": [
                    {
                        "title": "Resposta cordial e informativa",
                        "content": "Olá! Ficamos felizes com seu interesse...",
                        "tone": "cordial"
                    }
                ]
            }
        }

class HealthCheckResponse(BaseModel):
    
    status: Literal["healthy", "unhealthy"] = Field(default="healthy", description="Status da API")
    version: str = Field(default="1.0.0", description="Versão da API")