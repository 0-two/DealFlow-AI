"""
Application Constants
"""
from enum import Enum

# Supported Indic Languages Mapping
INDIC_LANGUAGES = {
    "hi": {"name": "Hindi", "code": "hi", "script": "Devanagari"},
    "bn": {"name": "Bengali", "code": "bn", "script": "Bengali"},
    "te": {"name": "Telugu", "code": "te", "script": "Telugu"},
    "mr": {"name": "Marathi", "code": "mr", "script": "Devanagari"},
    "ta": {"name": "Tamil", "code": "ta", "script": "Tamil"},
    "ur": {"name": "Urdu", "code": "ur", "script": "Arabic"},
    "gu": {"name": "Gujarati", "code": "gu", "script": "Gujarati"},
    "kn": {"name": "Kannada", "code": "kn", "script": "Kannada"},
    "ml": {"name": "Malayalam", "code": "ml", "script": "Malayalam"},
    "pa": {"name": "Punjabi", "code": "pa", "script": "Gurmukhi"},
    "or": {"name": "Odia", "code": "or", "script": "Odia"},
    "as": {"name": "Assamese", "code": "as", "script": "Assamese"},
    "en": {"name": "English", "code": "en", "script": "Latin"},
}

# Bhashini API Endpoints
BHASHINI_API_ENDPOINTS = {
    "translate": "https://api.bhashini.gov.in/services/ai4bharat/translation/v2",
    "transliterate": "https://api.bhashini.gov.in/services/ai4bharat/transliteration/v2",
    "asr": "https://api.bhashini.gov.in/services/ai4bharat/asr/v2",
    "tts": "https://api.bhashini.gov.in/services/ai4bharat/tts/v2",
    "ulca_translate": "https://api.bhashini.gov.in/services/ulca/translate",
    "ulca_transliterate": "https://api.bhashini.gov.in/services/ulca/transliterate",
}

# Weaviate Collection Names
WEAVIATE_COLLECTIONS = {
    "deals": "Deal",
    "investors": "Investor",
    "documents": "Document",
    "trends": "Trend",
    "companies": "Company",
}

# System Prompts for Gemini - Aligned with Multilingual RAG-based Startup Funding Intelligence System
GEMINI_SYSTEM_PROMPTS = {
    "general": """You are DealFlow AI - a Multilingual RAG-based Startup Funding Intelligence System.
    Your mission is to democratize access to startup funding information for Indian entrepreneurs.
    Use ONLY the provided context to answer. Cite sources using [Source N] format.
    If context is insufficient, clearly state what information is missing.
    Never hallucinate - accuracy is paramount for funding decisions.""",
    
    "trend_analysis": """You are DealFlow AI's Trend Analysis Module - identifying patterns in Indian startup funding data.
    Analyze the provided documents to surface:
    - Sector-wise funding trends and emerging verticals
    - Stage-wise investment patterns (Seed vs Series A vs Growth)
    - Geographic distribution of deals
    - Seasonal patterns and market cycles
    Present analysis with specific data points, charts descriptions, and actionable insights for founders.""",
    
    "investor_search": """You are DealFlow AI's Investor Intelligence Module - helping founders find the right investors.
    From the provided context, extract and present:
    - Investor names, types (VC/Angel/Accelerator/Corporate VC)
    - Focus sectors and stage preferences
    - Typical ticket sizes and recent investments
    - Portfolio companies and notable exits
    - Contact information and outreach recommendations
    Always cite sources and indicate when information may be outdated.""",
    
    "deal_analysis": """You are DealFlow AI's Deal Analysis Module - breaking down funding transactions.
    Analyze deal information to provide:
    - Deal terms, valuation, and structure
    - Investors involved and their participation
    - Comparison with sector benchmarks
    - Implications for the startup and market
    Use precise figures from documents and cite all sources.""",
    
    "query_response": """You are DealFlow AI - a RAG-based Startup Funding Intelligence System for Indian entrepreneurs.
    Answer queries using the provided context documents with strict source citation.
    Focus on: investors, funding trends, government policies, and actionable advice.
    If the query is in an Indic language, respond in the same language.
    Prioritize accuracy and helpfulness for founders making funding decisions.""",
}

# Query Types
class QueryType(str, Enum):
    """Query types for different use cases"""
    INVESTOR_SEARCH = "investor_search"
    TREND_ANALYSIS = "trend_analysis"
    GENERAL_QUERY = "general_query"
    DEAL_ANALYSIS = "deal_analysis"


# Document Types
class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MARKDOWN = "md"


# Language Codes
class LanguageCode(str, Enum):
    """Supported language codes"""
    ENGLISH = "en"
    HINDI = "hi"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    URDU = "ur"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
