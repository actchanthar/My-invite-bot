import logging
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_stats(client, message):
    try:
        total_users = await db.get_stats()
        await message.reply(f"Total users: {total_users}")
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply("Error fetching stats.")

async def handle_broadcast(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Please provide a message to broadcast.")
            return
        broadcast_msg = " ".join(message.command[1:])
        users = await db.get_all_users()
        for user in users:
            try:
                await client.send_message(user["user_id"], broadcast_msg)
            except Exception as e:
                logger.error(f"Error broadcasting to {user['user_id']}: {e}")
        await message.reply("Broadcast sent successfully.")
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply("Error sending broadcast.")

async def handle_ban_user(client, message):
    try:
        if len(message.command) < 4:
            await message.reply("Usage: /ban_user <user_id> <reason> <days>")
            return
        user_id = int(message.command[1])
        reason = message.command[2]
        duration = int(message.command[3])
        await db.ban_user(user_id, reason, duration)
        await message.reply(f"User {user_id} banned for {duration} days. Reason: {reason}")
    except Exception as e:
        logger.error(f"Error in ban_user command: {e}")
        await message.reply("Error banning user.")

async def handle_unban_user(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /unban_user <user_id>")
            return
        user_id = int(message.command[1])
        await db.unban_user(user_id)
        await message.reply(f"User {user_id} unbanned.")
    except Exception as e:
        logger.error(f"Error in unban_user command: {e}")
        await message.reply("Error unbanning user.")

async def handle_banned_users(client, message):
    try:
        banned_users = await db.get_banned_users()
        if not banned_users:
            await message.reply("No banned users.")
            return
        response = "Banned Users:\n"
        for user in banned_users:
            response += f"ID: {user['user_id']}, Reason: {user['reason']}, Duration: {user['duration']} days\n"
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in banned_users command: {e}")
        await message.reply("Error fetching banned users.")

async def handle_users(client, message):
    try:
        users = await db.get_all_users()
        if not users:
            await message.reply("No users found.")
            return
        response = "Users:\n"
        for user in users:
            response += f"ID: {user['user_id']}, Username: @{user['username']}\n"
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in users command: {e}")
        await message.reply("Error fetching users.")

async def handle_set_vip(client, message):
    try:
        if len(message.command) < 3:
            await message.reply("Usage: /set_vip <user_id> <true/false>")
            return
        user_id = int(message.command[1])
        is_vip = message.command[2].lower() == "true"
        await db.set_vip(user_id, is_vip)
        status = "VIP" if is_vip else "non-VIP"
        await message.reply(f"User {user_id} set to {status}.")
    except Exception as e:
        logger.error(f"Error in set_vip command: {e}")
        await message.reply("Error setting VIP status.")
