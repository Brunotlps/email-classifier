FROM python:3.11-slim

WORKDIR /app

# Copia dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY ./app ./app
COPY ./tests ./tests
COPY pytest.ini .
COPY test_ai.py .

# Railway define a porta via variável $PORT
# Não usamos EXPOSE fixo aqui
EXPOSE 8000

# Comando que aceita porta variável
# ${PORT:-8000} significa: use $PORT se existir, senão use 8000 (para rodar local)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}