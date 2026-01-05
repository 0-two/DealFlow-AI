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
1. When context is available, prioritize it and cite sources using [Source N] format
2. When no context is available, use your general knowledge as a startup and investment expert
3. Always provide helpful, actionable advice about startups, investors, funding, and financial matters
4. Explain complex terms in simple language
5. Structure answers clearly with bullet points when appropriate
6. Be encouraging and supportive to founders
7. Provide practical, actionable advice
8. If you're not sure about something, acknowledge the limitations
9. If the user asks about something outside your knowledge, politely explain that you don't have specific information about that topic
10. Provide only answers that are relevant and accurate to the user's query and do not explain topics unrelated to the user's query
11. Maintain a professional yet approachable tone suitable for startup founders
12. Keep responses concise but comprehensive
13. When providing funding advice, consider Indian startup ecosystem specifics
14. Be aware of Indian regulatory environment and funding landscape
15. Do not provide citations for general knowledge answers, only when context is explicitly provided

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
        
        # Check for simple conversational queries that don't need detailed responses
        if self._is_simple_conversational_query(query):
            logger.info("Detected simple conversational query - providing brief response")
            return await self._generate_simple_response(query, language)
        
        if not context or not context.strip():
            logger.warning("Empty context provided for answer generation - using general knowledge fallback")
            # Use general knowledge fallback
            return await self._generate_general_answer(query, language)
        
        try:
            logger.info(f"Generating answer for query (length: {len(query)})")
            start_time = time.time()
            
            # Build formatted sources first
            formatted_sources = self._format_sources(sources)
            
            # Use specialized context-based prompt
            prompt = self._get_context_based_prompt(context, formatted_sources, query)
            
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
    
    async def _generate_general_answer(self, query: str, language: str = "en") -> Dict:
        """Generate answer using general knowledge when no context is available"""
        try:
            logger.info(f"Generating general knowledge answer for query: {query[:100]}...")
            
            # Use specialized general knowledge prompt
            general_prompt = self._get_general_knowledge_prompt(query)
            
            response = self.model.generate_content(
                general_prompt,
                generation_config={
                    "temperature": 0.7,  # Slightly higher creativity for general answers
                    "max_output_tokens": settings.MAX_TOKENS,
                }
            )
            
            answer = response.text.strip()
            
            logger.info(f"Generated general answer (length: {len(answer)})")
            
            return {
                "answer": answer,
                "sources": [],  # No specific sources for general knowledge
                "language": language,
                "fallback_used": True  # Flag to indicate general knowledge was used
            }
            
        except Exception as e:
            logger.error(f"Error generating general answer: {str(e)}")
            return {
                "answer": "I apologize, but I'm having trouble generating a response. Please try rephrasing your question or contact support if the issue persists.",
                "sources": [],
                "language": language,
                "error": True
            }
    
    def _is_simple_conversational_query(self, query: str) -> bool:
        """Detect if query is a simple conversational query that doesn't need detailed responses"""
        simple_queries = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
            "how are you", "how do you do", "what's up", "what's new",
            "tell me about yourself", "who are you", "what are you", "what do you do",
            "thanks", "thank you", "bye", "goodbye", "see you", "see you later",
            "help", "what can you do", "how can you help me", "what's your purpose"
        ]
        
        query_lower = query.lower().strip()
        query_lower = query_lower.rstrip('?!.')
        
        # Check exact matches
        if query_lower in simple_queries:
            return True
            
        # Check if query starts with simple greetings
        for simple_query in simple_queries:
            if query_lower.startswith(simple_query):
                return True
                
        # Check for very short queries (likely conversational)
        if len(query_lower.split()) <= 2 and len(query_lower) <= 10:
            return True
            
        return False
    
    async def _generate_simple_response(self, query: str, language: str = "en") -> Dict:
        """Generate brief, appropriate responses for simple conversational queries"""
        try:
            query_lower = query.lower().strip()
            
            # Greeting responses
            if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
                response = "Hello! I'm your startup funding advisor. I can help you with information about investors, funding options, and government schemes for Indian startups. What would you like to know?"
            
            # "How are you" responses
            elif any(how_query in query_lower for how_query in ["how are you", "how do you do"]):
                response = "I'm doing great and ready to help! I'm here to assist you with startup funding advice and investor information. How can I help you today?"
            
            # "Who are you" responses
            elif any(who_query in query_lower for who_query in ["who are you", "what are you", "tell me about yourself", "what do you do"]):
                response = "I'm an expert startup funding advisor specializing in the Indian startup ecosystem. I can help you find investors, understand funding options, and navigate government schemes. Feel free to ask me anything about startup funding!"
            
            # "What can you do" responses
            elif any(help_query in query_lower for help_query in ["what can you do", "how can you help", "what's your purpose", "help"]):
                response = "I can help you with: • Finding suitable investors for your startup • Understanding funding stages and amounts • Navigating government schemes like Startup India • Analyzing pitch decks • Providing startup ecosystem insights. What would you like to explore?"
            
            # "Thanks" responses
            elif any(thanks_query in query_lower for thanks_query in ["thanks", "thank you"]):
                response = "You're welcome! I'm here to help with any startup funding questions you might have. Feel free to ask anything else!"
            
            # "Goodbye" responses
            elif any(bye_query in query_lower for bye_query in ["bye", "goodbye", "see you", "see you later"]):
                response = "Goodbye! Feel free to come back anytime you need startup funding advice. Best of luck with your entrepreneurial journey!"
            
            # Default simple response
            else:
                response = "Hello! I'm your startup funding advisor. I can help you with investors, funding options, and government schemes for Indian startups. What would you like to know?"
            
            logger.info(f"Generated simple response for query: {query[:50]}...")
            
            return {
                "answer": response,
                "sources": [],
                "language": language,
                "response_type": "simple_conversational"
            }
            
        except Exception as e:
            logger.error(f"Error generating simple response: {str(e)}")
            return {
                "answer": "Hello! I'm your startup funding advisor. How can I help you today?",
                "sources": [],
                "language": language,
                "error": True
            }
    
    def _get_context_based_prompt(self, context: str, sources: str, query: str) -> str:
        """Get enhanced context-based prompt"""
        return f"""You are an expert startup funding advisor for Indian entrepreneurs with access to specific documents.

Your task is to answer the user's question using ONLY the provided context documents.

Guidelines:
1. Base your answer ENTIRELY on the provided context
2. Cite sources using [Source N] format for each piece of information
3. If multiple documents provide conflicting info, acknowledge and explain
4. Extract specific details like investor names, funding amounts, dates
5. Be precise and factual - no speculation beyond the documents
6. Structure answer with clear sections and bullet points
7. Include relevant quotes or data points from the documents
8. Maintain professional yet approachable tone
9. Keep responses concise but comprehensive
10. Focus on Indian startup ecosystem specifics

Context Documents:
{context}

Sources:
{sources}

User Question: {query}

Provide a comprehensive answer based on these documents:"""
    
    def _get_general_knowledge_prompt(self, query: str) -> str:
        """Get enhanced general knowledge prompt"""
        return f"""You are an expert startup funding advisor for Indian entrepreneurs.

No specific documents were found for this query. Please provide a helpful answer based on your general knowledge as a startup and investment expert.

Guidelines:
1. Provide practical, actionable advice for Indian entrepreneurs
2. Focus on startups, investors, funding, and financial matters
3. Include Indian startup ecosystem specifics
4. Mention current trends and best practices
5. Be encouraging and supportive to founders
6. Structure answer with clear sections and bullet points
7. Provide concrete examples and actionable steps
8. Acknowledge when information is general rather than specific
9. Maintain professional yet approachable tone
10. Keep responses concise but comprehensive

User Question: {query}

Please provide a comprehensive, helpful response:"""
    
    def _get_multilingual_prompt(self, query: str, language: str) -> str:
        """Get multilingual prompt for IndicTrans2"""
        return f"""You are an expert startup funding advisor for Indian entrepreneurs, capable of communicating in multiple Indian languages.

Guidelines:
1. Respond in the user's preferred language ({language})
2. Maintain professional yet approachable tone
3. Use appropriate terminology for the Indian startup ecosystem
4. Provide culturally relevant examples and advice
5. Keep language simple and accessible
6. Focus on practical, actionable guidance
7. Structure answer with clear sections and bullet points
8. Include Indian startup ecosystem specifics

User Question: {query}

Please provide helpful advice in {language}:"""
    
    def _get_pitch_deck_analysis_prompt(self, content: str) -> str:
        """Get pitch deck analysis prompt"""
        return f"""You are an expert venture capitalist and startup advisor analyzing pitch decks.

Your task is to analyze the provided pitch deck content and provide actionable feedback.

Guidelines:
1. Evaluate business model and value proposition
2. Assess market opportunity and competitive landscape
3. Review financial projections and funding requirements
4. Identify strengths and areas for improvement
5. Suggest specific investors who might be interested
6. Provide actionable recommendations for next steps
7. Structure feedback with clear sections
8. Be constructive and encouraging
9. Focus on Indian startup ecosystem context
10. Provide specific, actionable advice

Pitch Deck Content:
{content}

Provide comprehensive analysis and recommendations:"""
    
    def _get_investor_matching_prompt(self, startup_profile: str, investor_data: str) -> str:
        """Get investor matching prompt"""
        return f"""You are an expert startup funding advisor specializing in investor-startup matching.

Your task is to match startups with suitable investors based on their profiles.

Guidelines:
1. Analyze startup's sector, stage, and funding needs
2. Consider investor preferences and portfolio
3. Prioritize investors with relevant domain expertise
4. Consider geographic alignment
5. Provide reasoning for each recommendation
6. Suggest outreach strategies
7. Structure recommendations with clear rankings
8. Include specific contact information if available
9. Focus on Indian startup ecosystem
10. Provide actionable next steps

Startup Profile:
{startup_profile}

Available Investors:
{investor_data}

Provide ranked investor recommendations with reasoning:"""
    
    def _get_policy_information_prompt(self, context: str, query: str) -> str:
        """Get policy information prompt"""
        return f"""You are an expert on Indian government policies and schemes for startups.

Your task is to provide accurate information about government support programs.

Guidelines:
1. Provide accurate, up-to-date policy information
2. Explain eligibility criteria clearly
3. Detail application processes and timelines
4. Highlight benefits and limitations
5. Suggest complementary schemes
6. Include practical implementation tips
7. Structure information clearly with sections
8. Use simple, accessible language
9. Focus on actionable guidance
10. Include relevant contact information

Policy Context:
{context}

User Question: {query}

Provide comprehensive policy guidance:"""


# Singleton instance
try:
    llm_service = LLMService()
except Exception as e:
    logger.error(f"Failed to initialize llm_service singleton: {str(e)}")
    llm_service = None
