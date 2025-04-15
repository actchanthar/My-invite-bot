import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from config import ADMIN_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_withdraw(client, message):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or user["earnings_mmk"] < 50000:
            await message.reply("You need at least 50,000 MMK to withdraw!")
            return
        buttons = [
            [InlineKeyboardButton("KBZ Pay", callback_data="withdraw_kbz")],
            [InlineKeyboardButton("Wave Pay", callback_data="withdraw_wave")]
        ]
        await message.reply(
            "Choose your withdrawal method:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in withdraw command: {e}")
        await message.reply("Error processing withdrawal request.")

async def handle_withdraw_callback(client, callback_query):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or user["earnings_mmk"] < 50000:
            await callback_query.message.reply("You need at least 50,000 MMK to withdraw!")
            await callback_query.answer()
            return
        buttons = [
            [InlineKeyboardButton("KBZ Pay", callback_data="withdraw_kbz")],
            [InlineKeyboardButton("Wave Pay", callback_data="withdraw_wave")]
        ]
        await callback_query.message.reply(
            "Choose your withdrawal method:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in withdraw callback: {e}")
        await callback_query.message.reply("Error processing withdrawal request.")

async def withdraw_method_callback(client, callback_query, method):
    try:
        user_id = callback_query.from_user.id
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return
        for admin_id in ADMIN_IDS:
            buttons = [
                [InlineKeyboardButton("Approve", callback_data=f"approve_withdraw_{user_id}")],
                [InlineKeyboardButton("Deny", callback_data=f"deny_withdraw_{user_id}")]
            ]
            await client.send_message(
                admin_id,
                f"Withdrawal Request:\n"
                f"User ID: {user_id}\n"
                f"Username: @{user['username']}\n"
                f"Amount: {user['earnings_mmk']} MMK\n"
                f"Method: {method}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        await callback_query.message.reply("Withdrawal request sent to admin. You'll be notified soon!")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in withdraw method callback: {e}")
        await callback_query.message.reply("Error sending withdrawal request.")

async def approve_withdraw_callback(client, callback_query, user_id):
    try:
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("Unauthorized!")
            return
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return
        await client.send_message(user_id, f"Your withdrawal of {user['earnings_mmk']} MMK has been approved and processed!")
        await db.update_earnings(user_id, -user["earnings_mmk"])
        await callback_query.message.reply("Withdrawal approved and processed.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in approve withdraw callback: {e}")
        await callback_query.message.reply("Error approving withdrawal.")

async def deny_withdraw_callback(client, callback_query, user_id):
    try:
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("Unauthorized!")
            return
        await client.send_message(user_id, "Your withdrawal request was denied by the admin.")
        await callback_query.message.reply("Withdrawal denied.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in deny withdraw callback: {e}")
        await callback_query.message.reply("Error denying withdrawal.")
