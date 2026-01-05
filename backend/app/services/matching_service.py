import logging
from typing import List, Dict
from app.services.vector_store_service import vector_store_service
from app.services.llm_service import llm_service
from app.services.reranker_service import reranker_service

logger = logging.getLogger(__name__)


class MatchingService:
    
    async def match_investors_for_startup(
        self,
        startup_profile: Dict,
        top_k: int = 10
    ) -> Dict:
        """Find best matching investors for a startup"""
        try:
            # Build search query from startup profile
            query = self._build_startup_search_query(startup_profile)
            
            # Search for matching investors
            investors = await vector_store_service.hybrid_search(
                "Investor",
                query=query,
                limit=30
            )
            
            if not investors:
                return {
                    "matches": [],
                    "reasoning": "No matching investors found. Try adjusting your profile or sector."
                }
            
            # Rerank based on relevance
            reranked = await reranker_service.rerank(query, investors, top_k=top_k)
            
            # Generate AI reasoning for each match
            matches_with_reasoning = await self._generate_match_reasoning(
                startup_profile,
                reranked,
                "investor"
            )
            
            return {
                "matches": matches_with_reasoning,
                "query_used": query
            }
            
        except Exception as e:
            logger.error(f"Error matching investors: {e}")
            return {"matches": [], "error": str(e)}
    
    async def match_startups_for_investor(
        self,
        investor_profile: Dict,
        top_k: int = 10
    ) -> Dict:
        """Find best matching startups for an investor"""
        try:
            # Build search query from investor thesis
            query = self._build_investor_search_query(investor_profile)
            
            # Search for matching startups
            startups = await vector_store_service.hybrid_search(
                "Startup",
                query=query,
                limit=30
            )
            
            if not startups:
                return {
                    "matches": [],
                    "reasoning": "No matching startups found. Try adjusting your thesis or criteria."
                }
            
            # Rerank based on relevance
            reranked = await reranker_service.rerank(query, startups, top_k=top_k)
            
            # Generate AI reasoning for each match
            matches_with_reasoning = await self._generate_match_reasoning(
                investor_profile,
                reranked,
                "startup"
            )
            
            return {
                "matches": matches_with_reasoning,
                "query_used": query
            }
            
        except Exception as e:
            logger.error(f"Error matching startups: {e}")
            return {"matches": [], "error": str(e)}
    
    def _build_startup_search_query(self, startup: Dict) -> str:
        """Build search query from startup profile"""
        parts = []
        
        if startup.get("sector"):
            parts.append(f"{startup['sector']} sector")
        
        if startup.get("stage"):
            parts.append(f"{startup['stage']} stage")
        
        if startup.get("location"):
            parts.append(f"{startup['location']} location")
        
        if startup.get("funding_amount"):
            parts.append(f"₹{startup['funding_amount']} crores funding")
        
        if startup.get("description"):
            parts.append(startup["description"][:200])
        
        return " ".join(parts)
    
    def _build_investor_search_query(self, investor: Dict) -> str:
        """Build search query from investor thesis"""
        parts = []
        
        if investor.get("focus_sectors"):
            sectors = " ".join(investor["focus_sectors"])
            parts.append(f"{sectors} sectors")
        
        if investor.get("stages"):
            stages = " ".join(investor["stages"])
            parts.append(f"{stages} stages")
        
        if investor.get("geographies"):
            geos = " ".join(investor["geographies"])
            parts.append(f"{geos} locations")
        
        if investor.get("investment_thesis"):
            parts.append(investor["investment_thesis"][:200])
        
        return " ".join(parts)
    
    async def _generate_match_reasoning(
        self,
        profile: Dict,
        matches: List[Dict],
        match_type: str
    ) -> List[Dict]:
        """Generate AI reasoning for why each match is good"""
        
        results = []
        
        for match in matches:
            props = match.get("properties", {})
            
            if match_type == "investor":
                reasoning_prompt = f"""Explain why this investor is a good match for the startup.

Startup Profile:
- Sector: {profile.get('sector')}
- Stage: {profile.get('stage')}
- Location: {profile.get('location')}
- Funding Need: ₹{profile.get('funding_amount')} Cr
- Description: {profile.get('description')}

Investor Profile:
- Name: {props.get('name')}
- Focus: {', '.join(props.get('focus_areas', []))}
- Stages: All stages they invest in
- Location: {props.get('location')}
- Ticket Size: ₹{props.get('ticket_size_min')}-{props.get('ticket_size_max')} Cr
- Portfolio: {', '.join(props.get('portfolio', [])[:3])}

Provide a 2-3 sentence explanation of why this is a good match. Be specific about alignment.
"""
            else:  # startup
                reasoning_prompt = f"""Explain why this startup is a good match for the investor.

Investor Thesis:
- Focus Sectors: {', '.join(profile.get('focus_sectors', []))}
- Stages: {', '.join(profile.get('stages', []))}
- Geographies: {', '.join(profile.get('geographies', []))}
- Ticket Size: ₹{profile.get('ticket_size_min')}-{profile.get('ticket_size_max')} Cr
- Thesis: {profile.get('investment_thesis')}

Startup Profile:
- Name: {props.get('startup_name')}
- Sector: {props.get('sector')}
- Stage: {props.get('stage')}
- Location: {props.get('location')}
- Funding Need: ₹{props.get('funding_amount')} Cr
- Description: {props.get('description')}
- Traction: {props.get('traction')}

Provide a 2-3 sentence explanation of why this is a good investment match. Be specific about alignment.
"""
            
            try:
                response = await llm_service.model.generate_content(reasoning_prompt)
                reasoning = response.text.strip()
            except:
                reasoning = "Good match based on sector, stage, and location alignment."
            
            results.append({
                "profile": props,
                "match_score": match.get("rerank_score", match.get("score", 0)),
                "reasoning": reasoning,
                "source": {
                    "type": "database",
                    "collection": "Investor" if match_type == "investor" else "Startup"
                }
            })
        
        return results


# Singleton instance
matching_service = MatchingService()
