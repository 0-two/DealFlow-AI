"""
Retriever for RAG-based document retrieval
"""
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.reranker_service import RerankerService
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class Retriever:
    """Service for retrieving relevant documents using RAG"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()
        self.reranker_service = RerankerService()
        self.top_k = settings.RETRIEVER_TOP_K
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Optional filters for retrieval
            use_reranking: Whether to use reranking
            
        Returns:
            List of relevant documents
        """
        try:
            top_k = top_k or self.top_k
            
            # Generate query embedding
            logger.info(f"Generating embedding for query: {query[:50]}...")
            query_embedding = await self.embedding_service.generate_query_embedding(query)
            
            # Retrieve documents from vector store
            logger.info(f"Retrieving top {top_k} documents from vector store")
            retrieved_docs = await self.vector_store_service.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k * 2 if use_reranking else top_k,  # Get more docs if reranking
                filters=filters
            )
            
            if not retrieved_docs:
                logger.warning("No documents retrieved")
                return []
            
            # Rerank documents if enabled
            if use_reranking and len(retrieved_docs) > 1:
                logger.info("Reranking retrieved documents")
                retrieved_docs = await self.reranker_service.rerank(
                    query=query,
                    documents=retrieved_docs,
                    top_k=top_k
                )
            
            return retrieved_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise
    
    async def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents and format as context for LLM
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Optional filters for retrieval
            
        Returns:
            Dictionary with query, documents, and formatted context
        """
        documents = await self.retrieve(query, top_k, filters)
        
        context_text = "\n\n".join([
            f"[Document {i+1}]\n{doc.get('content', '')}\nSource: {doc.get('source', 'Unknown')}"
            for i, doc in enumerate(documents)
        ])
        
        return {
            "query": query,
            "documents": documents,
            "context": context_text,
            "num_documents": len(documents)
        }

