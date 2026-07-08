"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GOOGLE_API_KEY: str
    LLAMA_CLOUD_API_KEY: str  # NEW: For LlamaParse
    HUGGINGFACE_HUB_TOKEN: str  # NEW: For IndicTrans2 models
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: str
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str
    JINA_API_KEY: str
    
    # Bhashini settings
    BHASHINI_API_KEY: Optional[str] = None
    BHASHINI_USER_ID: Optional[str] = None
    BHASHINI_API_KEY_ULC: Optional[str] = None
    
    # IndicTrans2 Settings (NEW)
    INDICTRANS2_MODEL_DIR: str = "./models/indictrans2"
    INDICTRANS2_DEVICE: str = "cuda"  # or "cpu"

    # Model Settings
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2048

    # Vector DB Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 7

    # Performance/Safety Flags
    USE_SOURCE_VERIFICATION: bool = False
    RETRIEVAL_PER_COLLECTION: int = 6
    VERIFY_TOP_SOURCES: int = 3
    RAG_CONTEXT_CHARS_PER_DOC: int = 1000

    # Caching
    CACHE_ENABLED: bool = True
    SEARCH_CACHE_TTL_SECONDS: int = 60
    SEARCH_CACHE_MAX_ENTRIES: int = 512
    RERANK_CACHE_TTL_SECONDS: int = 60

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
