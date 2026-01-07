"""
Investor Search and Recommendation API Routes
"""
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import logging
import urllib.parse

from app.services.vector_store_service import vector_store_service
from app.services.llm_service import llm_service
from app.services.tavily_service import tavily_service

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


class InvestorDetailResponse(BaseModel):
    """Response with detailed investor information including web sources"""
    investor: Dict[str, Any] = Field(..., description="Investor profile from database")
    web_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Web search results about investor")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary about investor")
    recent_news: List[Dict[str, Any]] = Field(default_factory=list, description="Recent news about investor")


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
        
        # Build filters dictionary for Weaviate
        weaviate_filters = {}
        if sector:
            weaviate_filters['sector'] = sector
        if location:
            weaviate_filters['location'] = location
        if stage:
            weaviate_filters['stage'] = stage
        if investor_type:
            weaviate_filters['investor_type'] = investor_type
        
        logger.info(f"Searching investors with query: {query}, filters: {weaviate_filters}")
        
        # Search vector store with filters
        results = await vector_store_service.hybrid_search(
            "Investor",
            query=query,
            limit=limit,
            filters=weaviate_filters if weaviate_filters else None
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


@router.get("/details/{investor_name}", response_model=InvestorDetailResponse,
            responses={
                404: {"description": "Investor not found"},
                500: {"description": "Internal server error"}
            })
async def get_investor_details(
    investor_name: str = Path(..., description="Name of the investor to look up"),
    include_news: bool = Query(True, description="Include recent news about the investor")
) -> InvestorDetailResponse:
    """
    Get detailed information about a specific investor including web-sourced insights
    
    Searches for the investor in the database and enriches the profile with
    real-time web search results using Tavily API.
    
    Args:
        investor_name: Name of the investor/fund to look up
        include_news: Whether to include recent news
        
    Returns:
        InvestorDetailResponse with investor profile and web insights
    """
    try:
        # Decode URL-encoded investor name
        decoded_name = urllib.parse.unquote(investor_name)
        logger.info(f"Fetching details for investor: {decoded_name}")
        
        # Search for investor in database
        search_results = await vector_store_service.hybrid_search(
            "Investor",
            query=decoded_name,
            limit=5
        )
        
        # Find exact or best match
        investor_data = None
        for result in search_results:
            props = result.get('properties', {})
            if props.get('name', '').lower() == decoded_name.lower():
                investor_data = props
                break
        
        # If no exact match, use best match
        if not investor_data and search_results:
            investor_data = search_results[0].get('properties', {})
        
        if not investor_data:
            raise HTTPException(
                status_code=404,
                detail=f"Investor '{decoded_name}' not found"
            )
        
        # Format investor data
        investor_profile = {
            "name": investor_data.get('name', 'Unknown'),
            "type": investor_data.get('type', 'Venture Capital'),
            "focus_areas": investor_data.get('focus_areas', []),
            "location": investor_data.get('location', ''),
            "ticket_size": {
                "min": investor_data.get('ticket_size_min'),
                "max": investor_data.get('ticket_size_max')
            },
            "contact": {
                "email": investor_data.get('contact_email', ''),
                "website": investor_data.get('website', '')
            },
            "portfolio": investor_data.get('portfolio', []),
            "investment_stages": investor_data.get('investment_stages', []),
            "number_of_investments": investor_data.get('number_of_investments', 0),
            "number_of_exits": investor_data.get('number_of_exits', 0),
            "description": investor_data.get('description', ''),
            "founding_year": investor_data.get('founding_year'),
            "partner_name": investor_data.get('partner_name', ''),
            "twitter": investor_data.get('twitter', ''),
            "linkedin": investor_data.get('linkedin', '')
        }
        
        # Search for additional web insights using Tavily
        web_insights = []
        recent_news = []
        ai_summary = None
        
        try:
            # Search for general information about the investor
            investor_search_query = f"{decoded_name} venture capital fund investments portfolio"
            web_results = await tavily_service.search(
                query=investor_search_query,
                max_results=5,
                search_depth="advanced"
            )
            
            for result in web_results:
                web_insights.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:300] + "..." if len(result.get("content", "")) > 300 else result.get("content", ""),
                    "score": result.get("score", 0)
                })
            
            # Search for recent news if requested
            if include_news:
                news_query = f"{decoded_name} investment news funding announcement 2024"
                news_results = await tavily_service.search(
                    query=news_query,
                    max_results=3,
                    search_depth="basic"
                )
                
                for result in news_results:
                    recent_news.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                        "date": result.get("published_date")
                    })
            
            # Generate AI summary if we have web insights
            if web_insights:
                try:
                    summary_prompt = f"""Based on the following information about {decoded_name}, provide a brief 2-3 sentence summary of their investment focus and notable characteristics:

Investor Profile:
- Type: {investor_profile['type']}
- Focus: {', '.join(investor_profile['focus_areas'][:5])}
- Location: {investor_profile['location']}
- Portfolio: {', '.join(investor_profile['portfolio'][:5])}

Web Sources:
{chr(10).join([f"- {insight['title']}: {insight['snippet']}" for insight in web_insights[:3]])}

Provide a concise, factual summary."""

                    ai_summary = await llm_service.generate_simple_response(summary_prompt)
                except Exception as summary_error:
                    logger.warning(f"Could not generate AI summary: {summary_error}")
                    ai_summary = None
                    
        except Exception as tavily_error:
            logger.warning(f"Tavily search failed for {decoded_name}: {tavily_error}")
            # Continue without web insights
        
        logger.info(f"Successfully retrieved details for {decoded_name}")
        
        return InvestorDetailResponse(
            investor=investor_profile,
            web_insights=web_insights,
            ai_summary=ai_summary,
            recent_news=recent_news
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching investor details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching investor details")

