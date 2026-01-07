"""
Enhanced LLM Service with Intelligent Hybrid RAG
Combines document retrieval with general knowledge for better responses
"""
import google.generativeai as genai
from typing import List, Dict, Optional
import logging
import asyncio
import time
from app.config.settings import settings
from typing import AsyncIterator

logger = logging.getLogger(__name__)


class LLMService:
    """Enhanced service for intelligent LLM interactions"""
    
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
                    "temperature": 0.4,  # Balanced between accuracy and creativity
                    "max_output_tokens": settings.MAX_TOKENS,
                    "top_p": 0.9,
                }
            )
            
            logger.info("✅ LLM service initialized successfully")
            
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
        Generate intelligent answer using hybrid approach:
        - Use retrieved documents if relevant
        - Fall back to general knowledge if documents insufficient
        - Combine both for best answer
        """
        if not query or not query.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "language": language
            }
        
        # Handle simple conversational queries
        if self._is_simple_conversational_query(query):
            logger.info("Simple conversational query detected")
            return await self._generate_simple_response(query, language)
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            start_time = time.time()
            
            # Check context relevance
            context_quality = self._assess_context_quality(query, context, sources)
            
            logger.info(f"Context quality score: {context_quality}/10")
            
            # Choose response strategy based on context quality
            if context_quality >= 7:
                # High quality context - use pure RAG
                logger.info("Using RAG mode (high quality context)")
                result = await self._generate_rag_answer(query, context, sources, language)
            
            elif context_quality >= 4:
                # Medium quality - hybrid mode
                logger.info("Using HYBRID mode (medium quality context)")
                result = await self._generate_hybrid_answer(query, context, sources, language)
            
            else:
                # Low quality context - use general knowledge
                logger.info("Using GENERAL KNOWLEDGE mode (low quality context)")
                result = await self._generate_general_answer(query, language)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Answer generated in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return {
                "answer": "I encountered an error. Please try rephrasing your question.",
                "sources": [],
                "language": language
            }
    
    def _assess_context_quality(self, query: str, context: str, sources: List[Dict]) -> int:
        """
        Assess if retrieved context is relevant to the query
        Returns score 0-10
        """
        if not context or not context.strip():
            return 0
        
        if not sources or len(sources) == 0:
            return 0
        
        # Extract key terms from query
        query_lower = query.lower()
        key_terms = []
        
        # Indian startup ecosystem keywords
        funding_terms = ['investor', 'vc', 'angel', 'funding', 'series', 'seed', 'capital', 
                        'investment', 'raise', 'funds', 'pitch', 'valuation', 'equity']
        
        sector_terms = ['fintech', 'edtech', 'healthtech', 'saas', 'ecommerce', 'startup',
                       'technology', 'software', 'platform', 'app', 'digital']
        
        india_terms = ['india', 'indian', 'bangalore', 'mumbai', 'delhi', 'hyderabad',
                      'rupees', 'crore', 'lakh', 'dpiit', 'startup india']
        
        # Check for relevant terms in query
        for term in funding_terms + sector_terms + india_terms:
            if term in query_lower:
                key_terms.append(term)
        
        if not key_terms:
            # Generic query - medium relevance
            return 5
        
        # Check how many key terms appear in context
        context_lower = context.lower()
        matches = sum(1 for term in key_terms if term in context_lower)
        
        # Check source quality
        irrelevant_indicators = ['zoom', 'zillionize', 'telecommunications', 'tmt']
        has_irrelevant = any(ind in context_lower for ind in irrelevant_indicators)
        
        # Calculate score
        if has_irrelevant and matches < len(key_terms) * 0.3:
            # Mostly irrelevant sources
            return 2
        
        match_ratio = matches / len(key_terms) if key_terms else 0
        base_score = int(match_ratio * 10)
        
        # Bonus for having multiple relevant sources
        if len(sources) >= 3 and matches >= len(key_terms) * 0.5:
            base_score += 2
        
        return min(base_score, 10)
    
    async def _generate_rag_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        language: str
    ) -> Dict:
        """Generate answer using pure RAG (high quality context)"""
        
        formatted_sources = self._format_sources(sources)
        
        prompt = f"""You are an expert startup funding advisor with deep knowledge of the Indian startup ecosystem.

**TASK**: Answer the user's question using the provided context documents. Be accurate and cite sources.

**CONTEXT FROM DOCUMENTS**:
{context}

**SOURCES**:
{formatted_sources}

**USER QUESTION**: {query}

**INSTRUCTIONS**:
1. Answer based primarily on the provided context
2. Cite specific sources using [Source N] format
3. Extract concrete details: names, amounts, dates, sectors
4. If context doesn't fully answer, supplement with your knowledge of Indian startup ecosystem
5. Be direct and actionable
6. Include practical next steps for founders

