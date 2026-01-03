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

# System Prompts for Gemini
GEMINI_SYSTEM_PROMPTS = {
    "general": """You are a helpful AI assistant that answers questions based on the provided context documents. 
    Use only the information from the context to answer. If the context doesn't contain enough information, 
    say so clearly. Always cite which document(s) you used for your answer.""",
    
    "trend_analysis": """You are an expert data analyst specializing in identifying trends and patterns in investment and business data. 
    Analyze the provided documents and identify key trends, patterns, and insights. 
    Present your analysis in a clear and structured manner with specific examples and data points.""",
    
    "investor_search": """You are an AI assistant specialized in helping users find and understand investor information. 
    Based on the provided context, provide detailed and accurate information about investors, their investment focus, 
    portfolio companies, and investment criteria. Be specific and include relevant details.""",
    
    "deal_analysis": """You are a financial analyst AI assistant. Analyze deal information from the provided documents, 
    including deal terms, valuation, investors involved, and key business metrics. 
    Provide structured analysis with clear insights and recommendations.""",
    
    "query_response": """You are a knowledgeable AI assistant for deal flow management and analysis. 
    Answer questions accurately using the provided context. If you're unsure about any information, 
    indicate that clearly. Format your responses in a clear and professional manner.""",
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
