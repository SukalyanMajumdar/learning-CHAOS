
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr


# Locate project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    openai_api_key: SecretStr = Field(min_length=1)
    openai_model: str = "gpt-4.1-mini"


# Initialize application settings
settings = Settings(
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
)
