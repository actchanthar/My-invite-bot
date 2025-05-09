# plugins/admin.py
from telegram import Update
from telegram.ext import CallbackContext
from database.database import get_user, update_user
from config import ADMIN_ID, LOG_CHANNEL, REFERRAL_REWARD, REFERRAL_THRESHOLD, PER_REFERRAL_EARNING

async def stats(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    users = await get_user(None)
    if not users:
        users = []

    total_users = len(users)
    total_referrals = sum(user.get("referrals", 0) for user in users)
    total_balance = sum(user.get("balance", 0) for user in users)

    stats_message = (
        f"Bot Statistics:\n"
        f"Total Users: {total_users}\n"
        f"Total Referrals: {total_referrals}\n"
        f"Total Balance Distributed: {total_balance} MMK"
    )
    await update.message.reply_text(stats_message)

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} ran /stats\n{stats_message}"
    )

async def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast. Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    users = await get_user(None)
    if not users:
        users = []

    success_count = 0
    for user in users:
        user_id = user.get("user_id")
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success_count += 1
        except Exception as e:
            print(f"Failed to send broadcast to {user_id}: {e}")

    await update.message.reply_text(f"Broadcast sent to {success_count} users.")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} sent a broadcast to {success_count} users:\n{message}"
    )

async def ban_user(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a user ID to ban. Usage: /ban_user <user_id>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")
        return

    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("User not found.")
        return

    await update_user(user_id, {"banned": True})
    await update.message.reply_text(f"User {user_id} has been banned.")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} banned user {user_id}"
    )

async def unban_user(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a user ID to unban. Usage: /unban_user <user_id>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")
        return

    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("User not found.")
        return

    await update_user(user_id, {"banned": False})
    await update.message.reply_text(f"User {user_id} has been unbanned.")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} unbanned user {user_id}"
    )

async def banned_users(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    users = await get_user(None)
    if not users:
        users = []

    banned_users = [user for user in users if user.get("banned", False)]
    if not banned_users:
        await update.message.reply_text("No users are currently banned.")
        return

    banned_list = "\n".join([f"User ID: {user['user_id']}" for user in banned_users])
    await update.message.reply_text(f"Banned Users:\n{banned_list}")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} viewed banned users list"
    )

async def users(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    users = await get_user(None)
    if not users:
        users = []

    if not users:
        await update.message.reply_text("No users found.")
        return

    total_users = len(users)
    user_list = "\n".join([f"User ID: {user['user_id']}, Balance: {user.get('balance', 0)} MMK, Referrals: {user.get('referrals', 0)}" for user in users])
    response_message = f"{total_users} people using this bot"

    # Send the simplified response to the admin
    await update.message.reply_text(response_message)

    # Log the detailed user list to the log channel
    detailed_message = f"Admin {update.effective_user.id} viewed all users list:\nTotal Users: {total_users}\n\nAll Users:\n{user_list}"
    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=detailed_message
    )

async def add_bonus(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /add_bonus <user_id> <amount>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid user ID or amount. Usage: /add_bonus <user_id> <amount>")
        return

    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("User not found.")
        return

    current_balance = user.get("balance", 0)
    new_balance = current_balance + amount
    await update_user(user_id, {"balance": new_balance})

    # Send congratulatory message to the user
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"Congratulations 🎉👏\n"
            f"Admin has added a bonus of {amount} MMK to your account.\n"
            f"New Balance: {new_balance} MMK"
        )
    )

    # Notify the admin
    await update.message.reply_text(f"Added {amount} MMK to user {user_id}. New balance: {new_balance} MMK")

    # Log the action
    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} added {amount} MMK bonus to user {user_id}. New balance: {new_balance} MMK"
    )

async def set_referral_reward(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /set_referral_reward <amount>")
        return

    try:
        new_reward = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid amount. Usage: /set_referral_reward <amount>")
        return

    await update.message.reply_text(f"Referral reward updated to {new_reward} MMK. Please update REFERRAL_REWARD in config.py manually.")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Admin {update.effective_user.id} set referral reward to {new_reward} MMK (manual config update required)"
    )