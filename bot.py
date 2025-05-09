# bot.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from telegram.request import HTTPXRequest
import logging
from config import *
from database.database import get_user, update_user
from plugins import start, admin, referral, withdrawal

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    logger.info(f"button_callback triggered with data: {query.data}")

    user_id = query.from_user.id
    data = query.data

    if data == "get_referral_link":
        user = await get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found in database when generating referral link")
            await query.message.reply_text("User not found. Please start with /start.")
            return

        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        logger.info(f"Generated referral link for user {user_id}: {referral_link}")
        await query.message.reply_text(f"Your Referral Link: {referral_link}")
    elif data == "check_balance":
        user = await get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found in database when checking balance")
            await query.message.reply_text("User not found. Please start with /start.")
            return
        balance = round(user.get("balance", 0), 2)  # Round to 2 decimal places (if you applied the rounding fix earlier)
        referrals = user.get("referrals", 0)
        per_referral = round(user.get("per_referral_earning", PER_REFERRAL_EARNING), 2)
        referral_threshold = user.get("referral_threshold", REFERRAL_THRESHOLD)
        referral_reward = round(user.get("referral_reward", REFERRAL_REWARD), 2)
        total_referral_earnings = round(referrals * per_referral, 2)
        bonus_earnings = round((referrals // referral_threshold) * referral_reward, 2)
        total_earnings = round(total_referral_earnings + bonus_earnings, 2)
        await query.message.reply_text(
            f"Current Balance: {balance} MMK 💸\n"
            f"Number of Referrals: {referrals} 👥\n"
            f"Earnings Per Referral: {per_referral} MMK 💰\n"
            f"Total Referral Earnings: {total_referral_earnings} MMK 📈\n"
            f"Bonus ({referral_threshold} Referrals for {referral_reward} MMK 🎁): {bonus_earnings} MMK\n"
            f"Total Earnings: {total_earnings} MMK 🤑"
        )
    elif data == "withdraw":
        await withdrawal.withdraw(update, context)
    elif data == "help":
        await query.message.reply_text(
            "Help:\n"
            "/start - Start the bot 🚀\n"
            "/withdraw - Withdraw funds 💸\n"
            "Share your referral link to earn rewards. 🔗"
        )
    elif data == "back":
        await start.start(update, context)
    elif data == "check_subscription":
        logger.info(f"check_subscription triggered for user {user_id}")
        all_subscribed = True
        for channel_id in REQUIRED_CHANNELS:
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if chat_member.status not in ["member", "administrator", "creator"]:
                    logger.info(f"User {user_id} not subscribed to channel {channel_id}. Status: {chat_member.status}")
                    all_subscribed = False
                    break
                else:
                    logger.info(f"User {user_id} is subscribed to channel {channel_id}. Status: {chat_member.status}")
            except Exception as e:
                logger.error(f"Error checking subscription for channel {channel_id} for user {user_id}: {e}")
                all_subscribed = False
                break

        if all_subscribed:
            logger.info(f"User {user_id} is subscribed to all channels")
            await query.message.reply_text("You have successfully joined! Use /start to continue.")
        else:
            channel_links = {}
            channel_names = {}
            for channel_id in REQUIRED_CHANNELS:
                try:
                    bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
                    if bot_member.status not in ["member", "administrator", "creator"]:
                        logger.warning(f"Bot is not a member of channel {channel_id}, cannot generate invite link")
                        channel_links[channel_id] = "https://t.me/+error"
                        channel_names[channel_id] = "Unknown Channel"
                        continue
                except Exception as e:
                    logger.error(f"Error checking bot membership in channel {channel_id}: {e}")
                    channel_links[channel_id] = "https://t.me/+error"
                    channel_names[channel_id] = "Unknown Channel"
                    continue

                try:
                    chat = await context.bot.get_chat(chat_id=channel_id)
                    channel_names[channel_id] = chat.title or "Unknown Channel"
                    logger.info(f"Fetched name for channel {channel_id}: {channel_names[channel_id]}")
                except Exception as e:
                    logger.error(f"Error fetching channel name for {channel_id}: {e}")
                    channel_names[channel_id] = "Unknown Channel"

                try:
                    invite_link = await context.bot.export_chat_invite_link(chat_id=channel_id)
                    channel_links[channel_id] = invite_link
                    logger.info(f"Generated invite link for channel {channel_id}: {invite_link}")
                except Exception as e:
                    logger.error(f"Error generating invite link for channel {channel_id}: {e}")
                    channel_links[channel_id] = "https://t.me/+error"

            keyboard = [
                [
                    InlineKeyboardButton(channel_names[REQUIRED_CHANNELS[0]], url=channel_links[REQUIRED_CHANNELS[0]]),
                    InlineKeyboardButton(channel_names[REQUIRED_CHANNELS[1]], url=channel_links[REQUIRED_CHANNELS[1]])
                ],
                [
                    InlineKeyboardButton(channel_names[REQUIRED_CHANNELS[2]], url=channel_links[REQUIRED_CHANNELS[2]]),
                    InlineKeyboardButton(channel_names[REQUIRED_CHANNELS[3]], url=channel_links[REQUIRED_CHANNELS[3]])
                ],
                [InlineKeyboardButton("Check Subscription ✅", callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                "Please subscribe to the following channels to continue: 📢",
                reply_markup=reply_markup
            )

def main():
    request = HTTPXRequest(read_timeout=20)
    application = Application.builder().token(BOT_TOKEN).request(request).build()

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("stats", admin.stats))
    application.add_handler(CommandHandler("broadcast", admin.broadcast))
    application.add_handler(CommandHandler("ban_user", admin.ban_user))
    application.add_handler(CommandHandler("unban_user", admin.unban_user))
    application.add_handler(CommandHandler("banned_users", admin.banned_users))
    application.add_handler(CommandHandler("users", admin.users))
    application.add_handler(CommandHandler("add_bonus", admin.add_bonus))
    application.add_handler(CommandHandler("set_referral_reward", admin.set_referral_reward))
    application.add_handler(MessageHandler(filters.Regex(r'^/start\s+\S+'), start.start))
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/withdraw"), withdrawal.withdraw))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, withdrawal.handle_withdrawal_details))
    application.add_handler(CallbackQueryHandler(withdrawal.handle_admin_receipt, pattern=r'^(approve_withdrawal_|reject_withdrawal_)'))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == '__main__':
    main()