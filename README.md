# 📧 Email Classifier API

Classificador de emails usando IA (Ollama/OpenAI) que determina se um email é produtivo ou improdutivo e gera sugestões de resposta.

## 🚀 Tecnologias

- **Backend**: FastAPI + Python 3.11
- **IA**: Ollama (desenvolvimento) / OpenAI (produção)
- **Containerização**: Docker + Docker Compose
- **Validação**: Pydantic

## 📋 Pré-requisitos

- Docker e Docker Compose
- Ollama (para desenvolvimento local)
- Python 3.11+ (para testes locais)

## ⚙️ Configuração do Ollama (Linux)

**IMPORTANTE**: Por padrão, o Ollama escuta apenas em `localhost`. Para funcionar com Docker, precisa aceitar conexões externas:

```bash
# 1. Criar/editar arquivo de configuração do systemd
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo nano /etc/systemd/system/ollama.service.d/override.conf

# 2. Adicionar estas linhas:
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"

# 3. Recarregar e reiniciar
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 4. Verificar se está escutando em todas as interfaces
sudo systemctl status ollama | grep Listening
# Deve mostrar: "Listening on [::]:11434"

# 5. Testar conectividade
curl http://localhost:11434/api/version
curl http://172.21.0.1:11434/api/version  # IP do gateway Docker
```

## 🐳 Instalação e Execução

### 1. Instalar Ollama

```bash
# Instalar
curl -fsSL https://ollama.com/install.sh | sh

# Baixar modelo
ollama pull qwen2.5:3b

# Configurar para aceitar conexões externas (ver seção acima)
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
ENVIRONMENT=development
AI_PROVIDER=ollama

# OpenAI (opcional, para produção)
OPENAI_API_KEY=sua-chave-aqui
OPENAI_MODEL=gpt-3.5-turbo

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# Configurações de IA
MAX_TOKENS=500
TEMPERATURE=0.7
```

### 3. Subir a aplicação

```bash
# Subir container
docker-compose up --build

# Ou em background
docker-compose up -d
```

### 4. Acessar

- **API**: http://localhost:8001
- **Documentação**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Teste de IA**: http://localhost:8001/test-ai

## 🧪 Testes

### Teste local (fora do Docker)

```bash
# Ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar teste
python test_ai.py
```

### Teste no container

```bash
# Verificar URL configurada
docker exec email_classifier_api python -c "from app.config import settings; print(settings.ollama_base_url)"

# Testar conectividade Ollama
docker exec email_classifier_api python -c "import httpx; print(httpx.get('http://172.21.0.1:11434/api/version', timeout=5.0).json())"

# Testar endpoint
curl http://localhost:8001/test-ai
```

## 📁 Estrutura do Projeto

```
email-classifier/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configurações
│   ├── api/
│   │   └── routes.py        # Endpoints
│   ├── services/
│   │   ├── classifier.py    # Lógica de classificação
│   │   └── response_generator.py
│   ├── models/
│   │   └── schemas.py       # Modelos Pydantic
│   └── utils/
│       └── ai_client.py     # Cliente de IA (Ollama/OpenAI)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── test_ai.py
└── README.md
```

## 🔧 Troubleshooting

### Container não conecta ao Ollama

**Erro**: `[Errno -2] Name or service not known`

**Solução**: Verifique se o Ollama está configurado para aceitar conexões externas (ver seção "Configuração do Ollama")

```bash
# Verificar se está escutando em todas as interfaces
sudo systemctl status ollama | grep Listening
```

### Porta 8001 já em uso

```bash
# Ver o que está usando a porta
sudo lsof -i :8001

# Matar processo (substitua PID)
kill -9 <PID>
```

### Hot-reload não funciona

Verifique se os volumes estão corretos no `docker-compose.yml`:

```yaml
volumes:
  - ./app:/app/app  # Sincroniza pasta local com container
```

## 🚀 Próximos Passos

- [ ] Implementar serviço de classificação
- [ ] Criar endpoint `/classify`
- [ ] Adicionar geração de sugestões de resposta
- [ ] Criar frontend
- [ ] Adicionar testes unitários
- [ ] Deploy em produção

## 📝 Licença

Projeto desenvolvido para processo seletivo de estágio em Engenharia de Software.