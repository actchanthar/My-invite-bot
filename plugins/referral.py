import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_profile(client, message):
    try:
        user_id = message.from_user.id
        user = await db.get_user(user_id)
        if not user:
            await message.reply("User not found!")
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

        await message.reply(
            profile_message,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in profile command for user {user_id}: {e}")
        await message.reply("Error retrieving your profile. Please try again later.")

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

async def invite_callback(client, callback_query):
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

async def my_referrals(client, message):
    try:
        user_id = message.from_user.id
        # Find all users who were referred by this user
        referred_users = await db.users.find({"referred_by": user_id}).to_list(None)
        if not referred_users:
            await message.reply("You have not referred any users yet.")
            return

        # Construct the response
        response = f"**Users You Referred**\n\nTotal: {len(referred_users)}\n\n"
        for user in referred_users:
            response += (
                f"User ID: {user['user_id']}\n"
                f"Username: @{user['username']}\n"
                f"Joined: {user['joined_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"---\n"
            )

        # Split the response if it's too long for a single message
        if len(response) > 4096:  # Telegram message length limit
            parts = [response[i:i + 4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response)

    except Exception as e:
        logger.error(f"Error in my_referrals for user {user_id}: {e}", exc_info=True)
        await message.reply("Error fetching your referrals. Please try again later.")
