import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragplatform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # LLM
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_PRICE_PROMPT_PER_1K: float = 0.00015
    LLM_PRICE_COMPLETION_PER_1K: float = 0.0006

    # Reranker
    COHERE_API_KEY: str = ""
    RERANKER_TYPE: str = "cohere"  # "cohere" or "cross_encoder"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Retrieval
    DEFAULT_TOP_K: int = 20
    DEFAULT_TOP_N: int = 5
    RRF_K: int = 60
    RERANK_SCORE_THRESHOLD: float = 0.3

    # Chunking
    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_CHUNK_OVERLAP: int = 50
    DEFAULT_CHUNKING_STRATEGY: str = "semantic"
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.75

    # Rate Limiting
    DEFAULT_RATE_LIMIT_QPM: int = 60

    # Cache
    QUERY_CACHE_TTL_SECONDS: int = 300

    # Admin
    ADMIN_API_KEY: str = "admin-secret-key-change-me"

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_secrets(self) -> None:
        """Raise on startup if default secrets are used in production."""
        env = os.getenv("APP_ENV", "development").lower()
        if env not in ("development", "dev", "test"):
            insecure_defaults = {
                "ADMIN_API_KEY": "admin-secret-key-change-me",
            }
            for field, default_val in insecure_defaults.items():
                if getattr(self, field, None) == default_val:
                    raise ValueError(
                        f"Insecure default detected for {field}. "
                        f"Set a unique value via environment variable before running in {env} mode."
                    )


settings = Settings()
settings.validate_secrets()
