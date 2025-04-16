import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_profile_callback(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return

        # Construct the profile message
        profile_message = (
            f"**Your Profile**\n\n"
            f"User ID: {user['user_id']}\n"
            f"Username: @{user['username']}\n"
            f"Referrals: {user['referrals']}\n"
            f"Earnings: {user['earnings_mmk']} MMK\n"
            f"VIP Status: {'Yes' if user['is_vip'] else 'No'}\n"
            f"Joined: {user['joined_at'].strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Add a "Back" button to return to the main menu
        buttons = [
            [InlineKeyboardButton("Back", callback_data="back_to_menu")]
        ]

        await callback_query.message.edit_text(
            profile_message,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in profile callback for user {user_id}: {e}")
        await callback_query.message.reply("Error retrieving your profile. Please try again later.")

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

        # Add a "Back" button to return to the main menu
        buttons = [
            [InlineKeyboardButton("Back", callback_data="back_to_menu")]
        ]

        await callback_query.message.edit_text(
            f"Your invite link: {invite_link}\nShare this link with your friends to earn referrals!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in invite callback for user {user_id}: {e}")
        await callback_query.message.reply("Error generating invite link. Please try again later.")
