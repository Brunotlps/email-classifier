import pytest
import os
from pathlib import Path


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


@pytest.fixture
def fixtures_dir():
  """Retorna o diretório de fixtures de teste."""
  
  return Path(__file__).parent / "fixtures"