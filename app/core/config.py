from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Iksan AI Interview Backend"
    API_V1_STR: str = "/api/v1"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    # DEPRECATED: Storage bucket not currently in use - kept for future implementation
    SUPABASE_STORAGE_BUCKET: str
    
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
            "text/markdown",
            "text/plain"
        ]
    )
    
    # Rate Limiting Configuration
    # Format: "X/period" where period can be: second, minute, hour, day
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"  # Default limit for most endpoints
    RATE_LIMIT_AUTH: str = "5/minute"  # Strict limit for auth endpoints (login, register)
    RATE_LIMIT_LLM: str = "10/minute"  # Limit for LLM-heavy endpoints (initiate, submit)
    RATE_LIMIT_HEALTH: str = "120/minute"  # Relaxed limit for health checks
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
