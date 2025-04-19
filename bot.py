import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    CallbackContext,
)
from telegram.error import BadRequest
from pymongo import MongoClient
from pymongo.exceptions import ConnectionError

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = -1002097823468
CHAT_INVITE_LINK = "https://t.me/tiktokceleshd"
MONGO_URI = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority"
DB_NAME = "bot_database"
USERS_COLLECTION = "users"
EARNINGS_PER_REFERRAL = 100
BOT_USERNAME = "@ITACTbot"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION]
    users_collection.create_index("user_id", unique=True)
    logger.info("Connected to MongoDB")
except ConnectionError as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    existing_user = users_collection.find_one({"user_id": user_id})
    if not existing_user:
        user_data = {
            "user_id": user_id,
            "username": user.username or "",
            "referrals": 0,
            "earnings_mmk": 0,
            "referral_counter": 0,
            "is_vip": False,
            "joined_at": datetime.now(),
            "referred_by": referrer_id
        }
        try:
            users_collection.insert_one(user_data)
            logger.info(f"New user {user_id} registered, referred_by: {referrer_id}")
        except Exception as e:
            logger.error(f"Error inserting user {user_id}: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
            return
    else:
        if referrer_id and not existing_user.get("referred_by"):
            try:
                users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"referred_by": referrer_id}}
                )
                logger.info(f"Updated user {user_id} with referrer {referrer_id}")
            except Exception as e:
                logger.error(f"Error updating user {user_id}: {e}")
                await update.message.reply_text("An error occurred. Please try again later.")
                return

    if referrer_id:
        try:
            users_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referral_counter": 1}}
            )
            logger.info(f"Incremented referral_counter for referrer {referrer_id}")
        except Exception as e:
            logger.error(f"Error updating referral_counter for referrer {referrer_id}: {e}")

    if await check_subscription(context.bot, user_id, CHAT_ID):
        await update.message.reply_text("You're all set! Thanks for joining our channel.")
        await process_referral(user_id, referrer_id)
    else:
        await update.message.reply_text(
            f"Welcome! Please join our channel to complete your referral: {CHAT_INVITE_LINK}\n"
            f"Your referral link: {BOT_USERNAME}?start={user_id}"
        )

async def getlink(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await update.message.reply_text("Please start the bot first with /start.")
        return
    await update.message.reply_text(f"Your referral link: {BOT_USERNAME}?start={user_id}")

async def check(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    try:
        if await check_subscription(context.bot, user_id, CHAT_ID):
            await update.message.reply_text("You're a member of the channel! Referral completed.")
            user = users_collection.find_one({"user_id": user_id})
            if user and user.get("referred_by"):
                await process_referral(user_id, user["referred_by"])
        else:
            await update.message.reply_text(
                f"Please join our channel to complete your referral: {CHAT_INVITE_LINK}"
            )
    except Exception as e:
        logger.error(f"Error checking referral status for user {user_id}: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def check_subscription(bot, user_id: int, chat_id: int) -> bool:
    for attempt in range(3):
        try:
            chat_member = await bot.get_chat_member(chat_id, user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                return True
            return False
        except BadRequest as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                logger.info(f"User {user_id} not in chat {chat_id}")
                return False
            logger.warning(f"Error checking subscription for user {user_id}: {e}")
            await asyncio.sleep(1)
    logger.error(f"Failed to check subscription for user {user_id} after retries")
    return False

async def process_referral(user_id: int, referrer_id: int) -> None:
    if not referrer_id or user_id == referrer_id:
        return

    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("referral_counted"):
        return

    if await check_subscription(context.bot, user_id, CHAT_ID):
        try:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"referral_counted": True}}
            )
            users_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referrals": 1, "earnings_mmk": EARNINGS_PER_REFERRAL}}
            )
            logger.info(f"Referral counted for referrer {referrer_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating referral for referrer {referrer_id}: {e}")
            raise

async def chat_member_update(update: Update, context: CallbackContext) -> None:
    member = update.chat_member
    if not member:
        return

    chat_id = member.chat.id
    user_id = member.new_chat_member.user.id
    status = member.new_chat_member.status

    if chat_id == CHAT_ID and status in ["member", "administrator", "creator"]:
        logger.info(f"User {user_id} joined chat {chat_id}")
        try:
            user = users_collection.find_one({"user_id": user_id})
            if user and user.get("referred_by"):
                await process_referral(user_id, user["referred_by"])
                await context.bot.send_message(
                    user_id,
                    "Thanks
