import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TRIAL_MODE = os.getenv("KURASHI_TRIAL_MODE") == "1"
_custom_directory = os.getenv("KURASHI_DATA_DIR")
DATA_DIR = Path(_custom_directory).expanduser().resolve() if _custom_directory else PROJECT_DIR
HEALTH_DB = DATA_DIR / "database" / "health.db"
ACTIVITY_DB = DATA_DIR / "app_data.db"
UPLOADS_DIR = DATA_DIR / "uploads"
NEWS_FILE = HEALTH_DB.parent / "daily_news.json"


def trial_directory_ready():
    return bool(_custom_directory and Path(_custom_directory).is_absolute() and DATA_DIR != PROJECT_DIR)


def prepare_runtime_storage():
    HEALTH_DB.parent.mkdir(parents=True, exist_ok=True)
    for group in ("seniors", "students"):
        (UPLOADS_DIR / group).mkdir(parents=True, exist_ok=True)
