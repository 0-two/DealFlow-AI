"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GOOGLE_API_KEY: str
    BHASHINI_API_KEY: str
    BHASHINI_USER_ID: str
    BHASHINI_API_KEY_ULC: str
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: str
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str
    JINA_API_KEY: str

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
