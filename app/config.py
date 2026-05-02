from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./travelapp.db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "TravelApp <onboarding@resend.dev>"

    class Config:
        env_file = ".env"

settings = Settings()
