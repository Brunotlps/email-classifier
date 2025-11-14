from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


app = FastAPI(
  title="Email Classifier API",
  description="Classificador de emails como produtivos/improdutivos e gera sugestões de respostas",
  version="1.0.0",
  docs_url="/docs", # Swagger
  redoc_url="/redoc" # ReDoc
)

# Configurações do CORS
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"], # especificar domínios em prod
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

