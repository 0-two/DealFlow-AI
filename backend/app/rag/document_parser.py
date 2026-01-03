"""
Document Parser for processing various document formats
"""
import PyPDF2
from pathlib import Path
from typing import Dict, List, Any
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentParser:
    """Service for parsing documents from various formats"""
    
    def __init__(self):
        self.supported_types = settings.SUPPORTED_FILE_TYPES
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
    
    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PDF document
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        try:
            text_content = []
            metadata = {
                "file_path": file_path,
                "file_type": "pdf",
                "pages": 0
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    text_content.append({
                        "page": page_num + 1,
                        "content": text
                    })
            
            full_text = "\n\n".join([page["content"] for page in text_content])
            
            return {
                "content": full_text,
                "metadata": metadata,
                "pages": text_content
            }
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
    
    def parse_txt(self, file_path: str) -> Dict[str, Any]:
        """
        Parse plain text document
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = {
                "file_path": file_path,
                "file_type": "txt"
            }
            
            return {
                "content": content,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {str(e)}")
            raise
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse file based on its extension
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(f"File size {file_size} exceeds maximum {self.max_file_size}")
        
        # Check if file type is supported
        if extension not in self.supported_types:
            raise ValueError(f"Unsupported file type: {extension}")
        
        if extension == ".pdf":
            return self.parse_pdf(file_path)
        elif extension == ".txt":
            return self.parse_txt(file_path)
        elif extension == ".md":
            return self.parse_txt(file_path)  # Markdown can be parsed as text
        else:
            raise ValueError(f"Parser not implemented for file type: {extension}")

