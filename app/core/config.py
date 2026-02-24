import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Arogya AI Hospital Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "development"
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Groq
    GROQ_API_KEY: str
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"WARNING: Could not load settings from .env file: {e}")
    # Fallback for CI/CD or initial setup if needed, strictly not recommended for prod secrets
    class MockSettings(Settings):
        GROQ_API_KEY: str = "mock_key"
        SMTP_HOST: str = "smtp.mock.com"
        SMTP_USER: str = "mock_user"
        SMTP_PASSWORD: str = "mock_pass"
        FROM_EMAIL: str = "mock@example.com"
    settings = MockSettings()
