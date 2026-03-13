from pathlib import Path

from pydantic_settings import BaseSettings


def _resolve_data_dir() -> Path:
    """Resolve DATA_DIR to project root / data, handling both local and Docker layouts."""
    resolved = Path(__file__).resolve()
    project_root = resolved.parents[2]
    # In Docker: __file__ = /app/app/config.py → parents[2] = / → /data (wrong)
    # Use parents[1] (/app) when parents[2] is the filesystem root
    if project_root == Path(project_root.root) or len(project_root.parts) <= 1:
        project_root = resolved.parents[1]
    return project_root / "data"


_DEFAULT_DATA_DIR = _resolve_data_dir()


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100
    DATA_DIR: Path = _DEFAULT_DATA_DIR
    FEEDBACK_DB_DIR: Path = _DEFAULT_DATA_DIR.parent / "feedback_data"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
