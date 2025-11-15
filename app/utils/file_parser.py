"""
Utilitário para extrair conteúdo de diferentes tipos de arquivo
"""
from typing import Optional
import email
from email import policy
from email.parser import BytesParser


class FileParser:
  """
  Parser para diferentes formatos de arquivo contendo emails.
  
  Suporta:
  - .txt (texto puro)
  - .eml (formato padrão de email)
  - .pdf (opcional, se pypdf2 estiver instalado)
  """
  
  SUPPORTED_EXTENSIONS = ['.txt', '.eml', '.pdf']
  MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
  
  @staticmethod
  def parse(filename: str, content: bytes) -> str:
    """
    Extrai texto de um arquivo baseado na extensão.
    
    Args:
        filename: Nome do arquivo (usado para detectar extensão)
        content: Conteúdo binário do arquivo
        
    Returns:
        Texto extraído do arquivo
        
    Raises:
        ValueError: Se formato não suportado ou arquivo inválido
    """

    # Valida tamanho
    if len(content) > FileParser.MAX_FILE_SIZE:
        raise ValueError(
            f"Arquivo muito grande. Máximo: {FileParser.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Detecta extensão
    extension = FileParser._get_extension(filename)
    
    # Parse baseado no tipo
    if extension == '.txt':
        return FileParser._parse_txt(content)
    elif extension == '.eml':
        return FileParser._parse_eml(content)
    elif extension == '.pdf':
        return FileParser._parse_pdf(content)
    else:
        raise ValueError(
            f"Formato '{extension}' não suportado. "
            f"Formatos aceitos: {', '.join(FileParser.SUPPORTED_EXTENSIONS)}"
        )
  
  @staticmethod
  def _get_extension(filename: str) -> str:
    """Obtém extensão do arquivo em lowercase."""

    if '.' not in filename:
        raise ValueError("Arquivo sem extensão")
    return '.' + filename.split('.')[-1].lower()
  
  @staticmethod
  def _parse_txt(content: bytes) -> str:
    """
    Parse de arquivo .txt simples.
    
    Args:
        content: Conteúdo binário
        
    Returns:
        Texto decodificado
    """

    try:
      # Tenta UTF-8 primeiro
      text = content.decode('utf-8')
    except UnicodeDecodeError:
      # Fallback para latin-1
      text = content.decode('latin-1', errors='ignore')
    
    text = text.strip()
    
    if not text:
      raise ValueError("Arquivo vazio")
    
    return text
  
  @staticmethod
  def _parse_eml(content: bytes) -> str:
    """
    Parse de arquivo .eml (formato padrão de email).
    
    Extrai o corpo do email (plain text ou HTML convertido).
    
    Args:
        content: Conteúdo binário do .eml
        
    Returns:
        Corpo do email como texto
    """
    try:
      # Parse do email
      msg = BytesParser(policy=policy.default).parsebytes(content)
      
      # Extrai informações principais
      subject = msg.get('subject', '(sem assunto)')
      from_addr = msg.get('from', '(desconhecido)')
      
      # Extrai corpo
      body = FileParser._extract_email_body(msg)
      
      if not body:
          raise ValueError("Email sem corpo de texto")
      
      # Monta texto completo
      email_text = f"De: {from_addr}\nAssunto: {subject}\n\n{body}"
      
      return email_text.strip()
          
    except Exception as e:
      raise ValueError(f"Erro ao processar arquivo .eml: {str(e)}")
  
  @staticmethod
  def _extract_email_body(msg) -> str:
    """
    Extrai o corpo de um objeto email.Message.
    
    Prioriza texto puro, mas aceita HTML se necessário.
    """

    body = ""
    
    if msg.is_multipart():
      # Email com múltiplas partes (texto + HTML, anexos, etc)
      for part in msg.walk():
        content_type = part.get_content_type()
        
        # Prioriza text/plain
        if content_type == 'text/plain':
          body = part.get_content()
          break
        elif content_type == 'text/html' and not body:
          # Usa HTML como fallback (poderia converter para texto)
          body = part.get_content()
    else:
      # Email simples
      body = msg.get_content()
  
    return body.strip() if body else ""
  
  @staticmethod
  def _parse_pdf(content: bytes) -> str:
    """
    Parse de arquivo PDF.
    
    NOTA: Requer pypdf2 instalado.
    
    Args:
        content: Conteúdo binário do PDF
        
    Returns:
        Texto extraído do PDF
    """
    
    try:
      from PyPDF2 import PdfReader
      from io import BytesIO
      
      # Cria objeto arquivo em memória
      pdf_file = BytesIO(content)
      
      # Lê PDF
      reader = PdfReader(pdf_file)
      
      # Extrai texto de todas as páginas
      text = ""
      for page in reader.pages:
        text += page.extract_text() + "\n"
      
      text = text.strip()
      
      if not text:
        raise ValueError("PDF não contém texto extraível")
      
      return text
        
    except ImportError:
      raise ValueError(
        "Suporte a PDF não instalado. "
        "Execute: pip install pypdf2"
      )
    except Exception as e:
      raise ValueError(f"Erro ao processar PDF: {str(e)}")