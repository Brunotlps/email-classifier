# 📧 Email Classifier

Classificador inteligente de emails utilizando IA (LLMs) para identificar emails produtivos/improdutivos e gerar sugestões de resposta.

## 🚀 Tecnologias

- **Backend**: FastAPI + Python 3.11
- **IA**: Ollama (desenvolvimento) / OpenAI (produção)
- **Containerização**: Docker + Docker Compose
- **Arquitetura**: Camadas (API → Services → Utils)

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.11+
- Ollama (para desenvolvimento local) ou OpenAI API Key

## 🔧 Configuração

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd email-classifier
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

3. Inicie o container:
```bash
docker-compose up --build
```

4. Acesse a documentação da API:
```
http://localhost:8001/docs
```

## 📁 Estrutura do Projeto

```
email-classifier/
├── app/
│   ├── main.py              # Aplicação FastAPI
│   ├── config.py            # Configurações
│   ├── api/                 # Endpoints REST
│   ├── services/            # Lógica de negócio
│   ├── models/              # Schemas Pydantic
│   └── utils/               # Utilitários
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🎯 Funcionalidades

- [ ] Classificação de emails (produtivo/improdutivo)
- [ ] Geração de respostas sugeridas
- [ ] Suporte multi-provider (Ollama/OpenAI)
- [ ] API REST documentada

## 📝 Licença

Este projeto foi desenvolvido para fins educacionais.

---

Desenvolvido por Bruno Teixeira
