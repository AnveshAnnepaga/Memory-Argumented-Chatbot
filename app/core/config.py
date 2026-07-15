# File: app/core/config.py
from functools import lru_cache
from dotenv import load_dotenv
from app.core.settings import Settings

# Ensure .env is loaded before settings instantiation if present
load_dotenv(override=False)


@lru_cache()
def get_settings() -> Settings:
    """
    Configuration Loader & Manager singleton.
    Loads environment variables, validates configuration schemas, and returns the Settings object.
    Uses lru_cache to ensure settings are instantiated only once per process.
    """
    return Settings()


# Global centralized settings instance for clean import across all application layers
settings = get_settings()
