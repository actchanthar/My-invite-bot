import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_invite_callback(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return

        # Increment the referral counter for the user
        referral_counter = await db.increment_referral_counter(user_id)
        if referral_counter is None:
            await callback_query.message.reply("Error generating invite link. Please try again later.")
            await callback_query.answer()
            return

        # Generate the invite link with the ACT_<counter> format
        invite_link = f"https://t.me/ITACTbot?start=ACT_{referral_counter}"

        await callback_query.message.reply(
            f"Your invite link: {invite_link}\nShare this link with your friends to earn referrals!"
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in invite callback for user {user_id}: {e}")
        await callback_query.message.reply("Error generating invite link. Please try again later.")
