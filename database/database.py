# database/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = AsyncIOMotorClient(MONGODB_URI)
db = client["actit"]
users_collection = db["users"]

logger.info("Connected to MongoDB")
logger.info(f"MongoDB host: {client.address}")
logger.info(f"users_collection defined: {users_collection}")

async def get_user(user_id):
    try:
        if user_id is None:
            users = []
            async for user in users_collection.find({}):
                users.append(user)
            if not users:
                logger.info("No users found in database")
            return users
        else:
            user = await users_collection.find_one({"user_id": user_id})
            if not user:
                logger.info(f"User {user_id} not found in database")
            return user
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None

async def update_user(user_id, data):
    try:
        result = await users_collection.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )
        success = result.modified_count > 0 or result.upserted_id is not None
        if success:
            logger.info(f"Successfully updated user {user_id}")
        else:
            logger.info(f"No changes made for user {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False