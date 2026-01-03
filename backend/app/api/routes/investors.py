"""
Investor Search and Recommendation API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import logging

from app.services.vector_store_service import vector_store_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter()


class TicketSize(BaseModel):
    """Ticket size range"""
    min: Optional[float] = Field(None, description="Minimum ticket size in USD")
    max: Optional[float] = Field(None, description="Maximum ticket size in USD")


class InvestorProfile(BaseModel):
    """Investor profile information"""
    name: str = Field(..., description="Investor/fund name")
    type: str = Field(..., description="Type: VC, Angel, Corporate, etc.")
    focus_areas: List[str] = Field(default_factory=list, description="Investment focus areas")
    location: str = Field(..., description="Geographic location")
    ticket_size: TicketSize = Field(default_factory=TicketSize, description="Investment ticket size range")
    contact: Optional[Dict[str, str]] = Field(None, description="Contact information")
    portfolio: List[str] = Field(default_factory=list, description="Notable portfolio companies")
    score: float = Field(default=0.0, description="Relevance score")


class StartupProfile(BaseModel):
    """Startup profile for recommendations"""
    name: str = Field(..., min_length=1, max_length=100, description="Startup name")
    sector: str = Field(..., description="Industry sector")
    stage: str = Field(..., description="Funding stage (Seed, Series A, etc.)")
    location: str = Field(..., description="Headquarters location")
    funding_needed: float = Field(..., gt=0, description="Amount seeking to raise")
    description: str = Field(..., min_length=10, max_length=2000, description="Startup description")


class InvestorResponse(BaseModel):
    """Response with investor search results"""
    investors: List[Dict[str, Any]] = Field(..., description="List of investor profiles")
    count: int = Field(..., description="Total count of results")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Applied search filters")


class RecommendationResponse(BaseModel):
    """Response with investor recommendations"""
    recommendation: str = Field(..., description="AI-generated recommendation text")
    investors: List[Dict[str, Any]] = Field(..., description="Recommended investors")
    reasoning: Optional[str] = Field(None, description="Reasoning behind recommendations")
    count: int = Field(..., description="Number of recommended investors")


@router.get("/search", response_model=InvestorResponse,
            responses={
                400: {"description": "Invalid query parameters"},
                500: {"description": "Internal server error"}
            })
async def search_investors(
    sector: Optional[str] = Query(None, description="Industry sector to filter"),
    location: Optional[str] = Query(None, description="Geographic location to filter"),
    stage: Optional[str] = Query(None, description="Funding stage to filter (Seed, Series A, etc.)"),
    investor_type: Optional[str] = Query(None, description="Investor type (VC, Angel, Corporate)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return")
) -> InvestorResponse:
    """
    Search for investors with optional filters
    
    Search across investor profiles with flexible filtering by sector, location,
    funding stage, and investor type.
    
    Args:
        sector: Industry sector to filter by
        location: Geographic location to filter by
        stage: Funding stage to filter by
        investor_type: Type of investor to filter by
        limit: Maximum number of results (1-100)
        
    Returns:
        InvestorResponse with matching investor profiles
    """
    try:
        # Build search query from filters
        query_parts = []
        
        if sector:
            query_parts.append(f"{sector} sector")
        if stage:
            query_parts.append(f"{stage} stage investments")
        if location:
            query_parts.append(f"{location} location")
        if investor_type:
            query_parts.append(f"{investor_type} investor")
        
        # Default query if no filters
        query = " ".join(query_parts) if query_parts else "venture capital investors"
        
        logger.info(f"Searching investors with query: {query}")
        
        # Search vector store
        results = await vector_store_service.hybrid_search(
            "Investor",
            query=query,
            limit=limit
        )
        
        if not results:
            logger.info("No investors found matching criteria")
            return InvestorResponse(
                investors=[],
                count=0,
                filters_applied={
                    "sector": sector,
                    "location": location,
                    "stage": stage,
                    "investor_type": investor_type
                }
            )
        
        # Format results
        investors = []
        for result in results:
            props = result.get('properties', {})
            
            investor_data = {
                "name": props.get('name', 'Unknown'),
                "type": props.get('type', 'Venture Capital'),
                "focus_areas": props.get('focus_areas', []),
                "location": props.get('location', ''),
                "ticket_size": {
                    "min": props.get('ticket_size_min'),
                    "max": props.get('ticket_size_max')
                },
                "contact": {
                    "email": props.get('contact_email', ''),
                    "website": props.get('website', '')
                },
                "portfolio": props.get('portfolio', []),
                "score": result.get('score', 0)
            }
            investors.append(investor_data)
        
        logger.info(f"Found {len(investors)} investors matching criteria")
        
        return InvestorResponse(
            investors=investors,
            count=len(investors),
            filters_applied={
                "sector": sector,
                "location": location,
                "stage": stage,
                "investor_type": investor_type
            }
        )
        
    except ValueError as ve:
        logger.error(f"Validation error in investor search: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Investor search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error searching investors")


@router.post("/recommend", response_model=RecommendationResponse,
             responses={
                 400: {"description": "Invalid startup profile"},
                 500: {"description": "Internal server error"}
             })
async def recommend_investors(profile: StartupProfile) -> RecommendationResponse:
    """
    Get personalized investor recommendations
    
    Analyzes startup profile and recommends the most suitable investors
    based on sector, stage, funding needs, and investor preferences.
    
    Args:
        profile: StartupProfile with company information
        
    Returns:
        RecommendationResponse with personalized recommendations
    """
    try:
        # Validate profile
        if profile.funding_needed <= 0:
            raise HTTPException(
                status_code=400,
                detail="Funding needed must be positive"
            )
        
        logger.info(f"Generating recommendations for startup: {profile.name}")
        
        # Build search query for relevant investors
        query = f"{profile.sector} {profile.stage} startup {profile.location}"
        
        # Search vector store
        search_results = await vector_store_service.hybrid_search(
            "Investor",
            query=query,
            limit=15
        )
        
        if not search_results:
            logger.warning(f"No investors found for profile: {profile.name}")
            return RecommendationResponse(
                recommendation="No investors found matching your profile criteria.",
                investors=[],
                count=0
            )
        
        # Format investor data for LLM
        investors = []
        for result in search_results:
            props = result.get('properties', {})
            
            investor_info = {
                "name": props.get('name', 'Unknown'),
                "type": props.get('type', 'Venture Capital'),
                "focus_areas": props.get('focus_areas', []),
                "location": props.get('location', ''),
                "ticket_size_min": props.get('ticket_size_min'),
                "ticket_size_max": props.get('ticket_size_max'),
                "investment_stage_preference": props.get('stage_preference', []),
                "score": result.get('score', 0)
            }
            investors.append(investor_info)
        
        # Generate recommendations using LLM
        try:
            recommendation_result = await llm_service.generate_investor_recommendation(
                startup_profile=profile.dict(),
                investors=investors
            )
            
            recommendation_text = recommendation_result.get(
                "recommendation",
                "Based on your profile, we recommend connecting with investors in your sector."
            )
            reasoning = recommendation_result.get("reasoning", "")
            
        except Exception as llm_error:
            logger.error(f"LLM recommendation error: {llm_error}")
            # Fallback to simple matching
            recommendation_text = (
                f"Based on your {profile.stage} stage {profile.sector} startup, "
                f"we recommend reviewing these {profile.location}-based investors."
            )
            reasoning = "Fallback recommendation due to LLM service unavailability"
        
        logger.info(f"Generated recommendations for {len(investors)} investors")
        
        return RecommendationResponse(
            recommendation=recommendation_text,
            investors=investors,
            reasoning=reasoning,
            count=len(investors)
        )
        
    except HTTPException as he:
        raise he
    except ValueError as ve:
        logger.error(f"Validation error in recommendation: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Recommendation generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating recommendations")


@router.get("/filters", response_model=Dict[str, Any])
async def get_available_filters() -> Dict[str, Any]:
    """
    Get available filter options for investor search
    
    Returns:
        Dictionary with available filter values
    """
    try:
        # Return commonly used filter options
        return {
            "sectors": [
                "Technology",
                "Healthcare",
                "FinTech",
                "E-commerce",
                "SaaS",
                "Artificial Intelligence",
                "Biotechnology",
                "Clean Energy",
                "EdTech",
                "Enterprise Software"
            ],
            "stages": [
                "Seed",
                "Series A",
                "Series B",
                "Series C",
                "Series D",
                "Series E+",
                "Growth",
                "Late Stage"
            ],
            "investor_types": [
                "Venture Capital",
                "Angel Investor",
                "Corporate VC",
                "Private Equity",
                "Accelerator",
                "Family Office"
            ],
            "regions": [
                "North America",
                "Europe",
                "Asia Pacific",
                "India",
                "Middle East",
                "Latin America",
                "Africa"
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving filter options: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving filter options")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for investor service
    
    Returns:
        Health status information
    """
    try:
        return {
            "status": "healthy",
            "service": "investors",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

