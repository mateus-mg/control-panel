from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    APP_NAME: str = "Control Panel"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme-in-production-12345")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Admin credentials (hashed password)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    
    DATABASE_URL: str = "sqlite:///./web-panel.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()