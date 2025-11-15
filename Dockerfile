FROM python:3.11-slim

WORKDIR /app

# Copia dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY ./app ./app

# Railway define a porta via variável $PORT
EXPOSE 8000

# Usa shell form para interpretar a variável $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]