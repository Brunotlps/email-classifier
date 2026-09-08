from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request
from app.models.schemas import (
    EmailAnalyzeRequest, EmailAnalysisResponse,
    ResponseSuggestion,
)
from app.services.analyzer import EmailAnalyzer
from app.utils.file_parser import FileParser
from app.exceptions import InvalidAIResponseError

from slowapi import Limiter
from slowapi.util import get_remote_address

INVALID_AI_RESPONSE_DETAIL = "O serviço de IA retornou uma resposta inválida. Tente novamente."
INVALID_AI_RESPONSE_RESPONSES = {
    status.HTTP_502_BAD_GATEWAY: {
        "description": "O provedor de IA retornou uma resposta que não pôde ser validada."
    }
}

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Instanciando o serviço (usar injeção de dependência futuramente)
analyzer = EmailAnalyzer()

# Criação das rotas

@limiter.limit("10/minute")
@router.post(
    "/analyze",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses=INVALID_AI_RESPONSE_RESPONSES,
    summary="Analisa um email",
    description="""
        Analisa um email e retorna um resumo, categoria, prioridade e sugestões de resposta contextuais.

        Em vez da classificação binária produtivo/improdutivo, este endpoint fornece uma análise
        completa e acionável do email em uma única chamada à IA.

        Suporta emails em **português (PT-BR)** e **inglês**."""
)
async def analyze_email(request: Request, email_request: EmailAnalyzeRequest):
    try:
        result = await analyzer.analyze(email_request.email_content, email_request.language)

        suggestions = [
            ResponseSuggestion(
                title=s.get("title", ""),
                content=s.get("content", ""),
                tone=s.get("tone", "cordial"),
            )
            for s in result.get("suggestions", [])
            if s.get("content", "").strip()
        ]

        return EmailAnalysisResponse(
            summary=result["summary"],
            category=result["category"],
            priority=result["priority"],
            action_required=result["action_required"],
            suggestions=suggestions,
        )

    except InvalidAIResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=INVALID_AI_RESPONSE_DETAIL,
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/health",
    summary="Health check da API de análise",
    tags=["health"]
)
async def analysis_health():
    """
    Verifica se o serviço de análise está operacional.
    """
    return {
        "status": "healthy",
        "service": "email-analysis",
        "analyzer": "operational",
    }


@router.post(
    "/classify-file",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses=INVALID_AI_RESPONSE_RESPONSES,
    summary="Analisa email a partir de arquivo",
    description="""
        Analisa um email enviado como arquivo (.txt, .eml ou .pdf).

        Formatos suportados: **.txt**, **.eml**, **.pdf** — tamanho máximo 5MB.

        Retorna a mesma estrutura do endpoint /analyze."""
)
async def classify_email_from_file(file: UploadFile = File(..., description="Arquivo contendo o email (.txt, .eml ou .pdf)")):
    try:
        content = await file.read()

        try:
            email_content = FileParser.parse(file.filename, content)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        result = await analyzer.analyze(email_content)

        suggestions = [
            ResponseSuggestion(
                title=s.get("title", ""),
                content=s.get("content", ""),
                tone=s.get("tone", "cordial"),
            )
            for s in result.get("suggestions", [])
            if s.get("content", "").strip()
        ]

        return EmailAnalysisResponse(
            summary=result["summary"],
            category=result["category"],
            priority=result["priority"],
            action_required=result["action_required"],
            suggestions=suggestions,
        )

    except HTTPException:
        raise
    except InvalidAIResponseError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=INVALID_AI_RESPONSE_DETAIL,
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
