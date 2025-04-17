import logging
from pyrogram import Client, filters
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_users(client, message):
    try:
        # Fetch all users from the database
        users = await db.users.find().to_list(None)
        if not users:
            await message.reply("No users found.")
            return

        # Construct the response
        total_users = len(users)
        response = f"**Total Users:** {total_users}\n\n"
        for user in users:
            response += (
                f"User ID: {user['user_id']}\n"
                f"Username: @{user['username']}\n"
                f"Referrals: {user['referrals']}\n"
                f"Earnings: {user['earnings_mmk']} MMK\n"
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
        logger.error(f"Error in handle_users: {str(e)}", exc_info=True)
        await message.reply("Error fetching users. Please try again later.")

async def handle_stats(client, message):
    try:
        total_users = await db.users.count_documents({})
        total_referrals = sum(user['referrals'] async for user in db.users.find())
        total_earnings = sum(user['earnings_mmk'] async for user in db.users.find())
        
        response = (
            f"**Bot Statistics**\n\n"
            f"Total Users: {total_users}\n"
            f"Total Referrals: {total_referrals}\n"
            f"Total Earnings Distributed: {total_earnings} MMK"
        )
        await message.reply(response)
    except Exception as e:
        logger.error(f"Error in handle_stats: {str(e)}", exc_info=True)
        await message.reply("Error fetching stats. Please try again later.")

async def handle_broadcast(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /broadcast <message>")
            return
        
        broadcast_message = " ".join(message.command[1:])
        users = await db.users.find().to_list(None)
        
        for user in users:
            try:
                await client.send_message(user['user_id'], broadcast_message)
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user['user_id']}: {str(e)}")
        
        await message.reply(f"Broadcast sent to {len(users)} users.")
    except Exception as e:
        logger.error(f"Error in handle_broadcast: {str(e)}", exc_info=True)
        await message.reply("Error sending broadcast. Please try again later.")

async def handle_ban_user(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /ban_user <user_id>")
            return
        
        user_id = int(message.command[1])
        await db.users.update_one({"user_id": user_id}, {"$set": {"is_banned": True}})
        await message.reply(f"User {user_id} has been banned.")
    except Exception as e:
        logger.error(f"Error in handle_ban_user: {str(e)}", exc_info=True)
        await message.reply("Error banning user. Please try again later.")

async def handle_unban_user(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /unban_user <user_id>")
            return
        
        user_id = int(message.command[1])
        await db.users.update_one({"user_id": user_id}, {"$set": {"is_banned": False}})
        await message.reply(f"User {user_id} has been unbanned.")
    except Exception as e:
        logger.error(f"Error in handle_unban_user: {str(e)}", exc_info=True)
        await message.reply("Error unbanning user. Please try again later.")

async def handle_banned_users(client, message):
    try:
        banned_users = await db.users.find({"is_banned": True}).to_list(None)
        if not banned_users:
            await message.reply("No banned users found.")
            return

        response = "**Banned Users**\n\n"
        for user in banned_users:
            response += (
                f"User ID: {user['user_id']}\n"
                f"Username: @{user['username']}\n"
                f"---\n"
            )

        if len(response) > 4096:
            parts = [response[i:i + 4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response)
    except Exception as e:
        logger.error(f"Error in handle_banned_users: {str(e)}", exc_info=True)
        await message.reply("Error fetching banned users. Please try again later.")

async def handle_set_vip(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Usage: /set_vip <user_id>")
            return
        
        user_id = int(message.command[1])
        await db.users.update_one({"user_id": user_id}, {"$set": {"is_vip": True}})
        await message.reply(f"User {user_id} has been set as VIP.")
    except Exception as e:
        logger.error(f"Error in handle_set_vip: {str(e)}", exc_info=True)
        await message.reply("Error setting VIP status. Please try again later.")

async def handle_add_bonus(client, message):
    try:
        if len(message.command) < 3:
            await message.reply("Usage: /add_bonus <user_id> <amount>")
            return
        
        user_id = int(message.command[1])
        amount = int(message.command[2])
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"earnings_mmk": amount}}
        )
        await message.reply(f"Added {amount} MMK bonus to user {user_id}.")
    except Exception as e:
        logger.error(f"Error in handle_add_bonus: {str(e)}", exc_info=True)
        await message.reply("Error adding bonus. Please try again later.")
