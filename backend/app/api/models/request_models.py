"""
Request Models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.config.constants import QueryType


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="User query text", min_length=1)
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    query_type: Optional[QueryType] = Field(default=QueryType.GENERAL_QUERY, description="Type of query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters for retrieval")


class InvestorSearchRequest(BaseModel):
    """Request model for investor search"""
    query: str = Field(..., description="Search query for investors", min_length=1)
    top_k: Optional[int] = Field(default=10, ge=1, le=50, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    query: str = Field(..., description="Query for trend analysis", min_length=1)
    time_period: Optional[str] = Field(default=None, description="Time period for analysis")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")


class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    file_path: str = Field(..., description="Path to file to ingest")
    source: Optional[str] = Field(default=None, description="Source identifier for the document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    chunk: Optional[bool] = Field(default=True, description="Whether to chunk the document")


class BatchIngestRequest(BaseModel):
    """Request model for batch document ingestion"""
    file_paths: List[str] = Field(..., description="List of file paths to ingest")
    source: Optional[str] = Field(default=None, description="Source identifier for all documents")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    chunk: Optional[bool] = Field(default=True, description="Whether to chunk documents")

