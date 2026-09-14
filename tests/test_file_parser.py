from io import BytesIO

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

  def test_parse_pdf_extracts_text_with_pypdf(self):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    page = writer.pages[0]
    font = DictionaryObject({
      NameObject("/Type"): NameObject("/Font"),
      NameObject("/Subtype"): NameObject("/Type1"),
      NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
      NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 200 Td (Please review this PDF.) Tj ET")
    page[NameObject("/Contents")] = stream
    pdf = BytesIO()
    writer.write(pdf)

    assert FileParser.parse("email.pdf", pdf.getvalue()) == "Please review this PDF."
  
  def test_parse_pdf_without_pypdf_raises_error(self, monkeypatch):
    """Testa erro quando pypdf não está instalado"""
    
    # Simula ImportError do pypdf.
    original_import = __import__

    def mock_import(name, *args, **kwargs):
      if name == "pypdf":
        raise ImportError("No module named 'pypdf'")
      return original_import(name, *args, **kwargs)
    
    monkeypatch.setattr("builtins.__import__", mock_import)
    
    content = b"%PDF-1.4 fake pdf content"
    
    with pytest.raises(ValueError, match=r"Execute: pip install pypdf$"):
      FileParser.parse("test.pdf", content)
