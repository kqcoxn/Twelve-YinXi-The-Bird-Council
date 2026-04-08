from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    FAST_MODEL_API_KEY: str = ""
    FAST_MODEL_ENDPOINT: str = "https://api.openai.com/v1"
    FAST_MODEL_NAME: str = "gpt-3.5-turbo"
    FAST_MODEL_PROVIDER: str = "openai"  # LiteLLM provider prefix

    STRONG_MODEL_API_KEY: str = ""
    STRONG_MODEL_ENDPOINT: str = "https://api.openai.com/v1"
    STRONG_MODEL_NAME: str = "gpt-4"
    STRONG_MODEL_PROVIDER: str = "openai"  # LiteLLM provider prefix

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    AUTO_OPEN_BROWSER: bool = True

    # Database Configuration
    DATABASE_URL: Optional[str] = None

    # Session Configuration
    SESSION_TTL: int = 86400
    MAX_DEBATE_ROUNDS: int = 3

    # Mock LLM for Development
    MOCK_LLM: bool = False

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "backend" / "data"
    DB_PATH: Path = DATA_DIR / "council.db"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-create data directory
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def database_url(self) -> str:
        """Get database URL with fallback default."""
        return self.DATABASE_URL or f"sqlite:///./{self.DB_PATH}"

    class Config:
        # Look for .env file in the backend directory
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
