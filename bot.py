import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_IDS
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = Database()

@app.on_message(filters.command("start"))
async def start_command(client, message):
    from plugins.start import handle_start
    logger.info(f"Received /start from user {message.from_user.id}")
    await handle_start(client, message)

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client, callback_query):
    from plugins.start import check_subscription, handle_start
    user_id = callback_query.from_user.id
    logger.info(f"Checking subscription for user {user_id} via callback")
    if await check_subscription(client, user_id):
        logger.info(f"User {user_id} passed subscription check")
        await callback_query.message.delete()
        await handle_start(client, callback_query.message)
    else:
        logger.info(f"User {user_id} failed subscription check")
        await callback_query.answer("You haven't joined all channels yet!")

@app.on_callback_query(filters.regex("profile"))
async def profile_callback(client, callback_query):
    from plugins.referral import handle_profile_callback
    logger.info(f"Profile callback from user {callback_query.from_user.id}")
    await handle_profile_callback(client, callback_query)

@app.on_callback_query(filters.regex("invite"))
async def invite_callback(client, callback_query):
    from plugins.referral import invite_callback
    logger.info(f"Invite callback from user {callback_query.from_user.id}")
    await invite_callback(client, callback_query)

@app.on_callback_query(filters.regex("withdraw"))
async def withdraw_callback(client, callback_query):
    from plugins.withdrawal import handle_withdraw_callback
    logger.info(f"Withdraw callback from user {callback_query.from_user.id}")
    await handle_withdraw_callback(client, callback_query)

@app.on_callback_query(filters.regex("withdraw_(kbz|wave)"))
async def withdraw_method_callback(client, callback_query):
    from plugins.withdrawal import withdraw_method_callback
    method = "KBZ Pay" if callback_query.data == "withdraw_kbz" else "Wave Pay"
    logger.info(f"Withdraw {method} callback from user {callback_query.from_user.id}")
    await withdraw_method_callback(client, callback_query, method)

@app.on_callback_query(filters.regex("approve_withdraw_"))
async def approve_withdraw_callback(client, callback_query):
    from plugins.withdrawal import approve_withdraw_callback
    user_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Approve withdraw callback for user {user_id} by admin {callback_query.from_user.id}")
    await approve_withdraw_callback(client, callback_query, user_id)

@app.on_callback_query(filters.regex("deny_withdraw_"))
async def deny_withdraw_callback(client, callback_query):
    from plugins.withdrawal import deny_withdraw_callback
    user_id = int(callback_query.data.split("_")[-1])
    logger.info(f"Deny withdraw callback for user {user_id} by admin {callback_query.from_user.id}")
    await deny_withdraw_callback(client, callback_query, user_id)

@app.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_command(client, message):
    from plugins.admin import handle_stats
    logger.info(f"Stats command from admin {message.from_user.id}")
    await handle_stats(client, message)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_command(client, message):
    from plugins.admin import handle_broadcast
    logger.info(f"Broadcast command from admin {message.from_user.id}")
    await handle_broadcast(client, message)

@app.on_message(filters.command("ban_user") & filters.user(ADMIN_IDS))
async def ban_user_command(client, message):
    from plugins.admin import handle_ban_user
    logger.info(f"Ban user command from admin {message.from_user.id}")
    await handle_ban_user(client, message)

@app.on_message(filters.command("unban_user") & filters.user(ADMIN_IDS))
async def unban_user_command(client, message):
    from plugins.admin import handle_unban_user
    logger.info(f"Unban user command from admin {message.from_user.id}")
    await handle_unban_user(client, message)

@app.on_message(filters.command("banned_users") & filters.user(ADMIN_IDS))
async def banned_users_command(client, message):
    from plugins.admin import handle_banned_users
    logger.info(f"Banned users command from admin {message.from_user.id}")
    await handle_banned_users(client, message)

@app.on_message(filters.command("users") & filters.user(ADMIN_IDS))
async def users_command(client, message):
    from plugins.admin import handle_users
    logger.info(f"Users command from admin {message.from_user.id}")
    await handle_users(client, message)

@app.on_message(filters.command("set_vip") & filters.user(ADMIN_IDS))
async def set_vip_command(client, message):
    from plugins.admin import handle_set_vip
    logger.info(f"Set VIP command from admin {message.from_user.id}")
    await handle_set_vip(client, message)

@app.on_message(filters.command("add_bonus") & filters.user(ADMIN_IDS))
async def add_bonus_command(client, message):
    from plugins.admin import handle_add_bonus
    logger.info(f"Add bonus command from admin {message.from_user.id}")
    await handle_add_bonus(client, message)

@app.on_message(filters.command("profile"))
async def profile_command(client, message):
    from plugins.referral import handle_profile
    logger.info(f"Profile command from user {message.from_user.id}")
    await handle_profile(client, message)

@app.on_message(filters.command("withdraw"))
async def withdraw_command(client, message):
    from plugins.withdrawal import handle_withdraw
    logger.info(f"Withdraw command from user {message.from_user.id}")
    await handle_withdraw(client, message)

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()
