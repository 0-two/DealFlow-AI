"""
LLM Service for Gemini integration with comprehensive error handling
"""
import google.generativeai as genai
from typing import List, Dict, Optional
import logging
import asyncio
import time
from app.config.settings import settings
from app.config.constants import GEMINI_SYSTEM_PROMPTS
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    """Service for interacting with Gemini LLM"""
    
    def __init__(self):
        """Initialize LLM service with Gemini model"""
        try:
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not configured in settings")
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            logger.info(f"Initializing LLM service with model: {settings.GEMINI_MODEL}")
            
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": settings.TEMPERATURE,
                    "max_output_tokens": settings.MAX_TOKENS,
                    "top_p": 0.8,
                }
            )
            
            # Default system prompt for startup funding advisor
            self.system_prompt = """You are an expert startup funding advisor for Indian entrepreneurs. 
Your role is to provide accurate, actionable insights about investors, funding trends, and government policies.

Guidelines:
1. Answer ONLY based on the provided context
2. Cite sources using [Source N] format
3. Explain complex terms in simple language
4. Structure answers clearly with bullet points when appropriate
5. If the context doesn't contain enough information, say "I don't have enough information to answer this accurately"
6. Always be encouraging and supportive to founders
7. Provide practical, actionable advice

Remember: You're helping founders make informed funding decisions."""
            
            logger.info("LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}", exc_info=True)
            raise
    
    async def generate_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        language: str = "en"
    ) -> Dict:
        """
        Generate answer using Gemini with context
        
        Args:
            query: User query/question
            context: Context text from retrieved documents
            sources: List of source dictionaries
            language: Response language (default: "en")
            
        Returns:
            Dictionary with answer, sources, and language
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for answer generation")
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "language": language
            }
        
        if not context or not context.strip():
            logger.warning("Empty context provided for answer generation")
            return {
                "answer": "I don't have enough information to answer this accurately.",
                "sources": [],
                "language": language
            }
        
        try:
            logger.info(f"Generating answer for query (length: {len(query)})")
            start_time = time.time()
            
            # Build prompt
            formatted_sources = self._format_sources(sources)
            prompt = f"""{self.system_prompt}

Context from reliable sources:
{context}

Sources:
{formatted_sources}

User Question: {query}

Instructions:
- Provide a comprehensive answer based on the context
- Cite sources using [Source 1], [Source 2] format
- Be specific with numbers, names, and details
- Structure your answer clearly
- Use simple language

Answer:"""
            
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Generate response (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Extract answer
            if not response:
                logger.error("Empty response from Gemini API")
                raise ValueError("Empty response from API")
            
            answer = response.text if hasattr(response, 'text') and response.text else "I couldn't generate an answer."
            
            if not answer or len(answer.strip()) == 0:
                logger.warning("Generated answer is empty")
                answer = "I couldn't generate an answer. Please try again."
            
            # Parse citations
            cited_sources = self._extract_citations(answer, sources)
            
            processing_time = time.time() - start_time
            logger.info(
                f"Answer generated successfully in {processing_time:.3f}s "
                f"(answer length: {len(answer)}, sources cited: {len(cited_sources)})"
            )
            
            return {
                "answer": answer,
                "sources": cited_sources,
                "language": language
            }
            
        except genai.types.BlockedPromptException as e:
            logger.error(f"Content blocked by Gemini API: {str(e)}")
            return {
                "answer": "I cannot process this query as it may violate content policies. Please rephrase your question.",
                "sources": [],
                "language": language
            }
        except genai.types.StopCandidateException as e:
            logger.error(f"Generation stopped by API: {str(e)}")
            return {
                "answer": "I encountered an issue while generating the answer. Please try again.",
                "sources": [],
                "language": language
            }
        except ValueError as e:
            logger.error(f"Value error during answer generation: {str(e)}")
            return {
                "answer": "I encountered an error processing your query. Please try again.",
                "sources": [],
                "language": language
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM generation error: {error_msg}", exc_info=True)
            
            # Check for rate limit or quota errors
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                logger.warning("Rate limit or quota exceeded")
                return {
                    "answer": "Service is currently busy. Please try again in a moment.",
                    "sources": [],
                    "language": language
                }
            
            return {
                "answer": "I encountered an error generating the answer. Please try again.",
                "sources": [],
                "language": language
            }
    
    async def generate_investor_recommendation(
        self,
        startup_profile: Dict,
        investors: List[Dict]
    ) -> Dict:
        """
        Generate personalized investor recommendations
        
        Args:
            startup_profile: Dictionary with startup information
            investors: List of investor dictionaries
            
        Returns:
            Dictionary with recommendation text
        """
        if not startup_profile:
            logger.warning("Empty startup profile provided")
            return {"recommendation": "Please provide startup profile information."}
        
        if not investors:
            logger.warning("Empty investors list provided")
            return {"recommendation": "No investors available for recommendation."}
        
        try:
            logger.info(f"Generating investor recommendations for startup profile")
            start_time = time.time()
            
            prompt = f"""Analyze the following startup profile and recommend the best investors from the list.

