"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    OPENROUTER_API_KEY: str
    LLAMA_CLOUD_API_KEY: str  # NEW: For LlamaParse
    HUGGINGFACE_HUB_TOKEN: str  # NEW: For IndicTrans2 models
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_TIMEOUT_SECONDS: int = 30
    QDRANT_UPSERT_BATCH_SIZE: int = 64
    JINA_API_KEY: str
    
    # IndicTrans2 Settings (NEW)
    INDICTRANS2_MODEL_DIR: str = "./models/indictrans2"
    INDICTRANS2_DEVICE: str = "cuda"  # or "cpu"

    # Model Settings
    OPENROUTER_MODEL: str = "openrouter/free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = "http://localhost:3000"
    OPENROUTER_APP_NAME: str = "DealFlow AI"
    LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
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
        extra = "ignore"


settings = Settings()
