"""
Query API Routes for RAG system
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query as FastAPIQuery
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
import logging
import asyncio

from app.rag.workflow import rag_workflow
from app.services.tavily_service import tavily_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Semaphore to limit concurrent heavy operations
MAX_CONCURRENT_QUERIES = 5
query_semaphore = asyncio.Semaphore(MAX_CONCURRENT_QUERIES)


class QueryRequest(BaseModel):
    """Query request model with validation"""
    query: str = Field(..., min_length=3, max_length=1000, description="User query string")
    language: Optional[str] = Field(None, description="Preferred response language code")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for document retrieval")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty after stripping"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        if len(v.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        return v.strip()


class SourceInfo(BaseModel):
    """Source document information"""
    id: int = Field(..., description="Source document ID")
    title: str = Field(..., description="Document title")
    snippet: str = Field(..., description="Document snippet")
    type: str = Field(..., description="Document type")
    score: float = Field(default=0.0, description="Relevance score")


class QueryMetadata(BaseModel):
    """Query execution metadata"""
    retrieved_count: int = Field(default=0, description="Number of documents retrieved")
    reranked_count: int = Field(default=0, description="Number of documents after reranking")


class QueryResponse(BaseModel):
    """Query response model"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents")
    language: str = Field(default="en", description="Response language")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query execution metadata")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")


@router.post("/", response_model=QueryResponse, 
             responses={
                 400: {"model": ErrorResponse, "description": "Bad request - invalid query"},
                 500: {"model": ErrorResponse, "description": "Internal server error"},
                 503: {"model": ErrorResponse, "description": "Service unavailable"}
             })