**YOUR ANSWER** (cite sources for specific facts):"""
        
        try:
            response = await self._call_gemini(prompt)
            cited_sources = self._extract_citations(response, sources)
            
            return {
                "answer": response,
                "sources": cited_sources,
                "language": language,
                "mode": "rag"
            }
        except Exception as e:
            logger.error(f"RAG generation error: {e}")
            # Fallback to hybrid
            return await self._generate_hybrid_answer(query, context, sources, language)
    
    async def _generate_hybrid_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        language: str
    ) -> Dict:
        """Generate answer combining retrieved docs with general knowledge"""
        
        formatted_sources = self._format_sources(sources)
        
        prompt = f"""You are an expert startup funding advisor for Indian entrepreneurs.

**USER QUESTION**: {query}

**AVAILABLE CONTEXT** (may be partially relevant):
{context}

**SOURCES**: {formatted_sources}

**YOUR TASK**:
You have some retrieved documents, but they may not fully answer the question. 

**INSTRUCTIONS**:
1. Be CONCISE - provide brief, actionable answers (2-4 sentences unless user asks for detail)
2. Use bullet points with proper line breaks (\\n• for bullets, \\n\\n for paragraphs)
3. **Use relevant parts from the context** where applicable - cite these with [Source N]
4. **Supplement with your expert knowledge** of Indian VC ecosystem and funding norms
5. **Be transparent** when using general knowledge
6. **Be practical and actionable** - 1-2 next steps maximum

**YOUR COMPREHENSIVE ANSWER** (be concise):"""
        
        try:
            response = await self._call_gemini(prompt)
            cited_sources = self._extract_citations(response, sources) if sources else []
            
            return {
                "answer": response,
                "sources": cited_sources[:5] if cited_sources else [],  # Limit sources
                "language": language,
                "mode": "hybrid"
            }
        except Exception as e:
            logger.error(f"Hybrid generation error: {e}")
            return await self._generate_general_answer(query, language)
    
    async def _generate_general_answer(self, query: str, language: str) -> Dict:
        """Generate answer using general knowledge (no relevant context)"""
        
        prompt = f"""You are an expert startup funding advisor specializing in the Indian startup ecosystem.

**USER QUESTION**: {query}

**CONTEXT**: No specific documents were retrieved for this query. Provide helpful guidance based on your knowledge.

**INSTRUCTIONS**:
1. Be CONCISE - provide brief, clear answers (2-4 sentences unless user asks for detail)
2. Use bullet points with proper line breaks (\\n• for bullets, \\n\\n for paragraphs)
3. Clearly indicate this is general guidance
4. Give practical, actionable advice
5. If mentioning specific investors, note these are examples

