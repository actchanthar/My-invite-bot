import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_IDS
from database.database import Database

logging.basicConfig(level=logging.INFO)
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database()

@app.on_message(filters.command("start"))
async def start_command(client, message):
    from plugins.start import handle_start
    await handle_start(client, message)

@app.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_command(client, message):
    from plugins.admin import handle_stats
    await handle_stats(client, message)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_command(client, message):
    from plugins.admin import handle_broadcast
    await handle_broadcast(client, message)

@app.on_message(filters.command("ban_user") & filters.user(ADMIN_IDS))
async def ban_user_command(client, message):
    from plugins.admin import handle_ban_user
    await handle_ban_user(client, message)

@app.on_message(filters.command("unban_user") & filters.user(ADMIN_IDS))
async def unban_user_command(client, message):
    from plugins.admin import handle_unban_user
    await handle_unban_user(client, message)

@app.on_message(filters.command("banned_users") & filters.user(ADMIN_IDS))
async def banned_users_command(client, message):
    from plugins.admin import handle_banned_users
    await handle_banned_users(client, message)

@app.on_message(filters.command("users") & filters.user(ADMIN_IDS))
async def users_command(client, message):
    from plugins.admin import handle_users
    await handle_users(client, message)

@app.on_message(filters.command("withdraw"))
async def withdraw_command(client, message):
    from plugins.withdrawal import handle_withdraw
    await handle_withdraw(client, message)

@app.on_message(filters.command("profile"))
async def profile_command(client, message):
    from plugins.referral import handle_profile
    await handle_profile(client, message)

if __name__ == "__main__":
    app.run()