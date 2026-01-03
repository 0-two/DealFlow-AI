"""
Document Preprocessor for preparing documents for vector storage
"""
from typing import List, Dict, Any
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentPreprocessor:
    """Service for preprocessing documents before vectorization"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize preprocessor
        
        Args:
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence-ending punctuation near the chunk boundary
                for i in range(end, max(start, end - 200), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def preprocess_document(
        self, 
        document: Dict[str, Any],
        chunk: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Preprocess a document for vector storage
        
        Args:
            document: Document dictionary with content and metadata
            chunk: Whether to chunk the document
            
        Returns:
            List of preprocessed document chunks
        """
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        
        if not content:
            logger.warning("Document has no content")
            return []
        
        # Clean and normalize text
        content = self._clean_text(content)
        
        if chunk:
            chunks = self.chunk_text(content)
        else:
            chunks = [content]
        
        processed_docs = []
        for i, chunk_text in enumerate(chunks):
            processed_doc = {
                "content": chunk_text,
                "source": metadata.get("file_path", ""),
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            processed_docs.append(processed_doc)
        
        return processed_docs
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(cleaned_lines)
    
    def preprocess_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Preprocess multiple documents
        
        Args:
            documents: List of document dictionaries
            chunk: Whether to chunk documents
            
        Returns:
            List of preprocessed document chunks
        """
        all_processed = []
        for doc in documents:
            processed = self.preprocess_document(doc, chunk=chunk)
            all_processed.extend(processed)
        
        logger.info(f"Preprocessed {len(documents)} documents into {len(all_processed)} chunks")
        return all_processed

