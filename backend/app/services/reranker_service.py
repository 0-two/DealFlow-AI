"""
Reranker Service using Jina Reranker v2 for re-ranking search results
"""
import requests
from typing import List, Dict, Optional, Any
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class RerankerService:
    """Service for re-ranking search results using Jina Reranker v2"""
    
    def __init__(self):
        """Initialize Jina Reranker Service"""
        self.api_url = "https://api.jina.ai/v1/rerank"
        self.api_key = settings.JINA_API_KEY
        self.model = "jina-reranker-v2-base-multilingual"
        self.timeout = 30
        self.max_retries = 2
        
        if not self.api_key:
            logger.warning("JINA_API_KEY not configured. Reranking will use fallback mechanism.")
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Jina Reranker v2
        
        Args:
            query: Search query string
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            List of reranked documents with rerank scores
        """
        if not documents:
            logger.warning("No documents provided for reranking")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided for reranking")
            return self._fallback_rerank(documents, top_k)
        
        try:
            return self._rerank_with_jina(query, documents, top_k)
        except Exception as e:
            logger.error(f"Jina reranking failed: {e}. Using fallback mechanism.")
            return self._fallback_rerank(documents, top_k)
    
    def _rerank_with_jina(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Call Jina Reranker API with retry logic
        
        Args:
            query: Search query string
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            List of reranked documents
        """
        if not self.api_key:
            raise ValueError("JINA_API_KEY is not configured")
        
        # Extract document texts
        doc_texts = []
        for doc in documents:
            content = self._extract_content(doc)
            doc_texts.append(content)
        
        if not doc_texts:
            logger.warning("No extractable content found in documents")
            return documents[:top_k]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "query": query,
            "documents": doc_texts,
            "top_n": top_k
        }
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                results = response.json()
                reranked_docs = self._process_rerank_results(
                    results, documents, doc_texts, top_k
                )
                
                logger.info(f"Successfully reranked {len(doc_texts)} documents using Jina API")
                return reranked_docs
                
            except requests.exceptions.Timeout:
                logger.warning(f"Jina API timeout on attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    continue
                raise
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.error("Invalid Jina API key")
                    raise ValueError("Invalid JINA_API_KEY")
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limited by Jina API on attempt {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        continue
                logger.error(f"HTTP error from Jina API: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error to Jina API: {e}")
                if attempt < self.max_retries - 1:
                    continue
                raise
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing Jina API response: {e}")
                raise
    
    def _extract_content(self, doc: Dict[str, Any]) -> str:
        """
        Extract content from document object
        
        Args:
            doc: Document dictionary
            
        Returns:
            Extracted content string
        """
        # Try multiple content extraction methods
        if isinstance(doc, dict):
            # Try nested properties.content structure
            if "properties" in doc and isinstance(doc["properties"], dict):
                content = doc["properties"].get("content", "")
                if content:
                    return str(content).strip()
            
            # Try direct content field
            if "content" in doc:
                content = doc.get("content", "")
                if content:
                    return str(content).strip()
            
            # Try text field
            if "text" in doc:
                content = doc.get("text", "")
                if content:
                    return str(content).strip()
            
            # Try body field
            if "body" in doc:
                content = doc.get("body", "")
                if content:
                    return str(content).strip()
            
            # Try to use string representation
            return str(doc)
        
        return str(doc)
    
    def _process_rerank_results(
        self,
        results: Dict[str, Any],
        documents: List[Dict[str, Any]],
        doc_texts: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Process Jina API reranking results
        
        Args:
            results: Response from Jina API
            documents: Original documents list
            doc_texts: Extracted document texts
            top_k: Number of top documents to return
            
        Returns:
            Reranked documents with scores
        """
        reranked_docs = []
        
        try:
            for result in results.get("results", []):
                index = result.get("index")
                score = result.get("relevance_score", 0.0)
                
                if index is not None and 0 <= index < len(documents):
                    doc = documents[index].copy()
                    doc["rerank_score"] = score
                    reranked_docs.append(doc)
            
            if not reranked_docs:
                logger.warning("No valid results from Jina API reranking")
                return documents[:top_k]
            
            return reranked_docs[:top_k]
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error processing rerank results: {e}")
            return documents[:top_k]
    
    def _fallback_rerank(
        self,
        documents: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback reranking using existing scores
        
        Args:
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Sorted documents by existing score
        """
        try:
            # Sort by existing score if available, otherwise return as-is
            reranked = sorted(
                documents,
                key=lambda x: x.get("score", x.get("_score", 0.0)),
                reverse=True
            )[:top_k]
            
            logger.info(f"Using fallback reranking for {len(documents)} documents")
            return reranked
            
        except Exception as e:
            logger.error(f"Fallback reranking error: {e}")
            return documents[:top_k]


# Singleton instance
reranker_service = RerankerService()

