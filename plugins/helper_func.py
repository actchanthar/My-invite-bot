# plugins/helper_func.py
from telegram import Update
from telegram.ext import CallbackContext
from config import OWNER_ID
from database.database import get_channel_mode
import logging
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    return user_id == OWNER_ID

async def is_subscribed(bot, user_id):
    from database.database import show_channels
    channel_ids = await show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid, _ in channel_ids:
        if not await is_sub(bot, user_id, cid):
            return False

    return True

async def is_sub(bot, user_id, channel_id):
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in {"creator", "administrator", "member"}
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id} in channel {channel_id}: {e}")
        return False