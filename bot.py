# bot.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ChatMemberUpdatedHandler, ChatJoinRequestHandler
from telegram.request import HTTPXRequest
import logging
from config import *
from database.database import get_user, update_user
from plugins import start, admin, referral, withdrawal, request_fsub

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def guide(update: Update, context: CallbackContext):
    guide_message = (
        "📘 **ဘော့ကို ဘယ်လိုအသုံးပြုရမလဲ**\n\n"
        "1. **ဘော့ကို စတင်ပါ**\n"
        "- `/start` ကို ပို့ပါ။\n"
        "- သင့်လက်ကျန်ငွေနဲ့ မီနူးပါတဲ့ ကြိုဆိုမှုစာကို တွေ့ရပါလိမ့်မယ်။\n\n"
        "2. **လိုအပ်သော ချန်နယ်များသို့ ဝင်ရောက်ပါ**\n"
        "- တောင်းဆိုထားတဲ့ ချန်နယ်တွေကို လင့်ခ်တွေနှိပ်ပြီး ဝင်ပါ။\n"
        "- အားလုံးဝင်ရောက်ပြီးရင် 'စာရင်းသွင်းမှု စစ်ဆေးရန် ✅' ကို နှိပ်ပါ။\n"
        "- `/start` ကို ထပ်ပို့ပြီး ဆက်လက်ပါ။\n\n"
        "3. **ရည်ညွှန်းမှုဖြင့် ငွေရှာပါ**\n"
        "- 'ရည်ညွှန်းလင့်ခ် ရယူရန် 🔗' ကို နှိပ်ပြီး သင့်လင့်ခ်ကို ရယူပါ။\n"
        "- သူငယ်ချင်းတွေနဲ့ မျှဝေပါ။\n"
        "- ရည်ညွှန်းသူတစ်ဦးလျှင် ၁ ကျပ် ရရှိပါမယ်။\n"
        "- စာတစ်စောင်ရရှိပါလိမ့်မယ်။ '🎉 သင့်ရည်ညွှန်းလင့်ခ်ကို အသုံးပြုပြီး အသုံးပြုသူ အသစ်တစ်ဦး ဝင်ရောက်ခဲ့ပါတယ်။ သင်ဟာ ၁ ကျပ် ရရှိခဲ့ပါတယ်။ သင့်လက်ကျန်ငွေ အသစ်က [လက်ကျန်ငွေ] ကျပ် ဖြစ်ပါတယ်။ 🙂'\n\n"
        "4. **သင့်လက်ကျန်ငွေကို စစ်ဆေးပါ**\n"
        "- 'လက်ကျန်ငွေ စစ်ဆေးရန် 💰' ကို နှိပ်ပါ။\n\n"
        "5. **သင့်ဝင်ငွေကို ထုတ်ယူပါ**\n"
        "- 'ငွေထုတ်ရန် 💸' ကို နှိပ်ပါ။\n"
        "- ပမာဏကို ရိုက်ထည့်ပါ (အနည်းဆုံး 1000 ကျပ်)။\n"
        "- ငွေပေးချေမှု အသေးစိတ် (ဥပမာ KBZ Pay 09123456789 ZAYAR KO KO MIN ZAW ) ပေးပါ။\n"
        "- အက်ဒမင် အတည်ပြုမှုကို စောင့်ပါ။\n\n"
        "6. **အကူအညီ ရယူပါ**\n"
        "- 'အကူအညီ ❓' ကို နှိပ်ပါ။\n\n"
        "**အကြံပြုချက်များ**:\n"
        "- အနည်းဆုံး ငွေထုတ်ပမာဏ: 1000 ကျပ်။\n"
        "- လိုအပ်သော ချန်နယ်များမှာ ဆက်လက်စာရင်းသွင်းထားပါ။\n"
        "- အကူအညီလိုရင် @actanibot ကို ဆက်သွယ်ပါ�।"
    )
    await update.message.reply_text(guide_message, parse_mode="Markdown")

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
        await query.message.reply_text(f"သင့်ရည်ညွှန်းလင့်ခ်: {referral_link}")
    elif data == "check_balance":
        user = await get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found in database when checking balance")
            await query.message.reply_text("User not found. Please start with /start.")
            return
        balance = round(user.get("balance", 0), 0)
        referrals = user.get("referrals", 0)
        per_referral = round(user.get("per_referral_earning", PER_REFERRAL_EARNING), 0)
        referral_threshold = user.get("referral_threshold", REFERRAL_THRESHOLD)
        referral_reward = round(user.get("referral_reward", REFERRAL_REWARD), 0)
        total_referral_earnings = round(referrals * per_referral, 0)
        bonus_earnings = round((referrals // referral_threshold) * referral_reward, 0)
        total_earnings = round(total_referral_earnings + bonus_earnings, 0)
        await query.message.reply_text(
            f"လက်ရှိလက်ကျန်ငွေ: {balance} ကျပ် 💸\n"
            f"ရည်ညွှန်းသူ အရေအတွက်: {referrals} 👥\n"
            f"ရည်ညွှန်းသူတစ်ဦးလျှင် ဝင်ငွေ: {per_referral} ကျပ် 💰\n"
            f"စုစုပေါင်း ရည်ညွှန်းဝင်ငွေ: {total_referral_earnings} ကျပ် 📈\n"
            f"ဘောနပ်စ် ({referral_threshold} ရည်ညွှန်းသူအတွက် {referral_reward} ကျပ် 🎁): {bonus_earnings} ကျပ်\n"
            f"စုစုပေါင်း ဝင်ငွေ: {total_earnings} ကျပ် 🤑"
        )
    elif data == "withdraw":
        await withdrawal.withdraw(update, context)
    elif data == "help":
        await query.message.reply_text(
            "အကူအညီ:\n"
            "/start - ဘော့ကို စတင်ပါ 🚀\n"
            "/withdraw - ငွေထုတ်ပါ 💸\n"
            "/guide - ဘော့ကို ဘယ်လိုအသုံးပြုရမလဲ 📘\n"
            "သင့်ရည်ညွှန်းလင့်ခ်ကို မျှဝေပြီး ဆုလာဘ်များ ရယူပါ။ 🔗"
        )
    elif data == "back":
        await start.start(update, context)
    elif data == "check_subscription":
        logger.info(f"check_subscription triggered for user {user_id}")
        all_subscribed = await request_fsub.is_subscribed(context.bot, user_id)
        if all_subscribed:
            await query.message.reply_text("သင်အောင်မြင်စွာ ဝင်ရောက်ပြီးပါပြီ။ ဆက်လက်ရန် /start ကို အသုံးပြုပါ။")
        else:
            channels = await request_fsub.db.show_channels()
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

                await query.message.edit_text(
                    "ဆက်လက်အသုံးပြုရန် အောက်ပါ ချန်နယ်များသို့ ဝင်ရောက်ပါ။ 📢",
                    reply_markup=reply_markup
                )

def main():
    request = HTTPXRequest(read_timeout=20)
    application = Application.builder().token(BOT_TOKEN).request(request).build()

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("guide", guide))
    application.add_handler(CommandHandler("stats", admin.stats))
    application.add_handler(CommandHandler("broadcast", admin.broadcast))
    application.add_handler(CommandHandler("ban_user", admin.ban_user))
    application.add_handler(CommandHandler("unban_user", admin.unban_user))
    application.add_handler(CommandHandler("banned_users", admin.banned_users))
    application.add_handler(CommandHandler("users", admin.users))
    application.add_handler(CommandHandler("add_bonus", admin.add_bonus))
    application.add_handler(CommandHandler("set_referral_reward", admin.set_referral_reward))
    application.add_handler(CommandHandler("addchnl", request_fsub.add_force_sub))
    application.add_handler(CommandHandler("delchnl", request_fsub.del_force_sub))
    application.add_handler(CommandHandler("listchnl", request_fsub.list_force_sub_channels))
    application.add_handler(CommandHandler("fsub_mode", request_fsub.change_force_sub_mode))
    application.add_handler(MessageHandler(filters.Regex(r'^/start\s+\S+'), start.start))
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/withdraw"), withdrawal.withdraw))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, withdrawal.handle_withdrawal_details))
    application.add_handler(CallbackQueryHandler(withdrawal.handle_admin_receipt, pattern=r'^(approve_withdrawal_|reject_withdrawal_)'))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(ChatMemberUpdatedHandler(request_fsub.handle_chat_member_updated))
    application.add_handler(ChatJoinRequestHandler(request_fsub.handle_join_request))

    application.run_polling()

if __name__ == '__main__':
    main()