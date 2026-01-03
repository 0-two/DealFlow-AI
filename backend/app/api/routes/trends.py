"""
Funding Trends and Analytics API Routes
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.services.vector_store_service import vector_store_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter()


class DealInfo(BaseModel):
    """Funding deal information"""
    startup_name: str = Field(..., description="Startup name")
    amount: float = Field(..., ge=0, description="Funding amount in USD")
    stage: str = Field(..., description="Funding stage")
    sector: str = Field(..., description="Industry sector")
    date: Optional[str] = Field(None, description="Deal date")
    investors: List[str] = Field(default_factory=list, description="Investor names")


class SectorTrendResponse(BaseModel):
    """Sector funding trend response"""
    sector: str = Field(..., description="Industry sector")
    year: int = Field(..., description="Fiscal year")
    total_funding: float = Field(..., description="Total funding amount in USD")
    deal_count: int = Field(..., description="Number of deals")
    average_deal_size: float = Field(..., description="Average deal size")
    unique_investors: int = Field(..., description="Number of unique investors")
    top_deals: List[Dict[str, Any]] = Field(..., description="Top 10 deals by amount")


class MonthlyTrendData(BaseModel):
    """Monthly trend data point"""
    month: str = Field(..., description="Month in YYYY-MM format")
    total_funding: float = Field(..., description="Total funding for the month")
    deal_count: int = Field(..., description="Number of deals")
    average_deal_size: float = Field(..., description="Average deal size")


class TimelineTrendResponse(BaseModel):
    """Timeline funding trend response"""
    timeline: List[MonthlyTrendData] = Field(..., description="Monthly trend data")
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


class AnalysisRequest(BaseModel):
    """Trend analysis request"""
    query: str = Field(..., min_length=3, max_length=500, description="Analysis query")
    dimensions: List[str] = Field(default_factory=list, description="Analysis dimensions")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class TrendAnalysisResponse(BaseModel):
    """Trend analysis response"""
    analysis: str = Field(..., description="AI-generated trend analysis")
    data_points: int = Field(..., description="Number of data points analyzed")
    dimensions: List[str] = Field(default_factory=list, description="Analyzed dimensions")
    insights: List[str] = Field(default_factory=list, description="Key insights")


@router.get("/sector", response_model=SectorTrendResponse,
            responses={
                400: {"description": "Invalid parameters"},
                500: {"description": "Internal server error"}
            })
async def get_sector_trends(
    sector: str = Query(..., description="Industry sector"),
    year: int = Query(2024, ge=2000, le=2100, description="Fiscal year")
) -> SectorTrendResponse:
    """
    Get funding trends for a specific sector
    
    Retrieves aggregated funding data for a sector including total funding,
    deal count, average deal size, and top deals.
    
    Args:
        sector: Industry sector to analyze
        year: Fiscal year (default: 2024)
        
    Returns:
        SectorTrendResponse with sector funding metrics
    """
    try:
        if not sector or not sector.strip():
            raise HTTPException(status_code=400, detail="Sector is required")
        
        logger.info(f"Fetching sector trends for {sector} in {year}")
        
        # Search funding deals for the sector
        query = f"{sector} funding {year}"
        results = await vector_store_service.hybrid_search(
            "FundingDeal",
            query=query,
            limit=100
        )
        
        if not results:
            logger.warning(f"No funding deals found for sector: {sector}, year: {year}")
            return SectorTrendResponse(
                sector=sector,
                year=year,
                total_funding=0.0,
                deal_count=0,
                average_deal_size=0.0,
                unique_investors=0,
                top_deals=[]
            )
        
        # Aggregate data
        deals = []
        total_funding = 0.0
        investors_set = set()
        
        for result in results:
            props = result.get('properties', {})
            amount = props.get('amount', 0)
            
            if amount > 0:
                total_funding += amount
            
            for inv in props.get('investors', []):
                if inv:
                    investors_set.add(inv)
            
            deal_info = {
                "startup": props.get('startup_name', 'Unknown'),
                "amount": amount,
                "stage": props.get('stage', 'Unknown'),
                "date": props.get('date'),
                "investors": props.get('investors', [])
            }
            deals.append(deal_info)
        
        # Calculate metrics
        avg_deal_size = total_funding / len(deals) if deals else 0.0
        
        # Get top 10 deals
        top_deals = sorted(deals, key=lambda x: x.get('amount', 0), reverse=True)[:10]
        
        logger.info(f"Found {len(deals)} funding deals for {sector} in {year}")
        
        return SectorTrendResponse(
            sector=sector,
            year=year,
            total_funding=total_funding,
            deal_count=len(deals),
            average_deal_size=avg_deal_size,
            unique_investors=len(investors_set),
            top_deals=top_deals
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Sector trends error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching sector trends")


@router.get("/timeline", response_model=TimelineTrendResponse,
            responses={
                400: {"description": "Invalid date format"},
                500: {"description": "Internal server error"}
            })
async def get_timeline_trends(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)")
) -> TimelineTrendResponse:
    """
    Get time series funding data
    
    Retrieves monthly aggregated funding trends between specified dates.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        
    Returns:
        TimelineTrendResponse with monthly trend data
    """
    try:
        # Parse and validate dates
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
        except ValueError as ve:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use ISO format: YYYY-MM-DD"
            )
        
        if start > end:
            raise HTTPException(
                status_code=400,
                detail="Start date cannot be after end date"
            )
        
        date_diff = (end - start).days
        if date_diff > 1825:  # ~5 years
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 5 years"
            )
        
        logger.info(f"Fetching timeline trends from {start_date} to {end_date}")
        
        # Search deals in date range
        results = await vector_store_service.hybrid_search(
            "FundingDeal",
            query="funding deals",
            limit=500
        )
        
        # Filter by date and aggregate by month
        monthly_data: Dict[str, Dict[str, float]] = {}
        
        for result in results:
            props = result.get('properties', {})
            deal_date_str = props.get('date')
            
            if not deal_date_str:
                continue
            
            try:
                deal_date = datetime.fromisoformat(deal_date_str)
                if start <= deal_date <= end:
                    month_key = deal_date.strftime("%Y-%m")
                    
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            "total_funding": 0.0,
                            "deal_count": 0
                        }
                    
                    monthly_data[month_key]["total_funding"] += props.get('amount', 0)
                    monthly_data[month_key]["deal_count"] += 1
            except (ValueError, TypeError):
                continue
        
        # Format for response
        timeline = []
        total_period_funding = 0.0
        total_period_deals = 0
        
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            avg_size = data["total_funding"] / data["deal_count"] if data["deal_count"] > 0 else 0.0
            
            timeline.append(
                MonthlyTrendData(
                    month=month,
                    total_funding=data["total_funding"],
                    deal_count=data["deal_count"],
                    average_deal_size=avg_size
                )
            )
            
            total_period_funding += data["total_funding"]
            total_period_deals += data["deal_count"]
        
        summary = {
            "total_funding": total_period_funding,
            "total_deals": total_period_deals,
            "months_covered": len(timeline),
            "average_monthly_funding": total_period_funding / len(timeline) if timeline else 0.0
        }
        
        logger.info(f"Generated timeline with {len(timeline)} months of data")
        
        return TimelineTrendResponse(
            timeline=timeline,
            start_date=start_date,
            end_date=end_date,
            summary=summary
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Timeline trends error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching timeline trends")


@router.post("/analyze", response_model=TrendAnalysisResponse,
             responses={
                 400: {"description": "Invalid request"},
                 500: {"description": "Internal server error"}
             })
async def analyze_trends(request: AnalysisRequest) -> TrendAnalysisResponse:
    """
    Generate AI-powered trend analysis
    
    Uses LLM to analyze funding trends based on query and selected dimensions.
    
    Args:
        request: AnalysisRequest with query and analysis dimensions
        
    Returns:
        TrendAnalysisResponse with AI-generated analysis
    """
    try:
        logger.info(f"Analyzing trends with query: {request.query}")
        
        # Get relevant funding data
        results = await vector_store_service.hybrid_search(
            "FundingDeal",
            query=request.query,
            limit=100
        )
        
        if not results:
            logger.warning(f"No data found for analysis query: {request.query}")
            return TrendAnalysisResponse(
                analysis="Insufficient data available to generate trend analysis.",
                data_points=0,
                dimensions=request.dimensions,
                insights=[]
            )
        
        # Format deals for analysis
        deals = []
        for result in results:
            props = result.get('properties', {})
            deal_info = {
                "startup_name": props.get('startup_name', 'Unknown'),
                "amount": props.get('amount', 0),
                "stage": props.get('stage', 'Unknown'),
                "sector": props.get('sector', 'Unknown'),
                "date": props.get('date'),
                "investors": props.get('investors', [])
            }
            deals.append(deal_info)
        
        # Generate analysis using LLM
        try:
            analysis_result = await llm_service.analyze_funding_trends(
                deals_data=deals,
                timeframe=request.query,
                dimensions=request.dimensions
            )
            
            analysis_text = analysis_result.get("analysis", "Unable to generate analysis")
            insights = analysis_result.get("insights", [])
            
        except Exception as llm_error:
            logger.error(f"LLM analysis error: {llm_error}")
            # Fallback analysis
            analysis_text = (
                f"Based on analysis of {len(deals)} funding deals matching '{request.query}', "
                f"the sector shows activity across multiple funding stages and investors."
            )
            insights = [
                f"Analyzed {len(deals)} funding deals",
                "Multiple funding stages represented",
                "Diverse investor participation"
            ]
        
        logger.info(f"Generated trend analysis for {len(deals)} data points")
        
        return TrendAnalysisResponse(
            analysis=analysis_text,
            data_points=len(deals),
            dimensions=request.dimensions,
            insights=insights
        )
        
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Trend analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error analyzing trends")


@router.get("/stats", response_model=Dict[str, Any])
async def get_funding_statistics() -> Dict[str, Any]:
    """
    Get overall funding statistics
    
    Returns global funding metrics and summary statistics.
    """
    try:
        logger.info("Fetching overall funding statistics")
        
        # Search all funding deals
        results = await vector_store_service.hybrid_search(
            "FundingDeal",
            query="funding",
            limit=1000
        )
        
        if not results:
            return {
                "total_deals": 0,
                "total_funding": 0.0,
                "average_deal_size": 0.0,
                "sectors": [],
                "stages": []
            }
        
        total_funding = 0.0
        sectors = set()
        stages = set()
        
        for result in results:
            props = result.get('properties', {})
            total_funding += props.get('amount', 0)
            
            if sector := props.get('sector'):
                sectors.add(sector)
            if stage := props.get('stage'):
                stages.add(stage)
        
        avg_deal_size = total_funding / len(results) if results else 0.0
        
        return {
            "total_deals": len(results),
            "total_funding": total_funding,
            "average_deal_size": avg_deal_size,
            "sectors": list(sectors),
            "stages": list(stages),
            "unique_sectors": len(sectors),
            "unique_stages": len(stages)
        }
        
    except Exception as e:
        logger.error(f"Error fetching funding statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching statistics")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for trends service
    
    Returns:
        Health status information
    """
    try:
        return {
            "status": "healthy",
            "service": "trends",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

