import os

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "telegram_bot"
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
FORCE_SUB_CHANNELS = [int(x) for x in os.getenv("FORCE_SUB_CHANNELS", "").split(",") if x]
REFERRAL_THRESHOLD = int(os.getenv("REFERRAL_THRESHOLD", 15))
DEFAULT_EARNINGS_MMK = int(os.getenv("DEFAULT_EARNINGS_MMK", 50000))