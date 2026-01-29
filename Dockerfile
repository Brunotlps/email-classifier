

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependências de sistema para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  && rm -rf /var/lib/apt/lists/*

# Cria um virtualenv em /opt/venv
RUN python -m venv /opt/venv

# Ativa o virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# 5. Copiar requirements.txt
COPY requirements.txt .

# 6. Instalar dependências Python no virtualenv
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copia APENAS o virtualenv do stage builder
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Copia o código da aplicação
COPY ./app ./app

# Cria usuário não-root
RUN useradd -m -u 1000 appuser

# Muda ownership das pastas
RUN chown -R appuser:appuser /app /opt/venv

# Troca para usuário não-root
USER appuser

EXPOSE 8000

# Usa shell form para interpretar a variável $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]