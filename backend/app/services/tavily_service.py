"""
Tavily Service for web search and source citation verification
"""
import httpx
from typing import List, Dict, Optional, Any
import logging
import asyncio
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TavilyService:
    """Service for web search and source verification using Tavily API"""
    
    def __init__(self):
        """Initialize Tavily service"""
        if not settings.TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not configured - source verification will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.api_key = settings.TAVILY_API_KEY
            self.base_url = "https://api.tavily.com"
            logger.info("TavilyService initialized successfully")
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced" search
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            
        Returns:
            List of search results with title, url, content, and score
        """
        if not self.enabled:
            logger.warning("Tavily search called but service is disabled")
            return []
        
        try:
            logger.info(f"Tavily search: '{query[:50]}...' (max_results={max_results})")
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            }
            
            if include_domains:
                payload["include_domains"] = include_domains
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date"),
                })
            
            logger.info(f"Tavily returned {len(results)} results")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Tavily API HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return []
    
    async def verify_source(
        self,
        claim: str,
        source_title: str,
        source_content: str
    ) -> Dict[str, Any]:
        """
        Verify a source citation by searching for corroborating evidence
        
        Args:
            claim: The claim or statement being made
            source_title: Title of the source document
            source_content: Content snippet from the source
            
        Returns:
            Verification result with status, confidence, and supporting sources
        """
        if not self.enabled:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "Verification service not available",
                "supporting_sources": []
            }
        
        try:
            # Search for corroborating evidence
            search_query = f"{claim} {source_title}"
            web_results = await self.search(search_query, max_results=3)
            
            if not web_results:
                return {
                    "verified": False,
                    "confidence": 0.0,
                    "reason": "No corroborating sources found",
                    "supporting_sources": []
                }
            
            # Calculate verification confidence based on content overlap
            claim_keywords = set(claim.lower().split())
            source_keywords = set(source_content.lower().split())
            
            supporting_sources = []
            total_confidence = 0.0
            
            for result in web_results:
                web_content = result.get("content", "").lower()
                web_keywords = set(web_content.split())
                
                # Calculate keyword overlap
                claim_overlap = len(claim_keywords.intersection(web_keywords)) / max(len(claim_keywords), 1)
                source_overlap = len(source_keywords.intersection(web_keywords)) / max(len(source_keywords), 1)
                
                # Weighted confidence score
                confidence = (claim_overlap * 0.6 + source_overlap * 0.4) * result.get("score", 0.5)
                
                if confidence > 0.1:  # Threshold for relevance
                    supporting_sources.append({
                        "title": result["title"],
                        "url": result["url"],
                        "confidence": round(confidence, 3),
                        "snippet": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                    })
                    total_confidence += confidence
            
            # Average confidence across supporting sources
            avg_confidence = total_confidence / max(len(supporting_sources), 1)
            
            return {
                "verified": avg_confidence > 0.2,
                "confidence": round(min(avg_confidence, 1.0), 3),
                "reason": "Corroborating sources found" if avg_confidence > 0.2 else "Low confidence in verification",
                "supporting_sources": supporting_sources[:3]  # Top 3 sources
            }
            
        except Exception as e:
            logger.error(f"Source verification error: {str(e)}")
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": f"Verification failed: {str(e)}",
                "supporting_sources": []
            }
    
    async def verify_multiple_sources(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Verify multiple source citations in parallel
        
        Args:
            sources: List of sources with 'title', 'content', and 'claim' keys
            
        Returns:
            List of verification results for each source
        """
        if not self.enabled or not sources:
            return []
        
        try:
            # Create verification tasks
            tasks = []
            for source in sources:
                task = self.verify_source(
                    claim=source.get("claim", source.get("content", "")[:100]),
                    source_title=source.get("title", ""),
                    source_content=source.get("content", "")
                )
                tasks.append(task)
            
            # Run verifications in parallel (with rate limiting)
            results = []
            for i in range(0, len(tasks), 3):  # Process 3 at a time
                batch = tasks[i:i+3]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Verification task failed: {result}")
                        results.append({
                            "verified": False,
                            "confidence": 0.0,
                            "reason": str(result),
                            "supporting_sources": []
                        })
                    else:
                        results.append(result)
                
                # Small delay between batches to respect rate limits
                if i + 3 < len(tasks):
                    await asyncio.sleep(0.5)
            
            return results
            
        except Exception as e:
            logger.error(f"Multiple source verification error: {str(e)}")
            return []
    
    async def background_check(
        self,
        entity_name: str,
        entity_type: str = "startup"
    ) -> Dict[str, Any]:
        """
        Perform a background check on an entity (startup, investor, etc.)
        
        Args:
            entity_name: Name of the entity to check
            entity_type: Type of entity ("startup", "investor", "company")
            
        Returns:
            Background check results with news, funding info, etc.
        """
        if not self.enabled:
            return {
                "entity": entity_name,
                "type": entity_type,
                "news": [],
                "funding_info": [],
                "warnings": [],
                "verified": False
            }
        
        try:
            logger.info(f"Background check for {entity_type}: {entity_name}")
            
            # Search for recent news
            news_query = f"{entity_name} {entity_type} news 2024 2025"
            news_results = await self.search(news_query, max_results=5)
            
            # Search for funding information
            funding_query = f"{entity_name} funding investment round"
            funding_results = await self.search(
                funding_query, 
                max_results=3,
                include_domains=["techcrunch.com", "crunchbase.com", "economictimes.com", "yourstory.com", "inc42.com"]
            )
            
            # Search for any warnings/red flags
            warning_query = f"{entity_name} fraud scam lawsuit controversy"
            warning_results = await self.search(warning_query, max_results=2)
            
            # Process results
            news = [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r["content"][:200],
                    "date": r.get("published_date")
                }
                for r in news_results
            ]
            
            funding_info = [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r["content"][:200]
                }
                for r in funding_results
            ]
            
            # Check for potential warnings (only include if score is high)
            warnings = [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r["content"][:200]
                }
                for r in warning_results
                if r.get("score", 0) > 0.7  # Only high-confidence warnings
            ]
            
            return {
                "entity": entity_name,
                "type": entity_type,
                "news": news,
                "funding_info": funding_info,
                "warnings": warnings,
                "verified": len(news) > 0 or len(funding_info) > 0,
                "sources_found": len(news) + len(funding_info)
            }
            
        except Exception as e:
            logger.error(f"Background check error: {str(e)}")
            return {
                "entity": entity_name,
                "type": entity_type,
                "news": [],
                "funding_info": [],
                "warnings": [],
                "verified": False,
                "error": str(e)
            }


# Singleton instance
tavily_service = TavilyService()
