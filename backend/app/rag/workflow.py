"""
RAG Workflow using LangGraph for complete RAG pipeline with multiple services
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional, Any
import logging
from app.services.indictrans2_service import translation_service
from app.services.vector_store_service import vector_store_service
from app.services.reranker_service import reranker_service
from app.services.llm_service import llm_service
from app.services.tavily_service import tavily_service

logger = logging.getLogger(__name__)


# Define workflow state
class RAGState(TypedDict):
    """RAG Workflow State"""
    original_query: str
    detected_language: str
    translated_query: Optional[str]
    intent: Optional[str]
    retrieved_docs: List[Dict[str, Any]]
    reranked_docs: List[Dict[str, Any]]
    context: Optional[str]
    answer: Optional[str]
    translated_answer: Optional[str]
    sources: List[Dict[str, Any]]
    verified_sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class RAGWorkflow:
    """End-to-end RAG workflow using LangGraph"""
    
    def __init__(self):
        """Initialize RAG Workflow"""
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("detect_language", self.detect_language)
        workflow.add_node("translate_query", self.translate_query)
        workflow.add_node("retrieve_docs", self.retrieve_docs)
        workflow.add_node("rerank_docs", self.rerank_docs)
        workflow.add_node("verify_sources", self.verify_sources)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("translate_answer", self.translate_answer)
        
        # Define edges
        workflow.set_entry_point("detect_language")
        workflow.add_edge("detect_language", "translate_query")
        workflow.add_edge("translate_query", "retrieve_docs")
        workflow.add_edge("retrieve_docs", "rerank_docs")
        workflow.add_edge("rerank_docs", "verify_sources")
        workflow.add_edge("verify_sources", "generate_answer")
        workflow.add_edge("generate_answer", "translate_answer")
        workflow.add_edge("translate_answer", END)
        
        return workflow.compile()
    
    async def detect_language(self, state: RAGState) -> RAGState:
        """Detect input language"""
        try:
            query = state["original_query"]
            detected_lang = await translation_service.detect_language(query)
            state["detected_language"] = detected_lang
            logger.info(f"Detected language: {detected_lang}")
            return state
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            state["detected_language"] = "en"
            return state
    
    async def translate_query(self, state: RAGState) -> RAGState:
        """Translate query to English"""
        try:
            query = state["original_query"]
            lang = state["detected_language"]
            
            if lang != "en":
                translated = await translation_service.translate(
                    query,
                    source_lang=lang,
                    target_lang="en"
                )
                state["translated_query"] = translated
            else:
                state["translated_query"] = query
            
            logger.info(f"Translated query: {state['translated_query']}")
            return state
        except Exception as e:
            logger.error(f"Translation error: {e}")
            state["translated_query"] = state["original_query"]
            return state
    
    async def retrieve_docs(self, state: RAGState) -> RAGState:
        """Retrieve relevant documents from multiple collections"""
        try:
            query = state["translated_query"]
            
            # Search across multiple collections
            investors = await vector_store_service.hybrid_search(
                "Investor", query, limit=10
            )
            deals = await vector_store_service.hybrid_search(
                "FundingDeal", query, limit=10
            )
            policies = await vector_store_service.hybrid_search(
                "PolicyDocument", query, limit=5
            )
            news = await vector_store_service.hybrid_search(
                "NewsArticle", query, limit=5
            )
            
            # Combine all results
            all_docs = investors + deals + policies + news
            state["retrieved_docs"] = all_docs
            logger.info(f"Retrieved {len(all_docs)} documents")
            return state
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            state["retrieved_docs"] = []
            return state
    
    async def rerank_docs(self, state: RAGState) -> RAGState:
        """Rerank retrieved documents for better relevance"""
        try:
            query = state["translated_query"]
            docs = state["retrieved_docs"]
            
            if not docs:
                state["reranked_docs"] = []
                return state
            
            reranked = await reranker_service.rerank(query, docs, top_k=7)
            state["reranked_docs"] = reranked
            logger.info(f"Reranked to top {len(reranked)} documents")
            return state
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            state["reranked_docs"] = state["retrieved_docs"][:7]
            return state
    
    async def verify_sources(self, state: RAGState) -> RAGState:
        """Verify source citations using Tavily web search"""
        try:
            docs = state["reranked_docs"]
            query = state["translated_query"]
            
            if not docs or not tavily_service.enabled:
                state["verified_sources"] = []
                return state
            
            # Prepare sources for verification
            sources_to_verify = []
            for doc in docs[:5]:  # Verify top 5 sources
                props = doc.get('properties', {})
                content = props.get('content', '')
                title = props.get(
                    'title',
                    props.get('name', props.get('startup_name', 'Unknown'))
                )
                sources_to_verify.append({
                    "title": title,
                    "content": content[:500],
                    "claim": query
                })
            
            # Verify sources in parallel
            verification_results = await tavily_service.verify_multiple_sources(sources_to_verify)
            
            # Merge verification results with sources
            verified_sources = []
            for i, result in enumerate(verification_results):
                if i < len(sources_to_verify):
                    verified_sources.append({
                        "source_title": sources_to_verify[i]["title"],
                        "verified": result.get("verified", False),
                        "confidence": result.get("confidence", 0),
                        "supporting_sources": result.get("supporting_sources", [])[:2]
                    })
            
            state["verified_sources"] = verified_sources
            logger.info(f"Verified {len(verified_sources)} sources")
            return state
            
        except Exception as e:
            logger.error(f"Source verification error: {e}")
            state["verified_sources"] = []
            return state
    
    async def generate_answer(self, state: RAGState) -> RAGState:
        """Generate answer using LLM with retrieved context"""
        try:
            query = state["translated_query"]
            docs = state["reranked_docs"]
            
            # Build context from documents
            context_parts = []
            sources = []
            
            for i, doc in enumerate(docs, 1):
                props = doc.get('properties', {})
                content = props.get('content', '')
                context_parts.append(f"[Document {i}]\n{content}\n")
                
                # Prepare source info
                source_title = props.get(
                    'title',
                    props.get(
                        'name',
                        props.get('startup_name', 'Unknown')
                    )
                )
                snippet = content[:200] + "..." if len(content) > 200 else content
                
                sources.append({
                    "id": i,
                    "title": source_title,
                    "snippet": snippet,
                    "type": doc.get('collection', 'document'),
                    "score": doc.get('rerank_score', doc.get('score', 0)),
                    "verified": False,
                    "verification_confidence": 0
                })
            
            # Add verification info to sources
            verified_sources = state.get("verified_sources", [])
            for source in sources:
                for verified in verified_sources:
                    if source["title"] == verified.get("source_title"):
                        source["verified"] = verified.get("verified", False)
                        source["verification_confidence"] = verified.get("confidence", 0)
                        source["supporting_web_sources"] = verified.get("supporting_sources", [])
                        break
            
            context = "\n".join(context_parts) if context_parts else ""
            state["context"] = context
            state["sources"] = sources
            
            # Generate answer using LLM
            result = await llm_service.generate_answer(
                query=query,
                context=context,
                sources=sources,
                language="en"
            )
            
            state["answer"] = result.get("answer", "No answer generated.")
            
            # Add metadata about whether fallback was used
            if result.get("fallback_used"):
                state["metadata"] = {
                    "answer_type": "general_knowledge",
                    "message": "Answer generated using general knowledge (no specific documents found)"
                }
            else:
                state["metadata"] = {
                    "answer_type": "context_based",
                    "documents_used": len(sources)
                }
            
            logger.info("Generated answer successfully")
            return state
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            state["answer"] = "I encountered an error generating the answer."
            state["sources"] = []
            return state
    
    async def translate_answer(self, state: RAGState) -> RAGState:
        """Translate answer back to user's original language"""
        try:
            answer = state["answer"]
            target_lang = state["detected_language"]
            
            if target_lang != "en":
                translated = await translation_service.translate(
                    answer,
                    source_lang="en",
                    target_lang=target_lang
                )
                state["translated_answer"] = translated
            else:
                state["translated_answer"] = answer
            
            logger.info("Translated answer successfully")
            return state
        except Exception as e:
            logger.error(f"Answer translation error: {e}")
            state["translated_answer"] = state["answer"]
            return state
    
    async def run(self, query: str) -> Dict[str, Any]:
        """
        Run the complete RAG workflow
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with answer, sources, language and metadata
        """
        try:
            initial_state: RAGState = {
                "original_query": query,
                "detected_language": "",
                "translated_query": None,
                "intent": None,
                "retrieved_docs": [],
                "reranked_docs": [],
                "context": None,
                "answer": None,
                "translated_answer": None,
                "sources": [],
                "verified_sources": [],
                "metadata": {}
            }
            
            # Execute workflow
            result = await self.graph.ainvoke(initial_state)
            
            # Count verified sources
            verified_count = sum(
                1 for s in result["sources"] 
                if s.get("verified", False)
            )
            
            return {
                "answer": result["translated_answer"],
                "sources": result["sources"],
                "language": result["detected_language"],
                "metadata": {
                    "retrieved_count": len(result["retrieved_docs"]),
                    "reranked_count": len(result["reranked_docs"]),
                    "verified_sources_count": verified_count,
                    "source_verification_enabled": tavily_service.enabled
                }
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "answer": "I encountered an error processing your query.",
                "sources": [],
                "language": "en",
                "metadata": {}
            }


# Create workflow instance
rag_workflow = RAGWorkflow()

