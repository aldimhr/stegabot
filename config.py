"""Environment configuration loader."""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY", "")
MAX_SECRET_BYTES = 500
MAX_COVER_CHARS = 10_000
RATE_LIMIT_SECONDS = 5