**YOUR EXPERT GUIDANCE** (be concise):"""
        
        try:
            response = await self._call_gemini(prompt, temperature=0.6)
            
            return {
                "answer": response,
                "sources": [],
                "language": language,
                "mode": "general_knowledge",
                "fallback_used": True,
                "note": "Based on general knowledge of Indian startup ecosystem"
            }
        except Exception as e:
            logger.error(f"General knowledge error: {e}")
            return {
                "answer": "I'm having trouble generating a response. Please try rephrasing your question about startup funding, investors, or government schemes.",
                "sources": [],
                "language": language
            }
    
    async def _call_gemini(self, prompt: str, temperature: float = 0.4) -> str:
        """Call Gemini API with error handling"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": settings.MAX_TOKENS,
                    }
                )
            )
            
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Empty response from Gemini")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def _stream_gemini(self, prompt: str, temperature: float = 0.4) -> AsyncIterator[str]:
        """Stream tokens from Gemini using a background thread feeding an asyncio queue"""
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        SENTINEL = object()

        def worker():
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": settings.MAX_TOKENS,
                    },
                    stream=True,
                )
                for chunk in response:
                    try:
                        text = getattr(chunk, 'text', None)
                        if text:
                            loop.call_soon_threadsafe(queue.put_nowait, text)
                    except Exception:
                        continue
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"[stream_error] {str(e)}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, SENTINEL)

        # Start worker thread without awaiting
        loop.run_in_executor(None, worker)

        while True:
            item = await queue.get()
            if item is SENTINEL:
                break
            yield str(item)

    async def stream_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        language: str = "en"
    ) -> AsyncIterator[str]:
        """Stream answer using same strategy selection as non-streaming path"""
        # Conversational fast path
        if self._is_simple_conversational_query(query):
            # Stream a short canned response
            simple = (await self._generate_simple_response(query, language)).get("answer", "Hello")
            # yield in one chunk
            yield simple
            return

        # Choose mode
        context_quality = self._assess_context_quality(query, context, sources)
        try:
            if context_quality >= 7:
                formatted_sources = self._format_sources(sources)
                prompt = f"""You are an expert startup funding advisor with deep knowledge of the Indian startup ecosystem.

**TASK**: Answer the user's question using the provided context documents. Be accurate and cite sources.

**CONTEXT FROM DOCUMENTS**:
{context}

**SOURCES**:
{formatted_sources}

**USER QUESTION**: {query}

**INSTRUCTIONS**:
1. Be CONCISE and to-the-point - provide brief, actionable answers
2. Use bullet points with proper line breaks (\\n• for bullets, \\n\\n for paragraphs)
3. Only provide detailed explanations if the user explicitly asks for it
4. Cite specific sources using [Source N] format for facts
5. Extract concrete details: names, amounts, dates, sectors
6. If context doesn't fully answer, briefly supplement with your knowledge
7. Include 1-2 practical next steps maximum

**YOUR ANSWER** (be concise, cite sources):"""
                async for token in self._stream_gemini(prompt, temperature=0.4):
                    yield token
            elif context_quality >= 4:
                formatted_sources = self._format_sources(sources)
                prompt = f"""You are an expert startup funding advisor for Indian entrepreneurs.

**USER QUESTION**: {query}

**AVAILABLE CONTEXT** (may be partially relevant):
{context}

**SOURCES**: {formatted_sources}

**YOUR TASK**:
You have some retrieved documents, but they may not fully answer the question. 

**INSTRUCTIONS**:
1. **Use relevant parts from the context** where applicable - cite these with [Source N]
2. **Supplement with your expert knowledge** of the Indian VC ecosystem and funding norms
3. **Be transparent** when using general knowledge
4. **Be practical and actionable**

**YOUR COMPREHENSIVE ANSWER** (combining documents + expertise):"""
                async for token in self._stream_gemini(prompt, temperature=0.4):
                    yield token
            else:
                prompt = f"""You are an expert startup funding advisor specializing in the Indian startup ecosystem.

**USER QUESTION**: {query}

**CONTEXT**: No specific documents were retrieved for this query. Provide helpful guidance based on your knowledge.

**INSTRUCTIONS**:
1. Provide accurate, helpful information based on your knowledge
2. Clearly indicate this is general guidance
3. Give practical, actionable advice

**YOUR EXPERT GUIDANCE**:"""
                async for token in self._stream_gemini(prompt, temperature=0.6):
                    yield token
        except Exception as e:
            yield f"[stream_error] {str(e)}"
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for prompt"""
        if not sources:
            return "No sources available."
        
        formatted = []
        for i, source in enumerate(sources[:5], 1):  # Limit to top 5
            title = source.get('title', source.get('name', 'Unknown'))
            snippet = source.get('snippet', source.get('content', ''))[:200]
            formatted.append(f"[Source {i}] {title}: {snippet}")
        
        return "\n".join(formatted)
    
    def _extract_citations(self, answer: str, sources: List[Dict]) -> List[Dict]:
        """Extract cited sources from answer"""
        if not answer or not sources:
            return []
        
        cited = []
        for i, source in enumerate(sources, 1):
            if f"[Source {i}]" in answer or f"Source {i}" in answer:
                cited.append(source)
        
        return cited if cited else sources[:3]  # Return top 3 if no explicit citations
    
    def _is_simple_conversational_query(self, query: str) -> bool:
        """Detect simple greetings/conversational queries"""
        simple_queries = [
            "hi", "hello", "hey", "how are you", "who are you", 
            "what can you do", "thanks", "thank you", "bye"
        ]
        
        query_lower = query.lower().strip().rstrip('?!.')
        
        if query_lower in simple_queries:
            return True
        
        if len(query.split()) <= 3 and any(q in query_lower for q in simple_queries):
            return True
        
        return False
    
    async def _generate_simple_response(self, query: str, language: str) -> Dict:
        """Generate brief response for conversational queries"""
        query_lower = query.lower()
        
        if any(g in query_lower for g in ["hi", "hello", "hey"]):
            response = "Hello! I'm your AI advisor for startup funding in India. I can help you with:\n• Finding investors (VCs, Angels)\n• Understanding funding options\n• Government schemes\n• Pitch deck guidance\n\nWhat would you like to know?"
        
        elif "who are you" in query_lower or "what are you" in query_lower:
            response = "I'm an AI-powered startup funding advisor specializing in the Indian ecosystem. I can help you find investors, understand funding stages, navigate government schemes, and provide practical fundraising guidance. Ask me anything!"
        
        elif "what can you do" in query_lower or "help" in query_lower:
            response = "I can assist with:\n\n• **Investor Discovery**: Find VCs and Angels matching your sector, stage, and location\n• **Funding Guidance**: Explain Series A, Seed, ticket sizes, typical terms\n• **Government Schemes**: Startup India, SISFS, state policies\n• **Strategy**: Pitch deck feedback, approach strategies\n• **Ecosystem Insights**: Trends, data, best practices\n\nWhat specific help do you need?"
        
        elif any(t in query_lower for t in ["thanks", "thank you"]):
            response = "You're welcome! Feel free to ask anything about startup funding. I'm here to help! 🚀"
        
        elif "bye" in query_lower:
            response = "Goodbye! Best of luck with your startup journey. Come back anytime! 🌟"
        
        else:
            response = "Hello! I'm your startup funding advisor. Ask me about investors, funding, or government schemes for Indian startups."
        
        return {
            "answer": response,
            "sources": [],
            "language": language,
            "mode": "conversational"
        }
    
    async def generate_investor_recommendation(
        self,
        startup_profile: Dict,
        investors: List[Dict]
    ) -> Dict:
        """Generate investor recommendations"""
        if not startup_profile or not investors:
            return {"recommendation": "Please provide startup profile and investor information."}
        
        try:
            prompt = f"""You are an expert VC matchmaker for Indian startups.

