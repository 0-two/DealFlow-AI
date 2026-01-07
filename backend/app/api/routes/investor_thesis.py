from fastapi import APIRouter, Form, HTTPException, Path, Query
from app.services.vector_store_service import vector_store_service
from app.services.matching_service import matching_service
from app.services.tavily_service import tavily_service
from app.services.llm_service import llm_service
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import json
import urllib.parse

logger = logging.getLogger(__name__)


def get_rfc3339_timestamp() -> str:
    """Get current timestamp in RFC 3339 format for Weaviate DATE fields"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class StartupDetailResponse(BaseModel):
    """Response with detailed startup information including web sources"""
    startup: Dict[str, Any] = Field(..., description="Startup profile from database")
    web_insights: List[Dict[str, Any]] = Field(default_factory=list, description="Web search results about startup")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary about startup")
    recent_news: List[Dict[str, Any]] = Field(default_factory=list, description="Recent news about startup")
    funding_history: List[Dict[str, Any]] = Field(default_factory=list, description="Funding rounds information")


router = APIRouter()

@router.post("/upload-thesis")
async def upload_investor_thesis(
    investor_name: str = Form(...),
    investment_thesis: str = Form(...),
    focus_sectors: str = Form(...),  # Comma-separated
    stages: str = Form(...),  # Comma-separated
    geographies: str = Form(...),  # Comma-separated
    ticket_size_min: float = Form(...),
    ticket_size_max: float = Form(...),
    investment_criteria: str = Form(None),
    portfolio: str = Form(None),  # Comma-separated
    contact_email: str = Form(None),
    website: str = Form(None),
    user_context: str = Form(...)
):
    """Upload investor thesis and find matching startups"""
    try:
        context = json.loads(user_context)
        
        if context.get("role") != "investor":
            raise HTTPException(status_code=403, detail="Only investors can upload thesis")
        
        # Parse comma-separated fields
        focus_sectors_list = [s.strip() for s in focus_sectors.split(",")]
        stages_list = [s.strip() for s in stages.split(",")]
        geographies_list = [g.strip() for g in geographies.split(",")]
        portfolio_list = [p.strip() for p in portfolio.split(",")] if portfolio else []
        
        # Build investor profile
        investor_data = {
            "name": investor_name,
            "type": "Venture Capital",  # Can be made dynamic
            "focus_areas": focus_sectors_list,
            "location": geographies_list[0] if geographies_list else "India",
            "ticket_size_min": float(ticket_size_min),
            "ticket_size_max": float(ticket_size_max),
            "investment_thesis": investment_thesis,
            "investment_criteria": investment_criteria or "Not specified",
            "stages": stages_list,
            "geographies": geographies_list,
            "portfolio": portfolio_list,
            "contact_email": contact_email,
            "website": website,
            "created_date": get_rfc3339_timestamp(),
            "content": f"{investor_name} | {' '.join(focus_sectors_list)} | {investment_thesis} | {' '.join(stages_list)} | {' '.join(geographies_list)} | Ticket: ₹{ticket_size_min}-{ticket_size_max}Cr"
        }
        
        # Check if investor already exists and update, otherwise create
        existing = await vector_store_service.hybrid_search(
            "Investor",
            query=investor_name,
            limit=1
        )
        
        # Store/Update in vector database
        logger.info(f"Storing investor thesis: {investor_name}")
        storage_success = await vector_store_service.add_documents(
            "Investor",
            [investor_data],
            generate_embeddings=True
        )
        
        if not storage_success:
            logger.error(f"Failed to store investor in Weaviate: {investor_name}")
            raise HTTPException(
                status_code=500,
                detail="Failed to store investor data in vector database. Please try again."
            )
        
        # Find matching startups (browse mode - no reranker, no AI reasoning)
        logger.info("Finding matching startups...")
        matches = await matching_service.match_startups_for_investor(
            investor_data,
            top_k=30,
            use_reranker=False,
            generate_reasoning=False
        )
        
        return {
            "success": True,
            "investor_profile": {
                "name": investor_name,
                "focus_sectors": focus_sectors_list,
                "stages": stages_list,
                "geographies": geographies_list,
                "ticket_size": f"₹{ticket_size_min}-{ticket_size_max} Cr",
                "thesis": investment_thesis
            },
            "matched_startups": matches["matches"],
            "message": f"Successfully uploaded thesis and found {len(matches['matches'])} matching startups"
        }
        
    except Exception as e:
        logger.error(f"Investor thesis upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find-startups")
async def find_matching_startups(
    query: str = Form(...),
    focus_sectors: str = Form(None),
    stages: str = Form(None),
    max_funding: float = Form(None),
    location: str = Form(None),
    user_context: str = Form(...)
):
    """Quick search for startups based on criteria"""
    try:
        context = json.loads(user_context)
        
        if context.get("role") != "investor":
            raise HTTPException(status_code=403, detail="Only investors can search startups")
        
        # Build search profile
        search_profile = {
            "investment_thesis": query,
            "focus_sectors": [s.strip() for s in focus_sectors.split(",")] if focus_sectors else [],
            "stages": [s.strip() for s in stages.split(",")] if stages else [],
            "geographies": [location] if location else [],
            "ticket_size_min": 0,
            "ticket_size_max": max_funding if max_funding else 1000
        }
        
        # Find matches (browse mode - no reranker, no AI reasoning)
        matches = await matching_service.match_startups_for_investor(
            search_profile,
            top_k=50,
            use_reranker=False,
            generate_reasoning=False
        )
        
        return {
            "success": True,
            "matches": matches["matches"],
            "query_used": matches.get("query_used")
        }
        
    except Exception as e:
        logger.error(f"Startup search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup-details/{startup_name}", response_model=StartupDetailResponse,
            responses={
                404: {"description": "Startup not found"},
                500: {"description": "Internal server error"}
            })
async def get_startup_details(
    startup_name: str = Path(..., description="Name of the startup to look up"),
    include_news: bool = Query(True, description="Include recent news about the startup")
) -> StartupDetailResponse:
    """
    Get detailed information about a specific startup including web-sourced insights
    
    Searches for the startup in the database and enriches the profile with
    real-time web search results using Tavily API for investor due diligence.
    
    Args:
        startup_name: Name of the startup to look up
        include_news: Whether to include recent news
        
    Returns:
        StartupDetailResponse with startup profile and web insights
    """
    try:
        # Decode URL-encoded startup name
        decoded_name = urllib.parse.unquote(startup_name)
        logger.info(f"Fetching details for startup: {decoded_name}")
        
        # Search for startup in database
        search_results = await vector_store_service.hybrid_search(
            "Startup",
            query=decoded_name,
            limit=5
        )
        
        # Find exact or best match
        startup_data = None
        for result in search_results:
            props = result.get('properties', {})
            if props.get('startup_name', '').lower() == decoded_name.lower():
                startup_data = props
                break
        
        # If no exact match, use best match
        if not startup_data and search_results:
            startup_data = search_results[0].get('properties', {})
        
        if not startup_data:
            raise HTTPException(
                status_code=404,
                detail=f"Startup '{decoded_name}' not found"
            )
        
        # Format startup data
        startup_profile = {
            "name": startup_data.get('startup_name', 'Unknown'),
            "sector": startup_data.get('sector', 'Technology'),
            "stage": startup_data.get('stage', 'Unknown'),
            "location": startup_data.get('location', ''),
            "description": startup_data.get('description', ''),
            "problem_statement": startup_data.get('problem_statement', ''),
            "solution": startup_data.get('solution', ''),
            "business_model": startup_data.get('business_model', ''),
            "market_size": startup_data.get('market_size', ''),
            "traction": startup_data.get('traction', ''),
            "funding_amount": startup_data.get('funding_amount', 0),
            "team_size": startup_data.get('team_size', 0),
            "revenue": startup_data.get('revenue', 0),
            "contact": {
                "email": startup_data.get('contact_email', ''),
                "website": startup_data.get('website', '')
            },
            "founder_name": startup_data.get('founder_name', ''),
            # Additional fields from CSV ingestion
            "investors": startup_data.get('_investors_str', ''),
            "total_funding": startup_data.get('_total_funding', ''),
            "last_funding_date": startup_data.get('_last_funding_date', ''),
            "year_founded": startup_data.get('_year_founded', 0),
            "funding_status": startup_data.get('_funding_status', ''),
            "twitter": startup_data.get('_twitter', ''),
            "linkedin": startup_data.get('_linkedin', ''),
            "facebook": startup_data.get('_facebook', '')
        }
        
        # Search for additional web insights using Tavily
        web_insights = []
        recent_news = []
        funding_history = []
        ai_summary = None
        
        try:
            # Search for general information about the startup
            startup_search_query = f"{decoded_name} startup company {startup_profile['sector']} funding investors"
            web_results = await tavily_service.search(
                query=startup_search_query,
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
                news_query = f"{decoded_name} startup news funding announcement 2024 2025"
                news_results = await tavily_service.search(
                    query=news_query,
                    max_results=4,
                    search_depth="basic"
                )
                
                for result in news_results:
                    recent_news.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                        "date": result.get("published_date")
                    })
            
            # Search for funding history
            funding_query = f"{decoded_name} funding rounds series seed investment"
            funding_results = await tavily_service.search(
                query=funding_query,
                max_results=3,
                search_depth="basic"
            )
            
            for result in funding_results:
                funding_history.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
                })
            
            # Generate AI summary for investor due diligence
            if web_insights:
                try:
                    summary_prompt = f"""You are an investment analyst providing due diligence on a startup for potential investors.

