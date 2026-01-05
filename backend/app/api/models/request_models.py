"""
Request Models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from app.config.constants import QueryType


class UserRole(str, Enum):
    """User role enumeration"""
    FOUNDER = "founder"
    INVESTOR = "investor"


class UserContext(BaseModel):
    """User context for requests"""
    role: UserRole
    user_id: Optional[str] = None
    preferences: Optional[Dict] = None


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="User query text", min_length=1)
    language: Optional[str] = Field(default=None, description="Language of the query")
    user_context: UserContext = Field(..., description="User context with role information")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    query_type: Optional[QueryType] = Field(default=QueryType.GENERAL_QUERY, description="Type of query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters for retrieval")


class InvestorSearchRequest(BaseModel):
    """Request model for investor search"""
    query: str = Field(..., description="Search query for investors", min_length=1)
    user_context: UserContext = Field(..., description="User context with role information")
    top_k: Optional[int] = Field(default=10, ge=1, le=50, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    query: str = Field(..., description="Query for trend analysis", min_length=1)
    user_context: UserContext = Field(..., description="User context with role information")
    time_period: Optional[str] = Field(default=None, description="Time period for analysis")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")


class PitchDeckUpload(BaseModel):
    """Request model for pitch deck upload"""
    user_context: UserContext = Field(..., description="User context with role information")
    startup_name: str = Field(..., description="Name of the startup")
    sector: str = Field(..., description="Industry sector")
    stage: str = Field(..., description="Funding stage")
    location: str = Field(..., description="Company location")
    funding_amount: float = Field(..., description="Target funding amount")
    description: str = Field(..., description="Startup description")
    team_size: Optional[int] = Field(default=None, description="Number of team members")
    revenue: Optional[float] = Field(default=None, description="Current revenue")
    pitch_deck_url: Optional[str] = Field(default=None, description="URL to pitch deck document")


class InvestorThesisUpload(BaseModel):
    """Request model for investor thesis upload"""
    user_context: UserContext = Field(..., description="User context with role information")
    investor_name: str = Field(..., description="Name of the investor/fund")
    investment_thesis: str = Field(..., description="Investment thesis description")
    focus_sectors: List[str] = Field(..., description="List of focus sectors")
    stages: List[str] = Field(..., description="Preferred funding stages")
    geographies: List[str] = Field(..., description="Geographic preferences")
    ticket_size_min: float = Field(..., description="Minimum ticket size")
    ticket_size_max: float = Field(..., description="Maximum ticket size")
    portfolio: Optional[List[str]] = Field(default=None, description="List of portfolio companies")
    investment_criteria: Optional[str] = Field(default=None, description="Detailed investment criteria")


class MatchRequest(BaseModel):
    """Request model for matching startups with investors"""
    user_context: UserContext = Field(..., description="User context with role information")
    profile: Dict = Field(..., description="Startup or Investor profile")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of matches to return")


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

