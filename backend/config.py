import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def _database_uri():
    url = os.environ.get("DATABASE_URL")
    if url:
        # Render gives postgres:// — use psycopg2 driver (see requirements.txt)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url
    data_dir = Path(os.environ.get("DATA_DIR", str(BASE_DIR)))
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'quickconcrete.db'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
