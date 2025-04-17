import os
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
from Database import Database
import config  # Import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = config.BOT_TOKEN
CHAT_ID = -1002097823468
CHAT_INVITE_LINK = "https://t.me/tiktokceleshd"
MONGO_URI = config.MONGO_URI
DB_NAME = "bot_db"
USERS_COLLECTION = "users"
EARNINGS_PER_REFERRAL = config.DEFAULT_EARNINGS_MMK  # Use config value (20)
BOT_USERNAME = "@ITACTbot"

# Initialize Database
try:
    db = Database()
    logger.info("Initialized Database connection")
except Exception as e:
    logger.error(f"Failed to initialize Database: {e}")
    raise

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    existing_user = await db.get_user(user_id)
    if not existing_user:
        try:
            await db.add_user(user_id, user.username or "", referred_by=referrer_id)
            logger.info(f"New user {user_id} registered, referred_by: {referrer_id}")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            await update.message.reply_text("An error occurred. Please try again later.")
            return
    else:
        if referrer_id and not existing_user.get("referred_by"):
            try:
                await db.users.update_one(
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
            await db.increment_referral_counter(referrer_id)
            logger.info(f"Incremented referral_counter for referrer {referrer_id}")
        except Exception as e:
            logger.error(f"Error updating referral_counter for referrer {referrer_id}: {e}")

    if await check_subscription(context.bot, user_id, CHAT_ID):
        await update.message.reply_text("You're all set! Thanks for joining our channel.")
        await process_referral(user_id, referrer_id, context)
    else:
        await update.message.reply_text(
            f"Welcome! Please join our channel to complete your referral: {CHAT_INVITE_LINK}\n"
            f"Your referral link: {BOT_USERNAME}?start={user_id}"
        )

async def getlink(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    if not user:
        await update.message.reply_text("Please start the bot first with /start.")
        return
    await update.message.reply_text(f"Your referral link: {BOT_USERNAME}?start={user_id}")

async def check(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    try:
        if await check_subscription(context.bot, user_id, CHAT_ID):
            await update.message.reply_text("You're a member of the channel! Referral completed.")
            user = await db.get_user(user_id)
            if user and user.get("referred_by"):
                await process_referral(user_id, user["referred_by"], context)
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

async def process_referral(user_id: int, referrer_id: int, context: CallbackContext) -> None:
    if not referrer_id or user_id == referrer_id:
        return

    user = await db.get_user(user_id)
    if user and user.get("referral_counted"):
        return

    try:
        if await check_subscription(context.bot, user_id, CHAT_ID):
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"referral_counted": True}}
            )
            await db.update_referrals(referrer_id)
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
            user = await db.get_user(user_id)
            if user and user.get("referred_by"):
                await process_referral(user_id, user["referred_by"], context)
                await context.bot.send_message(
                    user_id,
                    "Thanks for joining the channel! Your referral is complete."
                )
        except Exception as e:
            logger.error(f"Error processing chat member update for user {user_id}: {e}")

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.effective_message:
        await update.message.reply_text(
            "An error occurred. Please try again later."
        )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CommandHandler("getlink", getlink))
    application.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    application.add_error_handler(error_handler)

    logger.info("Starting bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
