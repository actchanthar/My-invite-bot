import logging
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_stats(client, message):
    try:
        total_users = await db.get_stats()
        logger.info(f"Stats command: Total users = {total_users}")
        await message.reply(f"Total users: {total_users}")
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply("Error fetching stats. Please try again later.")

async def handle_broadcast(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Please provide a message to broadcast.")
            return
        broadcast_msg = " ".join(message.command[1:])
        users = await db.get_all_users()
        logger.info(f"Broadcasting to {len(users)} users")
        for user in users:
            try:
                await client.send_message(user["user_id"], broadcast_msg)
                logger.info(f"Sent broadcast to {user['user_id']}")
            except Exception as e:
                logger.error(f"Error broadcasting to {user['user_id']}: {e}")
        await message.reply("Broadcast sent successfully.")
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply("Error sending broadcast. Please try again later.")

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
        await message.reply("Error banning user. Please try again later.")

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
        await message.reply("Error unbanning user. Please try again later.")

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
        await message.reply("Error fetching banned users. Please try again later.")

async def handle_users(client, message):
    try:
        users = await db.get_all_users()
        logger.info(f"Users command: Found {len(users)} users")
        if not users:
            await message.reply("No users found in the database.")
            return
        response = "Users:\n"
        for user in users:
            response += f"ID: {user['user_id']}, Username: @{user['username']}\n"
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in users command: {e}")
        await message.reply("Error fetching users. Please try again later.")

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
        await message.reply("Error setting VIP status. Please try again later.")

async def handle_add_bonus(client, message):
    try:
        if len(message.command) < 3:
            await message.reply("Usage: /add_bonus <user_id> <amount>")
            return
        user_id = int(message.command[1])
        amount = int(message.command[2])
        if amount <= 0:
            await message.reply("Bonus amount must be greater than 0.")
            return
        user = await db.get_user(user_id)
        if not user:
            await message.reply(f"User {user_id} not found.")
            return
        await db.update_earnings(user_id, amount)
        await client.send_message(user_id, f"You received a bonus of {amount} MMK!")
        await message.reply(f"Added {amount} MMK bonus to user {user_id}.")
    except Exception as e:
        logger.error(f"Error in add_bonus command: {e}")
        await message.reply("Error adding bonus. Please try again later.")
