import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# On Render/Railway set DATA_DIR to a mounted disk path so SQLite survives redeploys.
_data_dir = Path(os.environ.get("DATA_DIR", str(BASE_DIR)))
_data_dir.mkdir(parents=True, exist_ok=True)
_default_sqlite = _data_dir / "quickconcrete.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{_default_sqlite}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
