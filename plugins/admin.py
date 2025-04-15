from pyrogram import Client, filters
from database.database import Database
from config import ADMIN_IDS

db = Database()

async def handle_stats(client, message):
    total_users = await db.get_stats()
    await message.reply(f"Total Users: {total_users}")

async def handle_broadcast(client, message):
    if not message.reply_to_message:
        await message.reply("Please reply to a message to broadcast!")
        return
    users = await db.get_all_users()
    for user in users:
        try:
            await message.reply_to_message.copy(user["user_id"])
        except:
            continue
    await message.reply("Broadcast completed!")

async def handle_ban_user(client, message):
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply("Usage: /ban_user <user_id> <duration> <reason>")
        return
    user_id, duration, reason = args[1], args[2], args[3]
    await db.ban_user(int(user_id), reason, duration)
    await message.reply(f"Banned user {user_id} for {duration} days. Reason: {reason}")

async def handle_unban_user(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Usage: /unban_user <user_id>")
        return
    user_id = args[1]
    await db.unban_user(int(user_id))
    await message.reply(f"Unbanned user {user_id}")

async def handle_banned_users(client, message):
    banned = await db.get_banned_users()
    if not banned:
        await message.reply("No banned users.")
        return
    response = "\n".join([f"User {b['user_id']}: {b['reason']} (Duration: {b['duration']})" for b in banned])
    await message.reply(response)

async def handle_users(client, message):
    users = await db.get_all_users()
    response = f"Total Users: {len(users)}\n\n"
    for user in users:
        response += f"ID: {user['user_id']}, Referrals: {user['referrals']}, Earnings: {user['earnings_mmk']} MMK\n"
    await message.reply(response)

@app.on_message(filters.command("set_vip") & filters.user(ADMIN_IDS))
async def set_vip_command(client, message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /set_vip <user_id> <true/false>")
        return
    user_id, is_vip = args[1], args[2].lower() == "true"
    await db.set_vip(int(user_id), is_vip)
    await message.reply(f"Set VIP status for user {user_id} to {is_vip}")

@app.on_message(filters.command("add_bonus") & filters.user(ADMIN_IDS))
async def add_bonus_command(client, message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /add_bonus <user_id> <amount_mmk>")
        return
    user_id, amount_mmk = args[1], int(args[2])
    await db.update_earnings(int(user_id), amount_mmk)
    await message.reply(f"Added {amount_mmk} MMK to user {user_id}")