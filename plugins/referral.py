from pyrogram import Client, filters
from database.database import Database
from config import DEFAULT_EARNINGS_MMK

db = Database()

async def handle_profile(client, message):
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

@app.on_callback_query(filters.regex("invite"))
async def invite_callback(client, callback_query):
    user_id = callback_query.from_user.id
    invite_link = f"https://t.me/{(await client.get_me()).username}?start={user_id}"
    await callback_query.message.reply(f"Your invite link: {invite_link}")