from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from config import ADMIN_IDS

db = Database()

async def handle_withdraw(client, message):
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

@app.on_callback_query(filters.regex("withdraw_(kbz|wave)"))
async def withdraw_method_callback(client, callback_query):
    method = "KBZ Pay" if callback_query.data == "withdraw_kbz" else "Wave Pay"
    user_id = callback_query.from_user.id
    user = await db.get_user(user_id)
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

@app.on_callback_query(filters.regex("approve_withdraw_"))
async def approve_withdraw_callback(client, callback_query):
    if callback_query.from_user.id not in ADMIN_IDS:
        return
    user_id = int(callback_query.data.split("_")[-1])
    user = await db.get_user(user_id)
    await client.send_message(user_id, f"Your withdrawal of {user['earnings_mmk']} MMK has been approved and processed!")
    await db.update_earnings(user_id, -user["earnings_mmk"])
    await callback_query.message.reply("Withdrawal approved and processed.")

@app.on_callback_query(filters.regex("deny_withdraw_"))
async def deny_withdraw_callback(client, callback_query):
    if callback_query.from_user.id not in ADMIN_IDS:
        return
    user_id = int(callback_query.data.split("_")[-1])
    await client.send_message(user_id, "Your withdrawal request was denied by the admin.")
    await callback_query.message.reply("Withdrawal denied.")