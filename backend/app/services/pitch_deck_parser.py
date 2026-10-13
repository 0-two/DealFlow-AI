from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
import io
import logging
from typing import Dict, Optional
from openai import AsyncOpenAI
from app.config.settings import settings
import tempfile
import os

logger = logging.getLogger(__name__)

class EnhancedPitchDeckParser:
    """
    Enhanced pitch deck parser using LlamaParse for superior PDF extraction
    """
    
    def __init__(self):
        # Initialize LlamaParse
        self.parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",  # Can be "markdown" or "text"
            num_workers=4,  # Process 4 pages in parallel
            verbose=True,
            language="en"  # Primary language
        )
        
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-Title": settings.OPENROUTER_APP_NAME,
            },
        )
        
        logger.info("Enhanced PitchDeckParser initialized with LlamaParse")
    
    async def parse_pitch_deck(self, pdf_content: bytes, filename: str = "pitch.pdf") -> Dict:
        """
        Extract structured information from pitch deck PDF using LlamaParse
        
        Args:
            pdf_content: PDF file bytes
            filename: Original filename
            
        Returns:
            Structured startup data dictionary
        """
        try:
            logger.info(f"Parsing pitch deck: {filename}")
            
            # Save PDF to temporary file (LlamaParse requires file path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_content)
                tmp_path = tmp_file.name
            
            try:
                # Parse PDF with LlamaParse
                logger.info("Extracting text with LlamaParse...")
                documents = self.parser.load_data(tmp_path)
                
                # Combine all document text
                full_text = "\n\n".join([doc.text for doc in documents])
                
                if not full_text or len(full_text) < 50:
                    raise ValueError("Insufficient text extracted from PDF")
                
                logger.info(f"Extracted {len(full_text)} characters from PDF")
                
                # Also extract metadata if available
                metadata = documents[0].metadata if documents else {}
                logger.info(f"PDF metadata: {metadata}")
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
            
            # Use Gemini to structure the information
            structured_data = await self._extract_structured_info(full_text)
            
            # Add parsing metadata
            structured_data["_parsing_metadata"] = {
                "pages": len(documents),
                "extraction_method": "LlamaParse",
                "text_length": len(full_text)
            }
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error parsing pitch deck: {e}")
            raise
    
    async def _extract_structured_info(self, text: str) -> Dict:
        """
        Use OpenRouter to extract structured information from parsed text
        Enhanced with better prompting for comprehensive extraction
        """
        
        prompt = f"""You are an expert venture capital analyst. Extract comprehensive structured information from this startup pitch deck.

PITCH DECK TEXT:
{text}

Extract and return a JSON object with these fields. Be thorough and extract as much detail as possible:

{{
    "startup_name": "company name",
    "founder_name": "founder(s) names (comma-separated if multiple)",
    "sector": "primary industry/sector (e.g., Fintech, Edtech, Healthtech)",
    "stage": "current funding stage (Pre-Seed/Seed/Series A/Series B/etc)",
    "location": "headquarters city and country",
    "funding_amount": <number in crores>,
    "description": "2-3 sentence company description",
    "problem_statement": "what problem they're solving (be specific)",
    "solution": "how they solve it (include key features/approach)",
    "market_size": "TAM/SAM/SOM if mentioned, or market opportunity description",
    "business_model": "how they make money (revenue streams, pricing)",
    "traction": "key metrics: revenue, users, growth rate, customers, MoM/YoY growth, partnerships",
    "team_size": <number of employees>,
    "revenue": <current annual revenue in crores, 0 if pre-revenue>,
    "unique_value_proposition": "what makes them different/better than competitors",
    "competitors": "main competitors or competitive landscape",
    "go_to_market_strategy": "how they acquire customers",
    "key_metrics": "important KPIs and their values",
    "use_of_funds": "how they plan to use the funding",
    "milestones": "achieved and upcoming milestones",
    "vision": "long-term vision and goals",
    "ask": "what exactly they're asking for (funding amount, support, etc)"
}}

EXTRACTION GUIDELINES:
1. Extract ALL available information - be comprehensive
2. For numbers, use only digits (no currency symbols or text)
3. Use "Not specified" for missing text fields
4. Use 0 for missing numeric fields
5. For traction, include ALL metrics mentioned (users, revenue, growth %, partnerships, etc)
6. Look for implicit information too (e.g., if they mention "1000 paying customers at ₹500/month", calculate revenue)
7. Infer intelligently from context when information isn't explicitly stated

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no explanations.
```json
{{
  ...
}}
```

JSON:"""
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048,
            )

            response_text = response.choices[0].message.content.strip()
            
            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            import json
            structured_data = json.loads(response_text)
            
            # Create comprehensive searchable content
            structured_data["content"] = self._create_searchable_content(structured_data, text)
            
            logger.info(f"Successfully extracted structured data for: {structured_data.get('startup_name')}")
            
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            
            # Fallback: return basic structure with raw text
            return self._create_fallback_structure(text)
            
        except Exception as e:
            logger.error(f"Error extracting structured info: {e}")
            return self._create_fallback_structure(text)
    
    def _create_searchable_content(self, data: Dict, original_text: str) -> str:
        """Create rich searchable content from structured data"""
        parts = []
        
        # Add all structured fields
        parts.append(f"Startup: {data.get('startup_name', 'Unknown')}")
        parts.append(f"Founder: {data.get('founder_name', 'Unknown')}")
        parts.append(f"Sector: {data.get('sector', 'Unknown')}")
        parts.append(f"Stage: {data.get('stage', 'Unknown')}")
        parts.append(f"Location: {data.get('location', 'Unknown')}")
        parts.append(f"Funding Amount: ₹{data.get('funding_amount', 0)} Cr")
        
        # Add detailed descriptions
        if data.get('description'):
            parts.append(f"Description: {data['description']}")
        if data.get('problem_statement'):
            parts.append(f"Problem: {data['problem_statement']}")
        if data.get('solution'):
            parts.append(f"Solution: {data['solution']}")
        if data.get('business_model'):
            parts.append(f"Business Model: {data['business_model']}")
        if data.get('traction'):
            parts.append(f"Traction: {data['traction']}")
        if data.get('unique_value_proposition'):
            parts.append(f"UVP: {data['unique_value_proposition']}")
        if data.get('market_size'):
            parts.append(f"Market: {data['market_size']}")
        if data.get('key_metrics'):
            parts.append(f"Metrics: {data['key_metrics']}")
        
        # Also include snippet of original text for better semantic search
        parts.append(f"Raw Content: {original_text[:500]}")
        
        return " | ".join(parts)
    
    def _create_fallback_structure(self, text: str) -> Dict:
        """Create minimal structure when parsing fails"""
        logger.warning("Using fallback structure")
        
        # Try to extract startup name from first lines
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        potential_name = lines[0] if lines else "Unknown Startup"
        
        return {
            "startup_name": potential_name,
            "founder_name": "Not specified",
            "description": text[:500] if text else "No description available",
            "content": text[:1000] if text else "",
            "sector": "Not specified",
            "stage": "Not specified",
            "location": "Not specified",
            "funding_amount": 0,
            "revenue": 0,
            "team_size": 0,
            "problem_statement": "Not specified",
            "solution": "Not specified",
            "market_size": "Not specified",
            "business_model": "Not specified",
            "traction": "Not specified",
            "unique_value_proposition": "Not specified",
            "competitors": "Not specified",
            "_fallback": True
        }

# Singleton instance
pitch_deck_parser = EnhancedPitchDeckParser()
