"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://news_user:news_password@localhost/news_db"
    
    # AI Settings
    AI_API_KEY: Optional[str] = None
    AI_API_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4-turbo-preview"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHANNEL_ID: Optional[str] = None
    
    # Logo
    LOGO_PATH: str = "/app/static/images/logo.png"
    LOGO_POSITION: str = "bottom-right"
    LOGO_OPACITY: float = 0.7
    
    # Parser
    PARSER_INTERVAL: int = 300
    MAX_POSTS_PER_RUN: int = 10
    
    # Storage
    UPLOAD_FOLDER: str = "/app/static/uploads"
    IMAGES_FOLDER: str = "/app/static/images"
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
