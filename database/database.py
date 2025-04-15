import logging
from pymongo import MongoClient
from config import MONGO_URI, DEFAULT_EARNINGS_MMK, REFERRAL_THRESHOLD
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Use Motor for async MongoDB operations
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client["telegram_bot_db"]
        self.users = self.db.users
        self.banned_users = self.db.banned_users

    async def add_user(self, user_id, username, referral_id=None):
        try:
            user = {
                "user_id": user_id,
                "username": username,
                "referrals": 0,
                "earnings_mmk": 0,
                "is_vip": False,
                "joined_at": datetime.utcnow()
            }
            if referral_id:
                user["referred_by"] = int(referral_id)
            result = await self.users.insert_one(user)
            logger.info(f"Added user {user_id} to database with ID {result.inserted_id}")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            raise

    async def get_user(self, user_id):
        try:
            user = await self.users.find_one({"user_id": user_id})
            if user:
                logger.info(f"Fetched user {user_id}: {user}")
            else:
                logger.warning(f"User {user_id} not found in database")
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise

    async def update_referrals(self, referrer_id):
        try:
            referrer = await self.users.find_one({"user_id": referrer_id})
            if not referrer:
                logger.warning(f"Referrer {referrer_id} not found")
                return
            new_referrals = referrer.get("referrals", 0) + 1
            await self.users.update_one(
                {"user_id": referrer_id},
                {"$set": {"referrals": new_referrals}}
            )
            # Award earnings for each referral, since REFERRAL_THRESHOLD is now 1
            earnings = referrer.get("earnings_mmk", 0) + DEFAULT_EARNINGS_MMK
            await self.users.update_one(
                {"user_id": referrer_id},
                {"$set": {"earnings_mmk": earnings}}
            )
            logger.info(f"Updated earnings for {referrer_id} to {earnings} MMK for {new_referrals} referrals")
        except Exception as e:
            logger.error(f"Error updating referrals for {referrer_id}: {e}")
            raise

    async def update_earnings(self, user_id, amount):
        try:
            user = await self.users.find_one({"user_id": user_id})
            if not user:
                logger.warning(f"User {user_id} not found")
                return
            new_earnings = max(0, user.get("earnings_mmk", 0) + amount)
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"earnings_mmk": new_earnings}}
            )
            logger.info(f"Updated earnings for {user_id} to {new_earnings} MMK")
        except Exception as e:
            logger.error(f"Error updating earnings for {user_id}: {e}")
            raise

    async def set_vip(self, user_id, is_vip):
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_vip": is_vip}}
            )
            logger.info(f"Set VIP status for {user_id} to {is_vip}")
        except Exception as e:
            logger.error(f"Error setting VIP for {user_id}: {e}")
            raise

    async def get_stats(self):
        try:
            count = await self.users.count_documents({})
            logger.info(f"Total users in database: {count}")
            return count
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            raise

    async def get_all_users(self):
        try:
            users = await self.users.find().to_list(None)
            logger.info(f"Fetched {len(users)} users from database")
            return users
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            raise

    async def ban_user(self, user_id, reason, duration):
        try:
            ban_until = datetime.utcnow() + timedelta(days=duration)
            await self.banned_users.insert_one({
                "user_id": user_id,
                "reason": reason,
                "duration": duration,
                "banned_until": ban_until
            })
            logger.info(f"Banned user {user_id} for {duration} days")
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            raise

    async def unban_user(self, user_id):
        try:
            await self.banned_users.delete_one({"user_id": user_id})
            logger.info(f"Unbanned user {user_id}")
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            raise

    async def get_banned_users(self):
        try:
            current_time = datetime.utcnow()
            banned_users = await self.banned_users.find().to_list(None)
            active_bans = [user for user in banned_users if user["banned_until"] > current_time]
            for user in banned_users:
                if user["banned_until"] <= current_time:
                    await self.banned_users.delete_one({"user_id": user["user_id"]})
            logger.info(f"Fetched {len(active_bans)} active banned users")
            return active_bans
        except Exception as e:
            logger.error(f"Error fetching banned users: {e}")
            raise