Startup Profile:
- Sector: {startup_profile.get('sector', 'Not specified')}
- Stage: {startup_profile.get('stage', 'Not specified')}
- Location: {startup_profile.get('location', 'Not specified')}
- Funding Needed: ₹{startup_profile.get('funding_needed', 'Not specified')} Cr
- Description: {startup_profile.get('description', 'Not provided')}

Available Investors:
{self._format_investors(investors)}

Task:
1. Rank the top 5 most suitable investors
2. For each investor, explain WHY they're a good match
3. Highlight any potential concerns
4. Provide actionable next steps

Format your response as:
**Rank 1: [Investor Name]**
Match Score: X/10
Why this is a good match: ...
Potential concerns: ...

**Rank 2: [Investor Name]**
...
"""
            
            logger.debug(f"Investor recommendation prompt length: {len(prompt)} characters")
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response or not hasattr(response, 'text'):
                logger.error("Empty response from Gemini API for recommendations")
                return {"recommendation": "Error generating recommendations. Please try again."}
            
            recommendation = response.text if response.text else "Error generating recommendations."
            
            processing_time = time.time() - start_time
            logger.info(
                f"Investor recommendations generated in {processing_time:.3f}s "
                f"(length: {len(recommendation)})"
            )
            
            return {"recommendation": recommendation}
            
        except genai.types.BlockedPromptException as e:
            logger.error(f"Content blocked for investor recommendations: {str(e)}")
            return {"recommendation": "Unable to generate recommendations due to content policy restrictions."}
        except Exception as e:
            logger.error(f"Recommendation generation error: {str(e)}", exc_info=True)
            return {"recommendation": "Error generating recommendations. Please try again."}
    
    async def analyze_funding_trends(
        self,
        deals_data: List[Dict],
        timeframe: str
    ) -> Dict:
        """
        Analyze and explain funding trends
        
        Args:
            deals_data: List of deal dictionaries
            timeframe: Time period for analysis
            
        Returns:
            Dictionary with analysis text
        """
        if not deals_data:
            logger.warning("Empty deals data provided for trend analysis")
            return {"analysis": "No deals data available for analysis."}
        
        if not timeframe:
            timeframe = "the specified period"
        
        try:
            logger.info(f"Analyzing funding trends for {timeframe} ({len(deals_data)} deals)")
            start_time = time.time()
            
            prompt = f"""Analyze the following funding data for {timeframe} and provide insights.

Funding Data Summary:
{self._format_deals_data(deals_data)}

Provide:
1. Key trends and patterns
2. Sector-wise analysis
3. Stage-wise distribution
4. Geographic insights
5. Predictions and recommendations for founders

