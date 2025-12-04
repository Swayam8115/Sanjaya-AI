# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_KEY: str

    GOOGLE_API_KEY: str

settings = Settings()
