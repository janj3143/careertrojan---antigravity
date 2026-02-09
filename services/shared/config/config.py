from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "CareerTrojan"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Paths
    CAREERTROJAN_DATA_ROOT: str = r"L:\antigravity_version_ai_data_final"
    AI_DATA_PATH: Optional[str] = None
    PARSER_OUTPUT_PATH: Optional[str] = None
    
    # Flags
    ENABLE_AI_ENRICHMENT: bool = True
    ENABLE_MASQUERADE: bool = True
    
    class Config:
        env_file = ".env"

config = Settings()
