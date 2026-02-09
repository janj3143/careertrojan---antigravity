import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "CareerTrojan Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Data Paths
    CAREERTROJAN_DATA_ROOT: str
    CAREERTROJAN_WORKING_ROOT: str
    
    # Database (Optional for Phase 3 start, required for persistence)
    DATABASE_URL: str = "postgresql://user:pass@postgres:5432/careertrojan"
    REDIS_URL: str = "redis://redis:6379/0"

    # Feature Flags
    ALLOW_MOCK_DATA: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
