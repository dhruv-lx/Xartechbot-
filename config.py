import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "xartech_admin_2026")

# Storage Paths
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
PHOTOS_DIR = UPLOADS_DIR / "photos"
EXPORTS_DIR = UPLOADS_DIR / "exports"

# Ensure directories exist
for directory in [DATA_DIR, UPLOADS_DIR, PHOTOS_DIR, EXPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "xartech_bot.db"
