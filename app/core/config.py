from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import secrets
from urllib.parse import urlparse

class Settings(BaseSettings):
    PROJECT_NAME: str = "Iksan AI Interview Backend"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = Field(default=False)
    
    # Supabase (DEPRECATED - kept during migration phase)
    # Will be removed once SQLAlchemy migration is complete
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # DEPRECATED: Storage bucket not currently in use - kept for future implementation
    SUPABASE_STORAGE_BUCKET: str = ""
    
    # PostgreSQL Direct Connection (SQLAlchemy)
    # Format: postgresql+asyncpg://user:password@host:port/database
    DATABASE_URL: str = Field(default="")
    DATABASE_POOL_SIZE: int = 5  # Number of connections to maintain in the pool
    DATABASE_MAX_OVERFLOW: int = 10  # Max additional connections beyond pool_size
    DATABASE_POOL_TIMEOUT: int = 30  # Seconds to wait for a connection from pool
    
    # JWT Configuration (Custom Auth)
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 1 week
    JWT_ISSUER: str = "iksan-ai-interview"
    JWT_AUDIENCE: str = "iksan-ai-interview-api"
    
    # LLM Configuration
    # TODO: Set these values in .env when integrating with actual LLM provider
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.5-flash"  # Default model, can be overridden
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB default
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]
    )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
        
    # Rate Limiting Configuration
    # Format: "X/period" where period can be: second, minute, hour, day
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"  # Default limit for most endpoints
    RATE_LIMIT_AUTH: str = "5/minute"  # Strict limit for auth endpoints (login, register)
    RATE_LIMIT_LLM: str = "10/minute"  # Limit for LLM-heavy endpoints (initiate, submit)
    RATE_LIMIT_HEALTH: str = "120/minute"  # Relaxed limit for health checks
    

    DEEPGRAM_API_KEY: str
    GEMINI_API_KEY: str
    DB_PASSWORD: str
    
    REDIS_URL: str

    JOB_PROCESSING_INTERVAL_SECONDS: int = 7

    ELICE_API_KEY: str
    GPT_API_BASE_URL: str

    RAG_DB_CONN_STRING: str
    GPT_EMBED_BASE_URL: str

    WHISPER_BASE_URL: str
    MOCK_GPT: str

    # Student Registration
    STUDENT_PASSWORD_SALT: str = "iksan_student_pwd_"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


    # --- Computed Redis Properties (Parses REDIS_URL) ---
    @property
    def redis_host(self) -> str:
        """Parses the host from REDIS_URL."""
        try:
            url = urlparse(self.REDIS_URL)
            return url.hostname or "localhost"
        except Exception:
            return "localhost"

    @property
    def redis_port(self) -> int:
        """Parses the port from REDIS_URL."""
        try:
            url = urlparse(self.REDIS_URL)
            return url.port or 6379
        except Exception:
            return 6379

    @property
    def redis_password(self) -> Optional[str]:
        """Parses the password from REDIS_URL."""
        try:
            url = urlparse(self.REDIS_URL)
            return url.password
        except Exception:
            return None
settings = Settings()
