"""
Query API Routes for RAG system
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query as FastAPIQuery
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
import logging
import asyncio

from app.rag.workflow import rag_workflow

logger = logging.getLogger(__name__)
router = APIRouter()


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
        
        # Run RAG workflow with timeout
        try:
            result = await asyncio.wait_for(
                rag_workflow.run(request.query),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            logger.error("RAG workflow execution timed out")
            raise HTTPException(
                status_code=503,
                detail="Query processing timed out. Please try again."
            )
        
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

