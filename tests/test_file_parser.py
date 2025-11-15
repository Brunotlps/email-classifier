import pytest
from app.utils.file_parser import FileParser


class TestFileParser:
  """Testes da classe FileParser"""
  
  def test_parse_txt_file_success(self, sample_txt_file):
    """Testa parse de arquivo .txt válido"""
    
    content = sample_txt_file.read_bytes()
    result = FileParser.parse(str(sample_txt_file), content)
    
    assert isinstance(result, str)
    assert len(result) > 0
    assert "test@example.com" in result
  
  def test_parse_empty_file_raises_error(self, sample_empty_file):
    """Testa que arquivo vazio levanta erro"""
    
    content = sample_empty_file.read_bytes()
    
    with pytest.raises(ValueError, match="Arquivo vazio"):
      FileParser.parse(str(sample_empty_file), content)
  
  def test_parse_large_file_raises_error(self, sample_large_file):
    """Testa que arquivo muito grande levanta erro"""
    
    content = sample_large_file.read_bytes()
    
    with pytest.raises(ValueError, match="Arquivo muito grande"):
      FileParser.parse(str(sample_large_file), content)
  
  def test_parse_unsupported_extension_raises_error(self):
    """Testa que extensão não suportada levanta erro"""
    
    content = b"test content"
    
    with pytest.raises(ValueError, match="não suportado"):
      FileParser.parse("file.docx", content)
  
  def test_parse_file_without_extension_raises_error(self):
    """Testa que arquivo sem extensão levanta erro"""
    
    content = b"test content"
    
    with pytest.raises(ValueError, match="sem extensão"):
      FileParser.parse("filename", content)
  
  def test_get_extension_lowercase(self):
    """Testa que extensão é convertida para lowercase"""
    
    assert FileParser._get_extension("file.TXT") == ".txt"
    assert FileParser._get_extension("file.PDF") == ".pdf"
    assert FileParser._get_extension("file.EML") == ".eml"
  
  def test_parse_txt_with_utf8(self):
    """Testa parse de texto UTF-8"""
    
    content = "Olá, teste com acentuação".encode('utf-8')
    result = FileParser.parse("test.txt", content)
    
    assert "Olá" in result
    assert "acentuação" in result
  
  def test_parse_txt_with_latin1_fallback(self):
    """Testa fallback para latin-1 quando UTF-8 falha"""
    
    # Texto em latin-1 que não é UTF-8 válido
    content = "Café".encode('latin-1')
    result = FileParser.parse("test.txt", content)
    
    assert isinstance(result, str)
    assert len(result) > 0


class TestFileParserEML:
  """Testes específicos para arquivos .eml"""
  
  def test_parse_eml_basic(self):
    """Testa parse de email .eml básico"""
    
    eml_content = b"""From: sender@example.com
To: receiver@example.com
Subject: Test Email

This is the body of the email."""
    
    result = FileParser.parse("test.eml", eml_content)
    
    assert "sender@example.com" in result
    assert "Test Email" in result
    assert "body of the email" in result
  
  def test_parse_eml_without_body_raises_error(self):
    """Testa que email sem corpo levanta erro"""
    
    eml_content = b"""From: sender@example.com
Subject: No Body

"""
    
    with pytest.raises(ValueError, match="sem corpo de texto"):
      FileParser.parse("test.eml", eml_content)


class TestFileParserPDF:
  """Testes específicos para arquivos .pdf"""
  
  def test_parse_pdf_without_pypdf2_raises_error(self, monkeypatch):
    """Testa erro quando PyPDF2 não está instalado"""
    
    # Simula ImportError do PyPDF2
    def mock_import(*args, **kwargs):
      raise ImportError("No module named 'PyPDF2'")
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    content = b"%PDF-1.4 fake pdf content"
    
    with pytest.raises(ValueError, match="Suporte a PDF não instalado"):
      FileParser.parse("test.pdf", content)