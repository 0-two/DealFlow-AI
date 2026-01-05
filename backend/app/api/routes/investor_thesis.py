from fastapi import APIRouter, Form, HTTPException
from app.services.vector_store_service import vector_store_service
from app.services.matching_service import matching_service
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

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
            "ticket_size_min": ticket_size_min,
            "ticket_size_max": ticket_size_max,
            "investment_thesis": investment_thesis,
            "investment_criteria": investment_criteria or "Not specified",
            "stages": stages_list,
            "geographies": geographies_list,
            "portfolio": portfolio_list,
            "contact_email": contact_email,
            "website": website,
            "created_date": datetime.now().isoformat(),
            "content": f"{investor_name} | {' '.join(focus_sectors_list)} | {investment_thesis} | {' '.join(stages_list)} | {' '.join(geographies_list)} | Ticket: ₹{ticket_size_min}-{ticket_size_max}Cr"
        }
        
        # Check if investor already exists and update, otherwise create
        existing = await vector_store_service.hybrid_search(
            "Investor",
            query=investor_name,
            limit=1
        )
        
        # Store/Update in vector database
        await vector_store_service.add_documents(
            "Investor",
            [investor_data],
            generate_embeddings=True
        )
        
        # Find matching startups
        logger.info("Finding matching startups...")
        matches = await matching_service.match_startups_for_investor(
            investor_data,
            top_k=15
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
        
        # Find matches
        matches = await matching_service.match_startups_for_investor(
            search_profile,
            top_k=15
        )
        
        return {
            "success": True,
            "matches": matches["matches"],
            "query_used": matches.get("query_used")
        }
        
    except Exception as e:
        logger.error(f"Startup search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
