from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
