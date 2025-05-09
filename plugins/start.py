# plugins/start.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from config import OWNER_ID
from database.database import get_user, update_user, show_channels
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_subscribed(bot, user_id):
    channel_ids = await show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid, _ in channel_ids:
        try:
            member = await bot.get_chat_member(cid, user_id)
            if member.status not in {"creator", "administrator", "member"}:
                return False
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id} in channel {cid}: {e}")
            return False

    return True

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    args = context.args

    if args:
        referrer_id = int(args[0])
        if referrer_id != user_id:
            await update_user(user_id, user.first_name, referrer_id)
        else:
            referrer_id = None
    else:
        referrer_id = None

    user_data = await get_user(user_id)
    if not user_data:
        await update_user(user_id, user.first_name, referrer_id)
        user_data = await get_user(user_id)

    balance = user_data.get("balance", 0)
    all_subscribed = await is_subscribed(context.bot, user_id)

    if not all_subscribed:
        channels = await show_channels()
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
            keyboard.append([InlineKeyboardButton("စာရင်းသွင်းမှု စစ်ဆေးရန် ✅", callback_data="check_subscription")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "ဆက်လက်အသုံးပြုရန် အောက်ပါ ချန်နယ်များသို့ ဝင်ရောက်ပါ။ 📢",
                reply_markup=reply_markup
            )
            return

    keyboard = [
        [InlineKeyboardButton("လက်ကျန်ငွေ စစ်ဆေးရန် 💰", callback_data="check_balance")],
        [InlineKeyboardButton("ရည်ညွှန်းလင့်ခ် ရယူရန် 🔗", callback_data="get_referral_link")],
        [InlineKeyboardButton("ငွေထုတ်ရန် 💸", callback_data="withdraw")],
        [InlineKeyboardButton("အကူအညီ ❓", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 မင်္ဂလာပါ {user.first_name}!\n\n"
        f"သင့်လက်ကျန်ငွေ: {balance} ကျပ် 💸\n"
        f"ရည်ညွှန်းလင့်ခ်ကို အသုံးပြုပြီး သူငယ်ချင်းများကို ဖိတ်ကြားကာ ဆုလာဘ်များ ရယူပါ။ 🎉",
        reply_markup=reply_markup
    )