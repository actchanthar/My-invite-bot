# plugins/start.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from config import *
from database.database import get_user, update_user
from helper_func import is_subscribed
import logging
from datetime import datetime, timezone

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    user = await get_user(user_id)
    if not user:
        await update_user(user_id, {
            "username": username,
            "first_name": first_name,
            "balance": 0,
            "referrals": 0,
            "per_referral_earning": PER_REFERRAL_EARNING,
            "referral_threshold": REFERRAL_THRESHOLD,
            "referral_reward": REFERRAL_REWARD,
            "last_withdrawal": None,
            "withdrawn_today": 0,
            "banned": False
        })
        user = await get_user(user_id)

    if user.get("banned", False):
        await update.message.reply_text("You are banned from using this bot.")
        return

    # Log user start
    try:
        await context.bot.send_message(
            chat_id=LOG_CHANNEL,
            text=(
                f"User started the bot:\n"
                f"User ID: {user_id}\n"
                f"Username: {username or 'N/A'}\n"
                f"First Name: {first_name}\n"
                f"Date: {update.message.date}"
            )
        )
        logger.info(f"Logged user start for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send log message to LOG_CHANNEL: {e}")

    # Check subscription to required channels
    all_subscribed = await is_subscribed(context.bot, user_id)
    if not all_subscribed:
        channels = await db.show_channels()
        unsubscribed_channels = []
        for channel_id, invite_link in channels:
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if chat_member.status not in ["member", "administrator", "creator"]:
                    unsubscribed_channels.append((channel_id, invite_link))
            except Exception as e:
                logger.error(f"Error checking subscription for channel {channel_id}: {e}")
                unsubscribed_channels.append((channel_id, invite_link))

        if unsubscribed_channels:
            channel_links = {}
            channel_names = {}
            for channel_id, invite_link in unsubscribed_channels:
                try:
                    chat = await context.bot.get_chat(chat_id=channel_id)
                    channel_names[channel_id] = chat.title or "Unknown Channel"
                    channel_links[channel_id] = invite_link or f"https://t.me/c/{str(channel_id)[4:]}"
                except Exception as e:
                    logger.error(f"Error fetching channel name for {channel_id}: {e}")
                    channel_names[channel_id] = "Unknown Channel"
                    channel_links[channel_id] = invite_link or f"https://t.me/c/{str(channel_id)[4:]}"

            keyboard = [
                [InlineKeyboardButton(channel_names[ch_id], url=channel_links[ch_id]) for ch_id, _ in unsubscribed_channels[i:i+2]]
                for i in range(0, len(unsubscribed_channels), 2)
            ]
            keyboard.append([InlineKeyboardButton("Check Subscription ✅", callback_data="check_subscription")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await update.message.reply_photo(
                    photo=FORCE_SUB_IMAGE,
                    caption="Please subscribe to the following channels to continue: 📢",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error sending Force-Sub image: {e}")
                await update.message.reply_text(
                    "Please subscribe to the following channels to continue: 📢",
                    reply_markup=reply_markup
                )
            return

    # Handle referral if present
    args = context.args
    if args:
        referrer_id = args[0]
        if referrer_id != str(user_id):
            referrer = await get_user(int(referrer_id))
            if referrer:
                new_referrals = referrer.get("referrals", 0) + 1
                new_balance = referrer.get("balance", 0) + PER_REFERRAL_EARNING
                await update_user(int(referrer_id), {
                    "referrals": new_referrals,
                    "balance": new_balance
                })
                try:
                    rounded_balance = round(new_balance, 0)
                    await context.bot.send_message(
                        chat_id=LOG_CHANNEL,
                        text=(
                            f"New referral:\n"
                            f"Referrer ID: {referrer_id}\n"
                            f"New User ID: {user_id}\n"
                            f"Reward: {PER_REFERRAL_EARNING} MMK\n"
                            f"Referrer's New Balance: {rounded_balance} MMK\n"
                            f"Referrer's Total Referrals: {new_referrals}"
                        )
                    )
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            f"🎉 A new user joined using your referral link! "
                            f"You earned {PER_REFERRAL_EARNING} MMK. "
                            f"Your new balance is {rounded_balance} MMK. 🙂"
                        )
                    )
                    logger.info(f"Logged referral for referrer {referrer_id} and new user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send referral log to LOG_CHANNEL: {e}")

    # Show welcome message
    balance = round(user.get("balance", 0), 0)
    referrals = user.get("referrals", 0)
    per_referral = round(user.get("per_referral_earning", PER_REFERRAL_EARNING), 0)
    referral_threshold = user.get("referral_threshold", REFERRAL_THRESHOLD)
    referral_reward = round(user.get("referral_reward", REFERRAL_REWARD), 0)
    total_referral_earnings = round(referrals * per_referral, 0)
    bonus_earnings = round((referrals // referral_threshold) * referral_reward, 0)
    total_earnings = round(total_referral_earnings + bonus_earnings, 0)

    welcome_message = (
        f"Welcome back, {first_name} Sama! 👋\n\n"
        f"Current Balance: {balance} MMK 💸\n"
        f"Number of Referrals: {referrals} 👥\n"
        f"Earnings Per Referral: {per_referral} MMK 💰\n"
        f"Total Referral Earnings: {total_referral_earnings} MMK 📈\n"
        f"Bonus ({referral_threshold} Referrals for {referral_reward} MMK 🎁): {bonus_earnings} MMK\n"
        f"Total Earnings: {total_earnings} MMK 🤑"
    )

    keyboard = [
        [
            InlineKeyboardButton("Get Referral Link 🔗", callback_data="get_referral_link"),
            InlineKeyboardButton("Check Balance 💰", callback_data="check_balance")
        ],
        [
            InlineKeyboardButton("Withdraw 💸", callback_data="withdraw"),
            InlineKeyboardButton("Help ❓", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(
            photo=START_IMAGE,
            caption=welcome_message,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send start image: {e}")
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )