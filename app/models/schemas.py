from pydantic import BaseModel, Field
from typing import List, Literal


# --- Shared ---

class ResponseSuggestion(BaseModel):
    """Sugestão de resposta gerada pela IA"""
    title: str = Field(..., description="Título/tema da resposta")
    content: str = Field(..., description="Conteúdo sugerido da resposta")
    tone: Literal["formal", "cordial", "casual", "técnico"] = Field(..., description="Tom da resposta")


# --- /analyze ---

EMAIL_CATEGORIES = Literal[
    "Proposta Comercial",
    "Reunião / Agenda",
    "Suporte Técnico",
    "Cobrança / Pagamento",
    "Newsletter / Marketing",
    "Feedback / Avaliação",
    "Pessoal / Casual",
    "Alerta / Notificação",
    "Candidatura / RH",
    "Outro",
]

CATEGORIES_LIST = [
    "Proposta Comercial",
    "Reunião / Agenda",
    "Suporte Técnico",
    "Cobrança / Pagamento",
    "Newsletter / Marketing",
    "Feedback / Avaliação",
    "Pessoal / Casual",
    "Alerta / Notificação",
    "Candidatura / RH",
    "Outro",
]

EMAIL_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "category": {"type": "string", "enum": CATEGORIES_LIST},
        "priority": {"type": "string", "enum": ["alta", "normal", "baixa"]},
        "action_required": {"type": "boolean"},
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "tone": {"type": "string", "enum": ["formal", "cordial", "casual", "técnico"]},
                },
                "required": ["title", "content", "tone"],
            },
        },
    },
    "required": ["summary", "category", "priority", "action_required", "suggestions"],
}


class EmailAnalyzeRequest(BaseModel):
    """Request para análise completa de email"""
    email_content: str = Field(
        ...,
        min_length=10,
        description="Conteúdo do email a ser analisado",
    )
    language: Literal["pt", "en"] = Field(
        default="pt",
        description="Idioma da resposta gerada pela IA (pt = português, en = inglês)",
    )


class EmailAnalysisResponse(BaseModel):
    """Response da análise completa"""
    summary: str = Field(..., description="Resumo em 1-2 frases do que o email trata e qual ação é esperada")
    category: EMAIL_CATEGORIES = Field(..., description="Categoria do email")
    priority: Literal["alta", "normal", "baixa"] = Field(..., description="Prioridade estimada")
    action_required: bool = Field(..., description="Se o email requer uma ação ou resposta")
    suggestions: List[ResponseSuggestion] = Field(default_factory=list, description="Sugestões de resposta contextuais")


# --- Shared health ---

class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "unhealthy"] = Field(default="healthy")
    version: str = Field(default="1.0.0")
