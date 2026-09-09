import os
import socket

import pytest


# Definido antes da coleta/importação da aplicação; nunca usa credenciais locais.
os.environ.update(
    AI_PROVIDER="ollama",
    OPENAI_API_KEY="",
    OLLAMA_BASE_URL="http://127.0.0.1:1",
    ENVIRONMENT="test",
)


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch):
    """Falha em conexões IP/DNS; preserva sockets Unix usados pelo asyncio."""
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def blocked(*args, **kwargs):
        pytest.fail("External network is disabled in tests; mock the AI/HTTP client")

    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            blocked()
        return original_connect(sock, address)

    def connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            blocked()
        return original_connect_ex(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def sample_produtivo_email():
  
  """Email produtivo de exemplo para testes."""
  return """
  De: joao@empresa.com
  Assunto: Proposta de parceria
  
  Olá,
  
  Gostaria de agendar uma reunião para discutir uma possível parceria.
  Podemos marcar para a próxima semana?
  
  Atenciosamente,
  João Silva
  """


@pytest.fixture
def sample_improdutivo_email():
  
  """Email improdutivo (spam) de exemplo para testes."""
  return """
  🎉 PROMOÇÃO IMPERDÍVEL! 🎉
  
  Clique aqui para ganhar um iPhone 15 GRÁTIS!
  Oferta válida apenas hoje!
  
  👉 www.site-suspeito.com
  """


@pytest.fixture
def sample_txt_file(tmp_path):
  """Cria arquivo .txt temporário para testes."""
  
  file_path = tmp_path / "test_email.txt"
  content = "De: test@example.com\nAssunto: Teste\n\nConteúdo do email de teste"
  file_path.write_text(content)
  return file_path


@pytest.fixture
def sample_empty_file(tmp_path):
  """Cria arquivo vazio para testes de validação."""
  
  file_path = tmp_path / "empty.txt"
  file_path.write_text("")
  return file_path


@pytest.fixture
def sample_large_file(tmp_path):
  """Cria arquivo grande (>5MB) para testes de validação."""
  
  file_path = tmp_path / "large.txt"
  # Cria arquivo de ~6MB
  large_content = "A" * (6 * 1024 * 1024)
  file_path.write_text(large_content)
  return file_path
