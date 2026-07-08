"""
Enhanced LLM Service with Intelligent Hybrid RAG
Combines document retrieval with general knowledge for better responses
"""
import google.generativeai as genai
from typing import List, Dict, Optional, AsyncIterator
import logging
import asyncio
import time
import re
import textwrap
from app.config.settings import settings

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
            
            # Added top_k and lowered temperature slightly for better formatting stability
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": 0.25,  # Lowered for more structured output
                    "max_output_tokens": settings.MAX_TOKENS,
                    "top_p": 0.9,
                    "top_k": 40,         # Added for token selection stability
                }
            )
            
            logger.info("✅ LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}", exc_info=True)
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Post-process text to fix common Markdown formatting errors.
        Fixes issues where headers or bullets don't have newlines before them.
        """
        if not text:
            return ""
            
        # 1. Ensure newlines before headers (e.g., "text. ## Header" -> "text.\n\n## Header")
        text = re.sub(r'([^\n])\s*(#{2,})', r'\1\n\n\2', text)
        
        # 2. Ensure newlines before bullet points if they are stuck to text
        # (e.g., "text. - Item" -> "text.\n- Item")
        text = re.sub(r'([^\n])\s*(\n-\s)', r'\1\n\2', text)
        
        # 3. Fix double spaces or weird spacing artifacts (basic cleanup)
        text = re.sub(r'  +', ' ', text)
        
        return text.strip()

    async def generate_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict],
        language: str = "en"
    ) -> Dict:
        """
        Generate intelligent answer using hybrid approach
        """
        if not query or not query.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "language": language
            }
        
        # Refuse out-of-domain questions early
        if self._is_out_of_domain_query(query):
            refusal = (
                "I'm specialized in startup funding and entrepreneurship. "
                "This question is outside my scope of expertise. Please ask me about startups, investors, funding, or government schemes."
            )
            return {"answer": refusal, "sources": [], "language": language, "mode": "refusal"}
        
        # Handle simple conversational queries
        if self._is_simple_conversational_query(query):
            return await self._generate_simple_response(query, language)
        
        try:
            # Check context relevance
            context_quality = self._assess_context_quality(query, context, sources)
            
            # Choose response strategy based on context quality
            if context_quality >= 7:
                result = await self._generate_rag_answer(query, context, sources, language)
            elif context_quality >= 4:
                result = await self._generate_hybrid_answer(query, context, sources, language)
            else:
                result = await self._generate_general_answer(query, language)
            
            # Apply cleaning to the final answer
            result['answer'] = self._clean_text(result['answer'])
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return {
                "answer": "I encountered an error. Please try rephrasing your question.",
                "sources": [],
                "language": language
            }
    
    def _assess_context_quality(self, query: str, context: str, sources: List[Dict]) -> int:
        """Assess if retrieved context is relevant to the query"""
        if not context or not context.strip() or not sources:
            return 0
        
        # Simple keyword matching logic (kept from original)
        query_lower = query.lower()
        key_terms = [
            'investor', 'vc', 'angel', 'funding', 'series', 'seed', 'capital', 
            'fintech', 'edtech', 'healthtech', 'saas', 'india', 'indian', 'bangalore', 
            'startup', 'valuation', 'equity', 'rupees', 'crore'
        ]
        
        # Check for relevant terms in query
        active_terms = [t for t in key_terms if t in query_lower]
        
        if not active_terms:
            return 5
        
        context_lower = context.lower()
        matches = sum(1 for term in active_terms if term in context_lower)
        
        match_ratio = matches / len(active_terms)
        base_score = int(match_ratio * 10)
        
        if len(sources) >= 3 and matches >= len(active_terms) * 0.5:
            base_score += 2
            
        return min(base_score, 10)
    
    async def _generate_rag_answer(self, query: str, context: str, sources: List[Dict], language: str) -> Dict:
        """Generate answer using pure RAG"""
        formatted_sources = self._format_sources(sources)
        
        # Use dedent to remove python indentation from the prompt string
        prompt = textwrap.dedent(f"""
            You are an expert startup funding advisor with deep knowledge of the Indian startup ecosystem.
            Answer in this language: {language}

            SCOPE: You ONLY answer questions about startups, funding, investors, government schemes, business, entrepreneurship, and related topics in India.
            
            CRITICAL RULE: If the question is NOT related to startups, funding, investors, government schemes, or entrepreneurship, you MUST refuse to answer.
            Say: "I'm specialized in startup funding and entrepreneurship. This question is outside my scope of expertise. Please ask me about startups, investors, funding, or government schemes."
            
            Do NOT answer questions about weapons, firearms, cooking, sports, movies, or any unrelated topics.

            TASK: Answer only using the provided context documents. 
            
            FORMATTING RULES:
            - Use clear "## Section Headers" with a blank line before them.
            - Use standard Markdown bullets "- " for lists.
            - Do not put odd spaces inside words (e.g. write "Prominence", not "Prom inence").
            
            CONTEXT FROM DOCUMENTS:
            {context}

            SOURCES:
            {formatted_sources}

            USER QUESTION: {query}

            YOUR DETAILED ANSWER:
        """).strip()
        
        try:
            response = await self._call_gemini(prompt, temperature=0.25)
            cited_sources = self._extract_citations(response, sources)
            return {"answer": response, "sources": cited_sources, "language": language, "mode": "rag"}
        except Exception as e:
            logger.error(f"RAG generation error: {e}")
            return await self._generate_hybrid_answer(query, context, sources, language)
    
    async def _generate_hybrid_answer(self, query: str, context: str, sources: List[Dict], language: str) -> Dict:
        """Generate answer combining retrieved docs with general knowledge"""
        formatted_sources = self._format_sources(sources)
        
        prompt = textwrap.dedent(f"""
            You are an expert startup funding advisor for Indian entrepreneurs.
            Answer in this language: {language}

            SCOPE: You ONLY answer questions about startups, funding, investors, government schemes, business, entrepreneurship, and related topics in India.
            
            CRITICAL RULE: If the question is NOT related to startups, funding, investors, government schemes, or entrepreneurship, you MUST refuse to answer.
            Say: "I'm specialized in startup funding and entrepreneurship. This question is outside my scope of expertise. Please ask me about startups, investors, funding, or government schemes."
            
            Do NOT answer questions about weapons, firearms, cooking, sports, movies, or any unrelated topics.

            USER QUESTION: {query}

            AVAILABLE CONTEXT:
            {context}

            SOURCES: {formatted_sources}

            TASK: Combine relevant parts from the documents with your general knowledge.
            
            FORMATTING RULES:
            - Ensure there is a blank line before every "## Header".
            - Use standard Markdown bullets "- " for lists.
            - Write naturally without breaking words with spaces.
            
            YOUR COMPREHENSIVE ANSWER:
        """).strip()
        
        try:
            response = await self._call_gemini(prompt, temperature=0.3)
            cited_sources = self._extract_citations(response, sources) if sources else []
            return {"answer": response, "sources": cited_sources[:5], "language": language, "mode": "hybrid"}
        except Exception as e:
            logger.error(f"Hybrid generation error: {e}")
            return await self._generate_general_answer(query, language)
    
    async def _generate_general_answer(self, query: str, language: str) -> Dict:
        """Generate answer using general knowledge"""
        prompt = textwrap.dedent(f"""
            You are an expert startup funding advisor specializing in the Indian startup ecosystem.
            Answer in this language: {language}

            SCOPE: You ONLY answer questions about startups, funding, investors, government schemes, business, entrepreneurship, and related topics in India.
            
            CRITICAL RULE: If the question is NOT related to startups, funding, investors, government schemes, or entrepreneurship, you MUST refuse to answer.
            Say: "I'm specialized in startup funding and entrepreneurship. This question is outside my scope of expertise. Please ask me about startups, investors, funding, or government schemes."
            
            Do NOT answer questions about weapons, firearms, cooking, sports, movies, or any unrelated topics.

            USER QUESTION: {query}

            FORMATTING RULES:
            - Use clear "## Section Headers" with a blank line before them.
            - Use standard Markdown bullets "- " for lists.
            - Keep the text clean and professional.

            YOUR DETAILED EXPERT GUIDANCE:
        """).strip()
        
        try:
            response = await self._call_gemini(prompt, temperature=0.5)
            return {"answer": response, "sources": [], "language": language, "mode": "general"}
        except Exception as e:
            logger.error(f"General knowledge error: {e}")
            return {"answer": "Error generating response.", "sources": [], "language": language}
    
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

    async def stream_answer(self, query: str, context: str, sources: List[Dict], language: str = "en") -> AsyncIterator[str]:
        """Stream answer with cleaned prompts. Returns metadata about expertise."""
        # Refuse out-of-domain questions early
        if self._is_out_of_domain_query(query):
            refusal = (
                "I'm specialized in startup funding and entrepreneurship. "
                "This question is outside my scope of expertise. Please ask me about startups, investors, funding, or government schemes."
            )
            yield refusal
            return

        # Conversational fast path
        if self._is_simple_conversational_query(query):
            simple = (await self._generate_simple_response(query, language)).get("answer", "Hello")
            yield simple
            return

        formatted_sources = self._format_sources(sources)
        context_quality = self._assess_context_quality(query, context, sources)
        
        # Select Prompt based on quality
        if context_quality >= 7:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor.
                Answer in this language: {language}
                
                CONTEXT: {context}
                SOURCES: {formatted_sources}
                USER QUESTION: {query}
                
                Strictly format with Markdown. Ensure newlines before headers.
            """).strip()
            temp = 0.25
        elif context_quality >= 4:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor.
                Answer in this language: {language}
                
                CONTEXT: {context}
                SOURCES: {formatted_sources}
                USER QUESTION: {query}
                
                Combine context and general knowledge. Strictly format with Markdown.
            """).strip()
            temp = 0.25
        else:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor.
                Answer in this language: {language}
                USER QUESTION: {query}
                
                Strictly format with Markdown. Ensure newlines before headers.
            """).strip()
            temp = 0.25

        # Stream the response
        try:
            async for token in self._stream_gemini(prompt, temperature=temp):
                # Note: We cannot easily regex clean a stream in real-time without buffering
                # So we rely on the improved prompt structure here.
                yield token
        except Exception as e:
            yield f"[stream_error] {str(e)}"

    def _is_out_of_expertise(self, answer: str) -> bool:
        """
        Detect if the LLM indicates it cannot help with the query.
        Checks for:
        1. Explicit refusal phrases
        2. Domain relevance - is the answer about startup/funding/investors?
        """
        if not answer or not answer.strip():
            return True
            
        answer_lower = answer.lower()
        
        # Check for explicit refusal phrases
        out_of_scope_phrases = [
            "i cannot help",
            "i'm not able to",
            "i don't have expertise",
            "i'm not qualified",
            "this is outside",
            "this is beyond",
            "i cannot assist",
            "i'm unable to assist",
            "this is outside my expertise",
            "beyond my expertise",
            "out of my scope",
            "not within my scope",
            "cannot provide information",
            "i apologize, but i cannot",
            "unfortunately, i cannot",
            "i'm not designed to",
            "this question is",
            "this topic is beyond",
        ]
        
        for phrase in out_of_scope_phrases:
            if phrase in answer_lower:
                return True
        
        # Check for domain relevance - startup/funding keywords
        domain_keywords = [
            'startup', 'investor', 'funding', 'vc', 'venture capital', 'seed',
            'series a', 'series b', 'pitch', 'equity', 'founder', 'entrepreneur',
            'business', 'investment', 'angel', 'accelerator', 'incubator',
            'government scheme', 'subsidy', 'grant', 'loan', 'fintech', 'edtech',
            'saas', 'india', 'indian', 'rupees', 'crore', 'valuation',
            'unicorn', 'ipo', 'exit', 'acquisition', 'capital raise',
            'pitch deck', 'business plan', 'roi', 'market', 'revenue',
        ]
        
        # Count how many domain keywords appear in the answer
        domain_matches = sum(1 for keyword in domain_keywords if keyword in answer_lower)
        
        # If answer has very few domain-relevant keywords, it's likely out of scope
        # But allow some general business answers (threshold of 1 match)
        if domain_matches == 0:
            # No startup/funding keywords found - likely out of domain
            return True
        
        return False

    def _is_out_of_domain_query(self, query: str) -> bool:
        """Heuristic to detect queries outside startup/funding domain using the query text."""
        if not query or not query.strip():
            return True
        q = query.lower()
        # Strong out-of-domain indicators
        negative_keywords = [
            'gun', 'guns', 'weapon', 'weapons', 'glock', 'rifle', 'pistol', 'knife',
            'cook', 'cooking', 'recipe', 'bake', 'baking', 'cake', 'bread', 'kitchen',
            'football', 'cricket', 'soccer', 'basketball', 'tennis', 'sport', 'sports',
            'movie', 'movies', 'film', 'films', 'actor', 'actress', 'celebrity',
            'song', 'music', 'guitar', 'piano', 'lyrics',
            'weather', 'temperature', 'forecast',
        ]
        for word in negative_keywords:
            if word in q:
                return True
        # If it has at least one domain keyword, consider in-domain
        domain_keywords = [
            'startup', 'investor', 'funding', 'vc', 'venture capital', 'seed',
            'series a', 'series b', 'equity', 'founder', 'entrepreneur', 'business',
            'investment', 'angel', 'accelerator', 'incubator', 'government scheme',
            'grant', 'loan', 'fintech', 'edtech', 'saas', 'valuation', 'unicorn',
            'ipo', 'pitch', 'pitch deck', 'market', 'revenue', 'capital', 'term sheet',
        ]
        if any(k in q for k in domain_keywords):
            return False
        # Default conservative: treat as out-of-domain if no domain keyword present
        return True

    async def _stream_gemini(self, prompt: str, temperature: float = 0.4) -> AsyncIterator[str]:
        """Stream tokens from Gemini"""
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

        loop.run_in_executor(None, worker)

        while True:
            item = await queue.get()
            if item is SENTINEL:
                break
            yield str(item)
    
    # ... (Keep the remaining helper methods: _format_sources, _extract_citations, 
    # _is_simple_conversational_query, _generate_simple_response, 
    # generate_investor_recommendation, analyze_funding_trends, _format_deals_data, 
    # _format_investors, generate_simple_response as they were in your original code) ...
    
    def _format_sources(self, sources: List[Dict]) -> str:
        if not sources: return "No sources available."
        formatted = []
        for i, source in enumerate(sources[:5], 1):
            title = source.get('title', source.get('name', 'Unknown'))
            snippet = source.get('snippet', source.get('content', ''))[:200]
            formatted.append(f"[Source {i}] {title}: {snippet}")
        return "\n".join(formatted)

    def _extract_citations(self, answer: str, sources: List[Dict]) -> List[Dict]:
        if not answer or not sources: return []
        cited = []
        for i, source in enumerate(sources, 1):
            if f"[Source {i}]" in answer or f"Source {i}" in answer:
                cited.append(source)
        return cited if cited else sources[:3]

    def _is_simple_conversational_query(self, query: str) -> bool:
        simple_queries = ["hi", "hello", "hey", "how are you", "thanks", "bye"]
        query_lower = query.lower().strip().rstrip('?!.')
        if query_lower in simple_queries: return True
        return False

    async def _generate_simple_response(self, query: str, language: str) -> Dict:
        return {
            "answer": "Hello! I'm your startup funding advisor. Ask me about investors, funding, or government schemes.",
            "sources": [],
            "language": language,
            "mode": "conversational"
        }
    
    async def generate_simple_response(self, prompt: str) -> str:
        try:
            response = await self._call_gemini(prompt, temperature=0.5)
            return response
        except Exception:
            return ""

# Singleton instance
try:
    llm_service = LLMService()
    logger.info("✅ LLM Service singleton initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize llm_service: {e}")
    llm_service = None