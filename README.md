# 📧 Email Classifier API

[![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen)](https://github.com/Brunotlps/email-classifier)
[![Coverage](https://img.shields.io/badge/coverage-79%25-yellowgreen)](https://github.com/Brunotlps/email-classifier)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688)](https://fastapi.tiangolo.com/)

Classificador inteligente de emails usando IA (Ollama/OpenAI) que identifica emails produtivos/improdutivos e gera sugestões de resposta contextualmente relevantes.

---

## 🎯 Funcionalidades

- ✅ Classificação automática de emails (produtivo vs improdutivo)
- ✅ Geração de sugestões de resposta com múltiplos tons (formal, cordial, casual, técnico)
- ✅ Suporte para Ollama (dev) e OpenAI (prod)
- ✅ Upload de arquivos (.txt, .eml, .pdf)
- ✅ API REST totalmente documentada (Swagger)
- ✅ 44 testes automatizados com 79% de cobertura

---

## 🚀 Tecnologias

**Backend**: FastAPI 0.115.0 + Python 3.11  
**IA**: Ollama (qwen2.5:3b) / OpenAI (gpt-3.5-turbo)  
**Testes**: pytest + pytest-asyncio (44 testes, 79% coverage)  
**Deploy**: Docker + Docker Compose

---

## 🏗️ Decisões de Arquitetura

### Por que FastAPI?
- **Performance**: Async nativo ideal para chamadas de IA (I/O-bound)
- **Documentação automática**: Swagger gerado automaticamente
- **Validação**: Pydantic integrado reduz bugs

### Por que Ollama + OpenAI?
- **Ollama**: Desenvolvimento local sem custos, privado
- **OpenAI**: Produção com qualidade superior
- **Abstração**: Factory pattern permite trocar facilmente

### Arquitetura em Camadas
```
API Layer (routes.py)
    ↓
Service Layer (classifier, response_generator)
    ↓
Utils Layer (ai_client, file_parser)
```

**Benefícios**: Testabilidade, manutenibilidade, baixo acoplamento

## 📦 Instalação Rápida

### Pré-requisitos

- Docker e Docker Compose
- Ollama instalado e configurado

### 1. Instalar Ollama

```bash
# Instalar
curl -fsSL https://ollama.com/install.sh | sh

# Baixar modelo
ollama pull qwen2.5:3b

# Configurar para aceitar conexões externas (IMPORTANTE!)
sudo systemctl edit ollama
```

Adicione no editor:
```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Salve e reinicie:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 2. Clonar e Configurar

```bash
git clone https://github.com/Brunotlps/email-classifier.git
cd email-classifier

# Criar .env (use .env.example como base)
cp .env.example .env
```

### 3. Executar

```bash
# Subir aplicação
docker-compose up -d

# Verificar logs
docker-compose logs -f
```

**Acesse**: http://localhost:8001/docs

---

## 📚 Uso da API

### Classificar Email

```bash
curl -X POST http://localhost:8001/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "email_content": "Olá, gostaria de agendar uma reunião para discutir parceria."
  }'
```

**Resposta:**
```json
{
  "classification": "produtivo",
  "confidence": 0.92,
  "reasoning": "Email solicita reunião, demonstra interesse comercial",
  "suggestions": [
    {
      "title": "Resposta cordial",
      "content": "Olá! Agradeço o contato. Podemos agendar para...",
      "tone": "cordial"
    }
  ]
}
```

### Upload de Arquivo

```bash
curl -X POST http://localhost:8001/api/v1/classify-file \
  -F "file=@email.txt"
```

---

## 🧪 Testes

```bash
# Rodar testes
docker exec -it email_classifier_api pytest tests/ -v

# Com cobertura
docker exec -it email_classifier_api pytest tests/ --cov=app --cov-report=term
```

**Resultado**: 44 testes passando, 79% de cobertura ✅

---

## 📁 Estrutura

```
email-classifier/
├── app/
│   ├── api/routes.py              # Endpoints REST
│   ├── services/
│   │   ├── classifier.py          # Lógica de classificação
│   │   └── response_generator.py  # Geração de sugestões
│   ├── models/schemas.py          # Validação Pydantic
│   ├── utils/
│   │   ├── ai_client.py           # Cliente Ollama/OpenAI
│   │   └── file_parser.py         # Parser multi-formato
│   ├── config.py                  # Configurações
│   └── main.py                    # FastAPI app
├── tests/                         # 44 testes automatizados
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🔧 Troubleshooting

### Erro de Conexão com Ollama

```
Connection refused
```

**Solução**: Verifique se o Ollama está configurado para aceitar conexões externas (ver passo 1 da instalação).

```bash
# Verificar
sudo systemctl status ollama | grep Listening
# Deve mostrar: [::]:11434 ou 0.0.0.0:11434
```

### Porta 8001 em Uso

```bash
# Verificar processo
sudo lsof -i :8001

# Ou alterar porta no docker-compose.yml
ports:
  - "8002:8000"
```

---

## 📊 Cobertura de Testes

| Componente | Cobertura |
|------------|-----------|
| Schemas | 100% ✅ |
| Classifier | 98% ✅ |
| Response Generator | 98% ✅ |
| Main | 86% ✅ |
| Config | 85% ✅ |
| **Total** | **79%** ✅ |

---

## 🎯 Próximos Passos

1. ✅ **Backend completo** com testes
2. 🔄 **Frontend** básico em desenvolvimento
3. 📦 **Deploy** planejado (Vercel/Railway)

---

## 👤 Autor

**Bruno Teixeira**  
[![GitHub](https://img.shields.io/badge/GitHub-Brunotlps-181717?logo=github)](https://github.com/Brunotlps)

---

## 📝 Licença

Projeto educacional desenvolvido para processo seletivo de estágio em Engenharia de Software.

---

**Desenvolvido utilizando FastAPI + Ollama**