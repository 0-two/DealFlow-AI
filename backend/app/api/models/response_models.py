"""
Response Models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DocumentSource(BaseModel):
    """Model for document source information"""
    source: str = Field(..., description="Source of the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    score: float = Field(..., description="Relevance score")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="Generated answer")
    sources: List[DocumentSource] = Field(default_factory=list, description="Source documents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class InvestorSearchResponse(BaseModel):
    """Response model for investor search"""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    count: int = Field(..., description="Number of results")
    query: str = Field(..., description="Original query")


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis"""
    analysis: str = Field(..., description="Trend analysis text")
    trends: List[Dict[str, Any]] = Field(default_factory=list, description="Identified trends")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")


class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    success: bool = Field(..., description="Whether ingestion was successful")
    document_ids: List[str] = Field(default_factory=list, description="IDs of ingested documents")
    message: str = Field(..., description="Status message")
    num_documents: int = Field(..., description="Number of documents ingested")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")

