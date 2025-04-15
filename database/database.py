import logging
from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME, REFERRAL_THRESHOLD, DEFAULT_EARNINGS_MMK

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.users = self.db.users
        self.banned_users = self.db.banned_users

    async def add_user(self, user_id, username, referral_id=None):
        user_data = {
            "user_id": user_id,
            "username": username,
            "referrals": 0,
            "earnings_mmk": 0,
            "referral_id": referral_id,
            "is_vip": False
        }
        try:
            result = self.users.update_one({"user_id": user_id}, {"$setOnInsert": user_data}, upsert=True)
            logger.info(f"Added/updated user {user_id} with referral_id {referral_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return None

    async def update_referrals(self, referral_id):
        try:
            user = self.users.find_one({"user_id": referral_id})
            if user:
                self.users.update_one({"user_id": referral_id}, {"$inc": {"referrals": 1}})
                logger.info(f"Incremented referrals for user {referral_id}: {user['referrals'] + 1}")
                if user["referrals"] + 1 >= REFERRAL_THRESHOLD:
                    earnings = DEFAULT_EARNINGS_MMK * 2 if user["is_vip"] else DEFAULT_EARNINGS_MMK
                    self.users.update_one({"user_id": referral_id}, {"$inc": {"earnings_mmk": earnings}})
                    logger.info(f"User {referral_id} earned {earnings} MMK for {REFERRAL_THRESHOLD} referrals")
            else:
                logger.warning(f"Referral user {referral_id} not found")
        except Exception as e:
            logger.error(f"Error updating referrals for {referral_id}: {e}")

    async def get_user(self, user_id):
        try:
            user = self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    async def ban_user(self, user_id, reason, duration):
        try:
            self.banned_users.update_one(
                {"user_id": user_id},
                {"$set": {"reason": reason, "duration": duration}},
                upsert=True
            )
            logger.info(f"Banned user {user_id} for {duration} days: {reason}")
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")

    async def unban_user(self, user_id):
        try:
            self.banned_users.delete_one({"user_id": user_id})
            logger.info(f"Unbanned user {user_id}")
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")

    async def get_banned_users(self):
        try:
            return list(self.banned_users.find())
        except Exception as e:
            logger.error(f"Error fetching banned users: {e}")
            return []

    async def get_stats(self):
        try:
            count = self.users.count_documents({})
            logger.info(f"Retrieved stats: {count} users")
            return count
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return 0

    async def get_all_users(self):
        try:
            users = list(self.users.find())
            logger.info(f"Retrieved {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []

    async def update_earnings(self, user_id, amount_mmk):
        try:
            self.users.update_one({"user_id": user_id}, {"$inc": {"earnings_mmk": amount_mmk}})
            logger.info(f"Updated earnings for user {user_id}: {amount_mmk} MMK")
        except Exception as e:
            logger.error(f"Error updating earnings for {user_id}: {e}")

    async def set_vip(self, user_id, is_vip):
        try:
            self.users.update_one({"user_id": user_id}, {"$set": {"is_vip": is_vip}})
            logger.info(f"Set VIP status for user {user_id} to {is_vip}")
        except Exception as e:
            logger.error(f"Error setting VIP for {user_id}: {e}")