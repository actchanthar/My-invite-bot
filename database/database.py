import logging
import secrets
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DEFAULT_EARNINGS_MMK  # Import DEFAULT_EARNINGS_MMK
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.get_database("bot_db")
        self.users = self.db.get_collection("users")

    async def add_user(self, user_id, username, referred_by=None):
        try:
            user = {
                "user_id": user_id,
                "username": username,
                "referrals": 0,
                "earnings_mmk": 0,
                "is_vip": False,
                "joined_at": datetime.datetime.now(),
                "referred_by": referred_by,
                "referral_counter": 0
            }
            await self.users.insert_one(user)
            logger.info(f"Added user {user_id} to database")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            raise

    async def get_user(self, user_id):
        try:
            user = await self.users.find_one({"user_id": user_id})
            if user:
                logger.info(f"Fetched user {user_id}: {user}")
                return user
            logger.warning(f"User {user_id} not found in database")
            return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    async def update_referrals(self, referrer_id):
        try:
            await self.users.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referrals": 1, "earnings_mmk": DEFAULT_EARNINGS_MMK}}  # Use config value (20)
            )
            logger.info(f"Updated referrals for user {referrer_id}")
        except Exception as e:
            logger.error(f"Error updating referrals for {referrer_id}: {e}")
            raise

    async def increment_referral_counter(self, user_id):
        try:
            result = await self.users.find_one_and_update(
                {"user_id": user_id},
                {"$inc": {"referral_counter": 1}},
                return_document=True
            )
            if result:
                new_counter = result["referral_counter"]
                logger.info(f"Incremented referral counter for user {user_id} to {new_counter}")
                return new_counter
            logger.warning(f"User {user_id} not found for counter increment")
            return None
        except Exception as e:
            logger.error(f"Error incrementing referral counter for user {user_id}: {e}")
            raise

    async def get_user_by_referral_counter(self, counter):
        try:
            user = await self.users.find_one({"referral_counter": int(counter)})
            if user:
                logger.info(f"Found user with referral counter {counter}: {user['user_id']}")
                return user
            logger.warning(f"No user found with referral counter {counter}")
            return None
        except Exception as e:
            logger.error(f"Error fetching user by referral counter {counter}: {e}")
            return None
