import os
from pathlib import Path
from dotenv import load_dotenv

# Жоба каталогы
BASE_DIR = Path(__file__).resolve().parent

# .env файлын жүктеу
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Almaty").strip()
DB_PATH = BASE_DIR / "tracker.db"