Be specific with numbers and provide actionable insights."""
            
            logger.debug(f"Trend analysis prompt length: {len(prompt)} characters")
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response or not hasattr(response, 'text'):
                logger.error("Empty response from Gemini API for trend analysis")
                return {"analysis": "Error analyzing trends. Please try again."}
            
            analysis = response.text if response.text else "Error analyzing trends."
            
            processing_time = time.time() - start_time
            logger.info(
                f"Trend analysis completed in {processing_time:.3f}s "
                f"(analysis length: {len(analysis)})"
            )
            
            return {"analysis": analysis}
            
        except genai.types.BlockedPromptException as e:
            logger.error(f"Content blocked for trend analysis: {str(e)}")
            return {"analysis": "Unable to generate analysis due to content policy restrictions."}
        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}", exc_info=True)
            return {"analysis": "Error analyzing trends. Please try again."}
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for prompt"""
        if not sources:
            return "No sources available."
        
        try:
            formatted = []
            for i, source in enumerate(sources, 1):
                title = source.get('title', source.get('source', 'Unknown'))
                snippet = source.get('snippet', source.get('content', ''))[:200]  # Limit snippet length
                formatted.append(f"[Source {i}] {title} - {snippet}")
            
            return "\n".join(formatted)
        except Exception as e:
            logger.error(f"Error formatting sources: {str(e)}")
            return "Error formatting sources."
    
    def _extract_citations(self, answer: str, sources: List[Dict]) -> List[Dict]:
        """Extract which sources were cited in the answer"""
        if not answer or not sources:
            return sources[:3] if sources else []  # Return top 3 if no citations found
        
        try:
            cited = []
            for i, source in enumerate(sources, 1):
                # Check for citation patterns
                if f"[Source {i}]" in answer or f"Source {i}" in answer:
                    cited.append(source)
            
            # Return cited sources, or top 3 if no citations found
            return cited if cited else sources[:3]
        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
            return sources[:3] if sources else []
    
    def _format_investors(self, investors: List[Dict]) -> str:
        """Format investor list for prompt"""
        if not investors:
            return "No investors available."
        
        try:
            formatted = []
            for inv in investors:
                name = inv.get('name', 'Unknown')
                focus_areas = ', '.join(inv.get('focus_areas', [])) or 'Not specified'
                ticket_min = inv.get('ticket_size_min', 'N/A')
                ticket_max = inv.get('ticket_size_max', 'N/A')
                location = inv.get('location', 'Not specified')
                
                formatted.append(
                    f"- {name}: Focus on {focus_areas}, "
                    f"Ticket size: ₹{ticket_min} - ₹{ticket_max} Cr, "
                    f"Location: {location}"
                )
            
            return "\n".join(formatted)
        except Exception as e:
            logger.error(f"Error formatting investors: {str(e)}")
            return "Error formatting investors."
    
    def _format_deals_data(self, deals: List[Dict]) -> str:
        """Format deals data for analysis"""
        if not deals:
            return "No data available"
        
        try:
            # Create summary statistics
            total_funding = sum(float(d.get('amount', 0)) for d in deals)
            avg_deal = total_funding / len(deals) if deals else 0
            
            summary = f"""
Total Deals: {len(deals)}
Total Funding: ₹{total_funding:.2f} Cr
Average Deal Size: ₹{avg_deal:.2f} Cr

Sample Deals:
"""
            # Show first 10 deals
            for deal in deals[:10]:
                startup_name = deal.get('startup_name', 'Unknown')
                amount = deal.get('amount', 0)
                stage = deal.get('stage', 'Unknown')
                sector = deal.get('sector', 'Unknown')
                summary += f"- {startup_name}: ₹{amount} Cr ({stage}) in {sector}\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error formatting deals data: {str(e)}")
            return "Error formatting deals data."


# Singleton instance
try:
    llm_service = LLMService()
except Exception as e:
    logger.error(f"Failed to initialize llm_service singleton: {str(e)}")
    llm_service = None
