"""
Enhanced LLM Service with Intelligent Hybrid RAG
Combines document retrieval with general knowledge for better responses
"""
from openai import AsyncOpenAI
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
        """Initialize the OpenRouter chat client."""
        try:
            if not settings.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY not configured in settings")

            self.client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                    "X-Title": settings.OPENROUTER_APP_NAME,
                },
            )
            logger.info("LLM service initialized with OpenRouter model: %s", settings.OPENROUTER_MODEL)
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
            
            GUARDRAILS: Decide whether the request is within the startup, funding,
            investor, business, entrepreneurship, or government-scheme domain. For
            unrelated, unsafe, illegal, or harmful requests, refuse briefly in your
            own words and suggest a relevant question instead.

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
            response = await self._call_llm(prompt, temperature=0.25)
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
            
            GUARDRAILS: Decide whether the request is within the startup, funding,
            investor, business, entrepreneurship, or government-scheme domain. For
            unrelated, unsafe, illegal, or harmful requests, refuse briefly in your
            own words and suggest a relevant question instead.

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
            response = await self._call_llm(prompt, temperature=0.3)
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
            
            GUARDRAILS: Decide whether the request is within the startup, funding,
            investor, business, entrepreneurship, or government-scheme domain. For
            unrelated, unsafe, illegal, or harmful requests, refuse briefly in your
            own words and suggest a relevant question instead.

            USER QUESTION: {query}

            FORMATTING RULES:
            - Use clear "## Section Headers" with a blank line before them.
            - Use standard Markdown bullets "- " for lists.
            - Keep the text clean and professional.

            YOUR DETAILED EXPERT GUIDANCE:
        """).strip()
        
        try:
            response = await self._call_llm(prompt, temperature=0.5)
            return {"answer": response, "sources": [], "language": language, "mode": "general"}
        except Exception as e:
            logger.error(f"General knowledge error: {e}")
            return {"answer": "Error generating response.", "sources": [], "language": language}
    
    async def _call_llm(self, prompt: str, temperature: float = 0.4) -> str:
        """Call OpenRouter with error handling."""
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=settings.MAX_TOKENS,
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                raise ValueError("Empty response from OpenRouter")
            return content.strip()
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

    async def stream_answer(self, query: str, context: str, sources: List[Dict], language: str = "en") -> AsyncIterator[str]:
        """Stream answer with cleaned prompts. Returns metadata about expertise."""
        formatted_sources = self._format_sources(sources)
        context_quality = self._assess_context_quality(query, context, sources)
        
        # Select Prompt based on quality
        if context_quality >= 7:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor and conversational assistant.
                Answer in this language: {language}

                GUARDRAILS: Answer only questions related to startups, entrepreneurship,
                investors, fundraising, business, or government schemes. For unrelated,
                unsafe, illegal, or harmful requests, briefly explain that you cannot help
                and suggest a relevant startup or funding topic instead. Decide this from
                the user's actual request; do not use a hardcoded response.
                
                CONTEXT: {context}
                SOURCES: {formatted_sources}
                USER QUESTION: {query}
                
                Return clean Markdown. Use a blank line before headings, standard
                Markdown bullets, and normal word spacing. Never insert spaces inside
                words. Answer greetings and casual messages naturally using the model.
            """).strip()
            temp = 0.25
        elif context_quality >= 4:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor and conversational assistant.
                Answer in this language: {language}

                GUARDRAILS: Answer only questions related to startups, entrepreneurship,
                investors, fundraising, business, or government schemes. For unrelated,
                unsafe, illegal, or harmful requests, briefly explain that you cannot help
                and suggest a relevant startup or funding topic instead. Decide this from
                the user's actual request; do not use a hardcoded response.
                
                CONTEXT: {context}
                SOURCES: {formatted_sources}
                USER QUESTION: {query}
                
                Combine context and general knowledge. Return clean Markdown with normal
                word spacing and blank lines around headings. Answer casual messages
                naturally using the model.
            """).strip()
            temp = 0.3
        else:
            prompt = textwrap.dedent(f"""
                You are an expert startup funding advisor and conversational assistant.
                Answer in this language: {language}

                GUARDRAILS: Answer only questions related to startups, entrepreneurship,
                investors, fundraising, business, or government schemes. For unrelated,
                unsafe, illegal, or harmful requests, briefly explain that you cannot help
                and suggest a relevant startup or funding topic instead. Decide this from
                the user's actual request; do not use a hardcoded response.
                USER QUESTION: {query}
                
                Return clean Markdown with normal word spacing and blank lines around
                headings. Answer casual messages naturally using the model.
            """).strip()
            temp = 0.5

        # Stream the response
        try:
            async for token in self._stream_llm(prompt, temperature=temp):
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

    async def _stream_llm(self, prompt: str, temperature: float = 0.4) -> AsyncIterator[str]:
        """Stream tokens from OpenRouter."""
        response = await self.client.chat.completions.create(
            model=settings.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=settings.MAX_TOKENS,
            stream=True,
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content
            if text:
                yield text
    
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

    async def generate_simple_response(self, prompt: str) -> str:
        try:
            response = await self._call_llm(prompt, temperature=0.5)
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