async def process_query(request: QueryRequest) -> QueryResponse:
    """
    Main query endpoint for RAG system
    
    Processes user queries through the complete RAG pipeline:
    1. Language detection
    2. Query translation (if needed)
    3. Document retrieval from multiple collections
    4. Document reranking
    5. Answer generation with LLM
    6. Answer translation back to user language
    
    Args:
        request: QueryRequest with query and optional parameters
        
    Returns:
        QueryResponse with answer, sources, language and metadata
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Processing query: {request.query[:50]}...")
        
        # Validate query length
        if len(request.query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters long"
            )
        
        if len(request.query.strip()) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Query cannot exceed 1000 characters"
            )
        
        # Acquire semaphore to limit concurrent queries
        try:
            await asyncio.wait_for(query_semaphore.acquire(), timeout=30.0)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=503,
                detail="Server is busy. Please try again in a moment."
            )
        
        try:
            # Run RAG workflow with timeout
            try:
                result = await asyncio.wait_for(
                    rag_workflow.run(request.query),
                    timeout=120.0  # Increased timeout for complex queries
                )
            except asyncio.TimeoutError:
                logger.error("RAG workflow execution timed out")
                raise HTTPException(
                    status_code=503,
                    detail="Query processing timed out. Please try again."
                )
        finally:
            # Always release the semaphore
            query_semaphore.release()
        
        # Validate result structure
        if not result or not isinstance(result, dict):
            raise ValueError("Invalid workflow result structure")
        
        # Build response
        response = QueryResponse(
            answer=result.get("answer", "Unable to generate answer"),
            sources=result.get("sources", []),
            language=result.get("language", "en"),
            metadata=result.get("metadata", {})
        )
        
        logger.info(f"Query processed successfully. Retrieved {len(response.sources)} sources")
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions (validation errors)
        logger.warning(f"HTTP error processing query: {he.detail}")
        raise
    
    except ValueError as ve:
        # Validation errors
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for query service
    
    Returns:
        Health status information
    """
    try:
        return {
            "status": "healthy",
            "service": "query",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Query service is temporarily unavailable"
        )


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint for connectivity check
    
    Returns:
        Pong message
    """
    return {"message": "pong"}


class TranslateRequest(BaseModel):
    """Translation request model"""
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (hi, ta, te, bn, etc.)")


@router.post("/translate")
async def translate_text(request: TranslateRequest) -> Dict[str, Any]:
    """
    Translate text to target language using IndicTrans2 (local model)
    
    Args:
        request: TranslateRequest with text and target language
        
    Returns:
        Translated text
    """
    try:
        text = request.text
        target_language = request.target_language
        
        if target_language == "en":
            return {"translated_text": text, "source_language": "en", "target_language": "en"}
        
        # Map short codes to full language names for IndicTrans2
        lang_code_map = {
            "hi": "hindi",
            "ta": "tamil",
            "te": "telugu",
            "kn": "kannada",
            "bn": "bengali",
            "mr": "marathi",
            "gu": "gujarati",
            "ml": "malayalam",
            "pa": "punjabi",
            "or": "odia",
            "as": "assamese",
        }
        
        # Convert short code to full name
        target_lang_full = lang_code_map.get(target_language.lower(), target_language)
        
        # Use IndicTrans2 service singleton (local model - GPU/CPU)
        from app.services.indictrans2_service import translation_service as indic_service
        
        translated = await indic_service.translate(
            text=text,
            source_lang="english",
            target_lang=target_lang_full
        )
        
        return {
            "translated_text": translated,
            "source_language": "en",
            "target_language": target_language,
            "model": "IndicTrans2-1B"
        }
        
    except Exception as e:
        logger.error(f"IndicTrans2 translation error: {e}")
        # Fallback to Gemini if IndicTrans2 fails
        try:
            from app.services.translation_service import translation_service
            translated = await translation_service.translate(text=text, target_lang=target_language)
            return {
                "translated_text": translated,
                "source_language": "en", 
                "target_language": target_language,
                "model": "gemini-fallback"
            }
        except:
            return {"translated_text": request.text, "error": str(e)}


@router.post("/validate", response_model=Dict[str, Any])
async def validate_query(request: QueryRequest) -> Dict[str, Any]:
    """
    Validate query without processing
    
    Args:
        request: QueryRequest to validate
        
    Returns:
        Validation result
    """
    try:
        return {
            "valid": True,
            "message": "Query is valid",
            "query_length": len(request.query),
            "estimated_processing_time": "3-5 seconds"
        }
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============ SOURCE VERIFICATION ENDPOINTS ============

class SourceVerificationRequest(BaseModel):
    """Request to verify a source citation"""
    claim: str = Field(..., description="The claim or statement to verify")
    source_title: str = Field(..., description="Title of the source document")
    source_content: str = Field(..., description="Content snippet from the source")


class WebSearchRequest(BaseModel):
    """Request for web search"""
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum results to return")


class BackgroundCheckRequest(BaseModel):
    """Request for background check on an entity"""
    entity_name: str = Field(..., min_length=2, max_length=200, description="Name of the entity")
    entity_type: str = Field(default="startup", description="Type: startup, investor, company")


@router.post("/verify-source", response_model=Dict[str, Any])
async def verify_source(request: SourceVerificationRequest) -> Dict[str, Any]:
    """
    Verify a source citation using Tavily web search
    
    Searches the web for corroborating evidence to verify if the
    source citation is accurate and trustworthy.
    
    Args:
        request: SourceVerificationRequest with claim, title, and content
        
    Returns:
        Verification result with confidence score and supporting sources
    """
    try:
        if not tavily_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Source verification service is not available. Please configure TAVILY_API_KEY."
            )
        
        logger.info(f"Verifying source: {request.source_title[:50]}...")
        
        result = await tavily_service.verify_source(
            claim=request.claim,
            source_title=request.source_title,
            source_content=request.source_content
        )
        
        return {
            "success": True,
            "verification": result,
            "message": "Source verified" if result.get("verified") else "Could not verify source"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Source verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-search", response_model=Dict[str, Any])
async def web_search(request: WebSearchRequest) -> Dict[str, Any]:
    """
    Search the web using Tavily API
    
    Performs a web search and returns relevant results that can be
    used to verify claims or find additional information.
    
    Args:
        request: WebSearchRequest with query and max_results
        
    Returns:
        List of search results with title, url, content, and score
    """
    try:
        if not tavily_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Web search service is not available. Please configure TAVILY_API_KEY."
            )
        
        logger.info(f"Web search: {request.query[:50]}...")
        
        results = await tavily_service.search(
            query=request.query,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background-check", response_model=Dict[str, Any])
async def background_check(request: BackgroundCheckRequest) -> Dict[str, Any]:
    """
    Perform a background check on an entity (startup, investor, etc.)
    
    Searches for news, funding information, and potential red flags
    about the specified entity.
    
    Args:
        request: BackgroundCheckRequest with entity_name and entity_type
        
    Returns:
        Background check results with news, funding info, and warnings
    """
    try:
        if not tavily_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Background check service is not available. Please configure TAVILY_API_KEY."
            )
        
        logger.info(f"Background check for {request.entity_type}: {request.entity_name}")
        
        result = await tavily_service.background_check(
            entity_name=request.entity_name,
            entity_type=request.entity_type
        )
        
        return {
            "success": True,
            "background_check": result,
            "message": f"Found {result.get('sources_found', 0)} sources for {request.entity_name}"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Background check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verification-status")
async def verification_status() -> Dict[str, Any]:
    """
    Check if source verification service is available
    
    Returns:
        Status of the Tavily verification service
    """
    return {
        "enabled": tavily_service.enabled,
        "service": "Tavily",
        "features": [
            "source_verification",
            "web_search", 
            "background_check"
        ] if tavily_service.enabled else [],
        "message": "Source verification is available" if tavily_service.enabled else "TAVILY_API_KEY not configured"
    }

