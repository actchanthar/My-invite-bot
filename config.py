import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]
FORCE_SUB_CHANNELS = os.getenv("FORCE_SUB_CHANNELS", "").split(",")

# Load REFERRAL_THRESHOLD and DEFAULT_EARNINGS_MMK with logging
REFERRAL_THRESHOLD = int(os.getenv("REFERRAL_THRESHOLD", 1))
DEFAULT_EARNINGS_MMK = int(os.getenv("DEFAULT_EARNINGS_MMK", 50))

logger.info(f"Loaded REFERRAL_THRESHOLD: {REFERRAL_THRESHOLD}")
logger.info(f"Loaded DEFAULT_EARNINGS_MMK: {DEFAULT_EARNINGS_MMK}")