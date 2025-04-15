import logging
from pyrogram import Client, filters
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_profile(client, message):
    try:
        user = await db.get_user(message.from_user.id)
        if not user:
            await message.reply("User not found!")
            return
        response = (
            f"Profile:\n"
            f"ID: {user['user_id']}\n"
            f"Username: @{user['username']}\n"
            f"Referrals: {user['referrals']}\n"
            f"Earnings: {user['earnings_mmk']} MMK\n"
            f"VIP: {'Yes' if user['is_vip'] else 'No'}"
        )
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        await message.reply("Error fetching profile.")

async def handle_profile_callback(client, callback_query):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user:
            await callback_query.message.reply("User not found!")
            return
        response = (
            f"Profile:\n"
            f"ID: {user['user_id']}\n"
            f"Username: @{user['username']}\n"
            f"Referrals: {user['referrals']}\n"
            f"Earnings: {user['earnings_mmk']} MMK\n"
            f"VIP: {'Yes' if user['is_vip'] else 'No'}"
        )
        await callback_query.message.reply(response)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        await callback_query.message.reply("Error fetching profile.")

async def invite_callback(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        bot = await client.get_me()
        invite_link = f"https://t.me/{bot.username}?start={user_id}"
        await callback_query.message.reply(f"Your invite link: {invite_link}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in invite callback: {e}")
        await callback_query.message.reply("Error generating invite link.")