Based on the following information about {decoded_name}, provide a concise 3-4 sentence investment summary covering:
1. What the company does and its market position
2. Key strengths or differentiators
3. Potential concerns or areas for due diligence

Startup Profile:
- Sector: {startup_profile['sector']}
- Stage: {startup_profile['stage']}
- Location: {startup_profile['location']}
- Description: {startup_profile['description'][:300] if startup_profile['description'] else 'Not available'}
- Investors: {startup_profile['investors'] or 'Not disclosed'}
- Total Funding: {startup_profile['total_funding'] or 'Not disclosed'}

Web Intelligence:
{chr(10).join([f"- {insight['title']}: {insight['snippet']}" for insight in web_insights[:3]])}

Provide a factual, balanced investment summary for this startup:"""

                    ai_summary = await llm_service.generate_simple_response(summary_prompt)
                except Exception as summary_error:
                    logger.warning(f"Could not generate AI summary: {summary_error}")
                    ai_summary = None
                    
        except Exception as tavily_error:
            logger.warning(f"Tavily search failed for {decoded_name}: {tavily_error}")
            # Continue without web insights
        
        logger.info(f"Successfully retrieved details for {decoded_name}")
        
        return StartupDetailResponse(
            startup=startup_profile,
            web_insights=web_insights,
            ai_summary=ai_summary,
            recent_news=recent_news,
            funding_history=funding_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching startup details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching startup details")
