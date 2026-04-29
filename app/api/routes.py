import structlog

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request
from app.models.schemas import (
    EmailClassifyRequest, EmailClassifyResponse,
    EmailAnalyzeRequest, EmailAnalysisResponse,
    ResponseSuggestion,
)
from app.services.classifier import EmailClassifier
from app.services.response_generator import ResponseGenerator
from app.services.analyzer import EmailAnalyzer
from app.utils.file_parser import FileParser

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["Classification"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Instanciando os serviços (usar injeção de dependência futuramente)
classifier = EmailClassifier()
response_generator = ResponseGenerator()
analyzer = EmailAnalyzer()

# Criação das rotas

@limiter.limit("10/minute")
@router.post(
    "/classify",
    response_model=EmailClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Classifica um email",
    description="""
        Classifica um email como produtivo ou improdutivo usando IA.
        
        Se o email for classificado como **produtivo**, também retorna sugestões de resposta.
        
        **Produtivo**: Emails que requerem ação, oportunidades de negócio, solicitações legítimas.
        
        **Improdutivo**: Spam, marketing não solicitado, emails sem valor."""
)
async def classify_email(request: Request, email_request: EmailClassifyRequest):
    """
    Endpoint principal de classificação de emails.
    
    Args:
            request: EmailClassifyRequest com o conteúdo do email
            
    Returns:
            EmailClassifyResponse com classificação e sugestões (se aplicável)
            
    Raises:
            HTTPException 400: Se email inválido
            HTTPException 500: Se erro na IA
    """

    try:
        classification_result = await classifier.classify(email_request.email_content)
        suggestions = []

        if classification_result["classification"] == "produtivo":
            try:
                suggestions = await response_generator.generate_suggestions(email_content=email_request.email_content, num_suggestions=2)
            
            except Exception as e:
                # Não será necessário parar as requisições em caso de falha ao gerar sugestões de respostas
                logger.warning("suggestion_generation_failed", error=str(e))
                suggestions = []

        response = EmailClassifyResponse(
            classification=classification_result["classification"],
            confidence=classification_result["confidence"],
            reasoning=classification_result["reasoning"],
            suggestions=suggestions
        )

        return response
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao tentar processar email: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao tentar classificar email: {str(e)}"
        )
    
@limiter.limit("10/minute")
@router.post(
    "/analyze",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_200_OK,
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

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/health",
    summary="Health check da API de classificação",
    tags=["health"]
)
async def classification_health():
    """
    Verifica se o serviço de classificação está operacional.
    """
    return {
            "status": "healthy",
            "service": "email-classification",
            "classifier": "operational",
            "response_generator": "operational"
    }

@router.post(
    "/classify-file",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_200_OK,
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))