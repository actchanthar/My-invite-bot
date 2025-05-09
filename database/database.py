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
channels_collection = db["channels"]
requests_collection = db["requests"]

logger.info("Connected to MongoDB")
logger.info(f"MongoDB host: {client.address}")

# User functions (unchanged)
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

# Channel functions
async def add_channel(channel_id, invite_link=None, mode="on"):
    try:
        await channels_collection.insert_one({
            "channel_id": channel_id,
            "invite_link": invite_link,
            "mode": mode
        })
        logger.info(f"Added channel {channel_id} with invite link {invite_link}")
    except Exception as e:
        logger.error(f"Error adding channel {channel_id}: {e}")

async def show_channels():
    channels = []
    async for channel in channels_collection.find():
        channels.append((channel["channel_id"], channel.get("invite_link")))
    return channels

async def get_channel_mode(channel_id):
    channel = await channels_collection.find_one({"channel_id": channel_id})
    return channel.get("mode") if channel else None

async def update_channel_mode(channel_id, mode):
    await channels_collection.update_one(
        {"channel_id": channel_id},
        {"$set": {"mode": mode}}
    )

async def get_channel_invite_link(channel_id):
    channel = await channels_collection.find_one({"channel_id": channel_id})
    return channel.get("invite_link") if channel else None

async def update_channel_invite_link(channel_id, invite_link):
    await channels_collection.update_one(
        {"channel_id": channel_id},
        {"$set": {"invite_link": invite_link}}
    )

async def rem_channel(channel_id):
    await channels_collection.delete_one({"channel_id": channel_id})

async def req_user(chat_id, user_id):
    await requests_collection.insert_one({"chat_id": chat_id, "user_id": user_id})

async def del_req_user(chat_id, user_id):
    await requests_collection.delete_one({"chat_id": chat_id, "user_id": user_id})

async def req_user_exist(chat_id, user_id):
    return await requests_collection.find_one({"chat_id": chat_id, "user_id": user_id}) is not None

async def reqChannel_exist(chat_id):
    return await channels_collection.find_one({"channel_id": chat_id}) is not None