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
from pymongo.exceptions import ConnectionError  # Updated import

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
CHAT_ID = -1002097823468  # Chat ID for https://t.me/tiktokceleshd
CHAT_INVITE_LINK = "https://t.me/tiktokceleshd"
MONGO_URI = "mongodb://localhost:27017"  # Replace with your MongoDB URI
DB_NAME = "bot_database"
USERS_COLLECTION = "users"
EARNINGS_PER_REFERRAL = 100  # MMK per valid referral, adjust as needed
BOT_USERNAME = "@ITACTbot"  # Replace with your bot's username

# Initialize MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION]
    # Create index for user_id
    users_collection.create_index("user_id", unique=True)
    logger.info("Connected to MongoDB")
except ConnectionError as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

async def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command, process referrals, and prompt chat join."""
    user = update.effective_user
    user_id = user.id
    args = context.args  # Get referrer ID from /start <referrer_id>
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    # Check if user already exists in database
    existing_user = users_collection.find_one({"user_id": user_id})
    if not existing_user:
        # Create new user entry
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
        # Update referred_by if not set and referrer_id is provided
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

    # Increment referral_counter for referrer (tracks link clicks)
    if referrer_id:
        try:
            users_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referral_counter": 1}}
            )
            logger.info(f"Incremented referral_counter for referrer {referrer_id}")
        except Exception as e:
            logger.error(f"Error updating referral_counter for referrer {referrer_id}: {e}")

    # Check if user is in the chat
    if await check_subscription(context.bot, user_id, CHAT_ID):
        await update.message.reply_text("You're all set! Thanks for joining our channel.")
        # Process referral if not already counted
        await process_referral(user_id, referrer_id)
    else:
        await update.message.reply_text(
            f"Welcome! Please join our channel to complete your referral: {CHAT_INVITE_LINK}\n"
            f"Your referral link: {BOT_USERNAME}?start={user_id}"
        )

async def getlink(update: Update, context: CallbackContext) -> None:
    """Return the user's referral link."""
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        await update.message.reply_text("Please start the bot first with /start.")
        return
    await update.message.reply_text(f"Your referral link: {BOT_USERNAME}?start={user_id}")

async def check(update: Update, context: CallbackContext) -> None:
    """Allow users to check their referral status."""
    user_id = update.effective_user.id
    try:
        if await check_subscription(context.bot, user_id, CHAT_ID):
            await update.message.reply_text("You're a member of the channel! Referral completed.")
            # Check and process referral
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
    """Check if a user is a member of the chat with retry logic."""
    for attempt in range(3):  # Retry up to 3 times
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
            await asyncio.sleep(1)  # Wait before retrying
    logger.error(f"Failed to check subscription for user {user_id} after retries")
    return False

async def process_referral(user_id: int, referrer_id: int) -> None:
    """Process a referral and update referrer's stats if valid."""
    if not referrer_id or user_id == referrer_id:  # Prevent self-referrals
        return

    # Check if referral already counted
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("referral_counted"):
        return

    # Verify user is in chat
    if await check_subscription(context.bot, user_id, CHAT_ID):
        try:
            # Mark referral as counted
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"referral_counted": True}}
            )
            # Update referrer's referrals and earnings
            users_collection.update_one(
                {"user_id": referrer_id},
                {"$inc": {"referrals": 1, "earnings_mmk": EARNINGS_PER_REFERRAL}}
            )
            logger.info(f"Referral counted for referrer {referrer_id}, user {user_id}")
        except Exception as e:
            logger.error(f"Error updating referral for referrer {referrer_id}: {e}")
            raise

async def chat_member_update(update: Update, context: CallbackContext) -> None:
    """Handle chat member updates to detect when users join the chat."""
    member = update.chat_member
    if not member:
        return

    chat_id = member.chat.id
    user_id = member.new_chat_member.user.id
    status = member.new_chat_member.status

    if chat_id == CHAT_ID and status in ["member", "administrator", "creator"]:
        logger.info(f"User {user_id} joined chat {chat_id}")
        # Find referrer
        try:
            user = users_collection.find_one({"user_id": user_id})
            if user and user.get("referred_by"):
                await process_referral(user_id, user["referred_by"])
                await context.bot.send_message(
                    user_id,
                    "Thanks for joining the channel! Your referral is complete."
                )
        except Exception as e:
            logger.error(f"Error processing chat member update for user {user_id}: {e}")

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors, including database or API issues."""
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.effective_message:
        await update.message.reply_text(
            "An error occurred. Please try again later."
        )

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("getlink", getlink))
    application.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Starting bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
