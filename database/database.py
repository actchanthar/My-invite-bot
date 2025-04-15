from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME

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
        return self.users.update_one({"user_id": user_id}, {"$setOnInsert": user_data}, upsert=True)

    async def update_referrals(self, referral_id):
        user = self.users.find_one({"user_id": referral_id})
        if user:
            self.users.update_one({"user_id": referral_id}, {"$inc": {"referrals": 1}})
            from config import REFERRAL_THRESHOLD, DEFAULT_EARNINGS_MMK
            if user["referrals"] + 1 >= REFERRAL_THRESHOLD:
                earnings = DEFAULT_EARNINGS_MMK * 2 if user["is_vip"] else DEFAULT_EARNINGS_MMK
                self.users.update_one({"user_id": referral_id}, {"$inc": {"earnings_mmk": earnings}})

    async def get_user(self, user_id):
        return self.users.find_one({"user_id": user_id})

    async def ban_user(self, user_id, reason, duration):
        self.banned_users.update_one(
            {"user_id": user_id},
            {"$set": {"reason": reason, "duration": duration}},
            upsert=True
        )

    async def unban_user(self, user_id):
        self.banned_users.delete_one({"user_id": user_id})

    async def get_banned_users(self):
        return list(self.banned_users.find())

    async def get_stats(self):
        return self.users.count_documents({})

    async def get_all_users(self):
        return list(self.users.find())

    async def update_earnings(self, user_id, amount_mmk):
        self.users.update_one({"user_id": user_id}, {"$inc": {"earnings_mmk": amount_mmk}})

    async def set_vip(self, user_id, is_vip):
        self.users.update_one({"user_id": user_id}, {"$set": {"is_vip": is_vip}})