from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request
from app.models.schemas import EmailClassifyRequest, EmailClassifyResponse
from app.services.classifier import EmailClassifier
from app.services.response_generator import ResponseGenerator
from app.utils.file_parser import FileParser

from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/v1", tags=["Classification"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Instanciando os serviços (usar injeção de dependência futuramente)
classifier = EmailClassifier()
response_generator = ResponseGenerator()

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
        print(f"Erro ao gerar sugestões: {e}")
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
  response_model=EmailClassifyResponse,
  status_code=status.HTTP_200_OK,
  summary="Classifica email a partir de arquivo",
  description="""
    Classifica um email enviado como arquivo (.txt, .eml ou .pdf).
    
    Formatos suportados:
    - **.txt**: Arquivo de texto simples
    - **.eml**: Formato padrão de email (exportado de clientes de email)
    - **.pdf**: Arquivo PDF contendo texto
    
    Tamanho máximo: 5MB
    
    Retorna a mesma estrutura do endpoint /classify.
    """
)
async def classify_email_from_file(file: UploadFile = File(..., description="Arquivo contendo o email (.txt, .eml ou .pdf)")):
  """
  Endpoint para classificação de email a partir de arquivo.
  
  Args:
      file: Arquivo enviado via upload
      
  Returns:
      EmailClassifyResponse com classificação e sugestões
      
  Raises:
      HTTPException 400: Se arquivo inválido ou formato não suportado
      HTTPException 500: Se erro na IA
  """

  try:
    # 1. Lê conteúdo do arquivo
    content = await file.read()
    
    # 2. Parse baseado no formato
    try:
      email_content = FileParser.parse(file.filename, content)
    except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
    
    # 3. Classifica o email (mesma lógica do /classify)
    classification_result = await classifier.classify(email_content)
    
    # 4. Gera sugestões se produtivo
    suggestions = []
    if classification_result["classification"] == "produtivo":
      try:
        suggestions = await response_generator.generate_suggestions(
          email_content=email_content,
          num_suggestions=2
        )
      except Exception as e:
        print(f"⚠️  Erro ao gerar sugestões: {e}")
        suggestions = []

    response = EmailClassifyResponse(
      classification=classification_result["classification"],
      confidence=classification_result["confidence"],
      reasoning=classification_result["reasoning"],
      suggestions=suggestions
    )
    
    return response
      
  except HTTPException:
    # Re-raise HTTPException para não capturar no except genérico
    raise
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Erro ao processar arquivo: {str(e)}"
    )
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro interno ao classificar email: {str(e)}"
    )