from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.api.models.request_models import UserContext, UserRole
from app.services.pitch_deck_parser import pitch_deck_parser
from app.services.vector_store_service import vector_store_service
from app.services.matching_service import matching_service
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)


def get_rfc3339_timestamp() -> str:
    """Get current timestamp in RFC 3339 format for Weaviate DATE fields"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

router = APIRouter()

@router.post("/upload")
async def upload_pitch_deck(
    file: UploadFile = File(...),
    user_context: str = Form(...),
    contact_email: str = Form(None),
    website: str = Form(None),
    sector: str = Form(None),
    stage: str = Form(None),
    location: str = Form(None),
    funding_amount: str = Form(None)
):
    """Upload and parse pitch deck, then find matching investors"""
    try:
        # Parse user context
        context = json.loads(user_context)
        
        if context.get("role") != "founder":
            raise HTTPException(status_code=403, detail="Only founders can upload pitch decks")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        
        # Parse pitch deck
        logger.info(f"Parsing pitch deck: {file.filename}")
        startup_data = await pitch_deck_parser.parse_pitch_deck(content)
        
        # Override with user-provided values if present (they take priority)
        if sector:
            startup_data["sector"] = sector
            logger.info(f"Overriding sector with user-provided value: {sector}")
        
        if stage:
            startup_data["stage"] = stage
            logger.info(f"Overriding stage with user-provided value: {stage}")
        
        if location:
            startup_data["location"] = location
            logger.info(f"Overriding location with user-provided value: {location}")
        
        if funding_amount:
            try:
                startup_data["funding_amount"] = float(funding_amount)
                logger.info(f"Overriding funding_amount with user-provided value: {funding_amount}")
            except ValueError:
                logger.warning(f"Invalid funding_amount value: {funding_amount}, using parsed value")
        
        # Add metadata
        startup_data["contact_email"] = contact_email
        startup_data["website"] = website
        startup_data["created_date"] = get_rfc3339_timestamp()
        startup_data["pitch_deck_url"] = f"uploaded/{file.filename}"
        
        # Ensure numeric fields are proper types with better defaults
        startup_data["funding_amount"] = float(startup_data.get("funding_amount", 0) or 0)
        startup_data["revenue"] = float(startup_data.get("revenue", 0) or 0)
        startup_data["team_size"] = int(startup_data.get("team_size", 0) or 0)
        
        # Log warning if critical fields are missing
        if startup_data["funding_amount"] == 0:
            logger.warning(f"Funding amount is 0 for startup: {startup_data.get('startup_name')}")
        if not startup_data.get("sector"):
            logger.warning(f"Sector is missing for startup: {startup_data.get('startup_name')}")
        if not startup_data.get("stage"):
            logger.warning(f"Stage is missing for startup: {startup_data.get('startup_name')}")
        
        # Store in vector database
        logger.info(f"Storing startup: {startup_data.get('startup_name')}")
        storage_success = await vector_store_service.add_documents(
            "Startup",
            [startup_data],
            generate_embeddings=True
        )
        
        if not storage_success:
            logger.error(f"Failed to store startup in Weaviate: {startup_data.get('startup_name')}")
            raise HTTPException(
                status_code=500,
                detail="Failed to store startup data in vector database. Please try again."
            )
        
        # Find matching investors
        logger.info("Finding matching investors...")
        matches = await matching_service.match_investors_for_startup(
            startup_data,
            top_k=10
        )
        
        return {
            "success": True,
            "startup_profile": {
                "name": startup_data.get("startup_name"),
                "sector": startup_data.get("sector"),
                "stage": startup_data.get("stage"),
                "location": startup_data.get("location"),
                "description": startup_data.get("description"),
                "funding_amount": startup_data.get("funding_amount")
            },
            "matched_investors": matches["matches"],
            "message": f"Successfully uploaded pitch deck and found {len(matches['matches'])} matching investors"
        }
        
    except Exception as e:
        logger.error(f"Pitch deck upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual-submit")
async def manual_startup_submission(
    startup_name: str = Form(...),
    founder_name: str = Form(...),
    sector: str = Form(...),
    stage: str = Form(...),
    location: str = Form(...),
    funding_amount: float = Form(...),
    description: str = Form(...),
    problem_statement: str = Form(None),
    solution: str = Form(None),
    traction: str = Form(None),
    team_size: int = Form(None),
    revenue: float = Form(0),
    contact_email: str = Form(None),
    website: str = Form(None),
    user_context: str = Form(...)
):
    """Manually submit startup details without pitch deck"""
    try:
        context = json.loads(user_context)
        
        if context.get("role") != "founder":
            raise HTTPException(status_code=403, detail="Only founders can submit startups")
        
        # Build startup profile
        startup_data = {
            "startup_name": startup_name,
            "founder_name": founder_name,
            "sector": sector,
            "stage": stage,
            "location": location,
            "funding_amount": float(funding_amount),
            "description": description,
            "problem_statement": problem_statement or "Not provided",
            "solution": solution or "Not provided",
            "traction": traction or "Not provided",
            "team_size": int(team_size or 0),
            "revenue": float(revenue),
            "contact_email": contact_email,
            "website": website,
            "created_date": get_rfc3339_timestamp(),
            "content": f"{startup_name} | {sector} | {stage} | {location} | {description} | {problem_statement} | {solution}"
        }
        
        # Store in vector database
        logger.info(f"Storing startup manually: {startup_name}")
        storage_success = await vector_store_service.add_documents(
            "Startup",
            [startup_data],
            generate_embeddings=True
        )
        
        if not storage_success:
            logger.error(f"Failed to store startup in Weaviate: {startup_name}")
            raise HTTPException(
                status_code=500,
                detail="Failed to store startup data in vector database. Please try again."
            )
        
        # Find matching investors
        matches = await matching_service.match_investors_for_startup(
            startup_data,
            top_k=10
        )
        
        return {
            "success": True,
            "startup_profile": startup_data,
            "matched_investors": matches["matches"],
            "message": f"Successfully submitted startup and found {len(matches['matches'])} matching investors"
        }
        
    except Exception as e:
        logger.error(f"Manual submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