**STARTUP PROFILE**:
- Sector: {startup_profile.get('sector', 'Not specified')}
- Stage: {startup_profile.get('stage', 'Not specified')}
- Location: {startup_profile.get('location', 'Not specified')}
- Funding Need: ₹{startup_profile.get('funding_needed', 0)} Cr
- Description: {startup_profile.get('description', 'Not provided')}

**AVAILABLE INVESTORS**:
{self._format_investors(investors)}

**TASK**: Rank top 5 investors and explain why they match.

**FORMAT**:
**1. [Investor Name]** (Match: X/10)
- Why they fit: [2-3 specific reasons]
- Approach strategy: [how to reach them]

**2. [Investor Name]**...

Provide ranked recommendations:"""
            
            response = await self._call_gemini(prompt)
            return {"recommendation": response}
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return {"recommendation": "Error generating recommendations. Please try again."}
    
    def _format_investors(self, investors: List[Dict]) -> str:
        """Format investor list"""
        formatted = []
        for inv in investors[:10]:  # Limit to 10
            name = inv.get('name', 'Unknown')
            focus = ', '.join(inv.get('focus_areas', [])[:3]) or 'Not specified'
            ticket = f"₹{inv.get('ticket_size_min', 'N/A')}-{inv.get('ticket_size_max', 'N/A')}Cr"
            location = inv.get('location', 'Not specified')
            
            formatted.append(f"• {name}: {focus} | {ticket} | {location}")
        
        return "\n".join(formatted)
    
    async def analyze_funding_trends(self, deals_data: List[Dict], timeframe: str) -> Dict:
        """Analyze funding trends"""
        if not deals_data:
            return {"analysis": "No data available for analysis."}
        
        try:
            summary = self._format_deals_data(deals_data)
            
            prompt = f"""Analyze this Indian startup funding data for {timeframe}:

{summary}

Provide:
1. **Key Trends**: Major patterns and changes
2. **Sector Analysis**: Which sectors are hot/cold
3. **Stage Distribution**: Where capital is flowing
4. **Actionable Insights**: What founders should know

Be specific with numbers and practical:"""
            
            response = await self._call_gemini(prompt)
            return {"analysis": response}
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return {"analysis": "Error analyzing trends."}
    
    def _format_deals_data(self, deals: List[Dict]) -> str:
        """Format deals for analysis"""
        total = sum(float(d.get('amount', 0)) for d in deals)
        avg = total / len(deals) if deals else 0
        
        summary = f"**Total**: {len(deals)} deals, ₹{total:.1f}Cr total, ₹{avg:.1f}Cr average\n\n**Sample Deals**:\n"
        
        for deal in deals[:10]:
            summary += f"• {deal.get('startup_name', 'Unknown')}: ₹{deal.get('amount', 0)}Cr ({deal.get('stage', 'Unknown')}) - {deal.get('sector', 'Unknown')}\n"
        
        return summary

    async def generate_simple_response(self, prompt: str) -> str:
        """
        Generate a simple response from the LLM given a prompt
        Used by external modules like investors.py for AI summaries
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated response text
        """
        try:
            response = await self._call_gemini(prompt, temperature=0.5)
            return response
        except Exception as e:
            logger.error(f"Error generating simple response: {str(e)}")
            return ""


# Singleton instance
try:
    llm_service = LLMService()
    logger.info("✅ LLM Service singleton initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize llm_service: {e}")
    llm_service = None
