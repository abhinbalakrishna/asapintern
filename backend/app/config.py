import secrets
from pathlib import Path
from pydantic_settings import BaseSettings

_KEY_FILE = Path(__file__).resolve().parent.parent / ".secret_key"


def _load_or_create_secret_key() -> str:
    if _KEY_FILE.exists():
        return _KEY_FILE.read_text().strip()
    key = secrets.token_urlsafe(32)
    _KEY_FILE.write_text(key)
    return key


class Settings(BaseSettings):
    secret_key: str = _load_or_create_secret_key()
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./asapintern.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
