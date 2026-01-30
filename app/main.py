import structlog, time, logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# Configurações de structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)


# Logger global
logger = structlog.get_logger()


# Configuração do rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
  title="Email Classifier API",
  description="Classificador de emails como produtivos/improdutivos e gera sugestões de respostas",
  version="1.0.0",
  docs_url="/docs", # Swagger
  redoc_url="/redoc" # ReDoc
)

# Registrar handler de erro para rate limit
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Captura o IP do cliente
    client_ip = request.client.host if request.client else "unknown"
    
    # Processa a request
    response = await call_next(request)
    
    # Calcula o tempo de resposta em ms
    process_time_ms = (time.time() - start_time) * 1000
    
    # Loga as informações da request
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time_ms=round(process_time_ms, 2),
        client_ip=client_ip
    )
    
    return response


# Configurações do CORS
# Em produção, allowed_origins virá das variáveis de ambiente
allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=allowed_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/")
async def root():
  return {
    "message": "API inicial rodando!",
    "environment": settings.environment,
    "ai_provider": settings.ai_provider,
    "docs": "/docs"
  }

@app.get("/health")
async def health():
  return {"status": "healthy"}

from app.api.routes import router as classification_router
app.include_router(classification_router)

@app.get("/test-ai")
async def test_ai():
    """Endpoint para testar conexão com IA"""
    from app.utils.ai_client import get_ai_client
    
    try:
        client = get_ai_client()
        response = await client.generate(
            prompt="Me diga olá em uma frase curta",
            system_prompt="Você é um assistente útil"
        )
        return {
            "status": "success",
            "provider": settings.ai_provider,
            "model": settings.ollama_model if settings.ai_provider == "ollama" else settings.openai_model,
            "response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

