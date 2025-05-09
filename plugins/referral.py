# plugins/referral.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database.database import get_user, update_user
from config import LOG_CHANNEL, PER_REFERRAL_EARNING, REQUIRED_CHANNELS, FORCE_SUB_IMAGE

async def handle_referral_link(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if len(update.message.text.split()) < 2:
        print(f"No referral code provided for user {user_id}")
        await update.message.reply_text("Please start with a valid referral link or use /start.")
        return

    referral_code = update.message.text.split()[1]
    print(f"handle_referral_link triggered for user {user_id} with referral code {referral_code}")

    if not referral_code.isdigit():
        print(f"Referral code {referral_code} is not a valid user ID")
        await update.message.reply_text("Invalid referral link. Please use a valid referral link or start with /start.")
        return

    referrer_id = int(referral_code)
    referrer = await get_user(referrer_id)
    print(f"Referral code {referral_code} resolved to referrer_id {referrer_id}")

    if not referrer or (referrer_id == user_id):
        print(f"Invalid referral code {referral_code} or self-referral by user {user_id}")
        await update.message.reply_text("Invalid referral link. Please use a valid referral link or start with /start.")
        return

    context.user_data["referrer_id"] = referrer_id
    print(f"Stored referrer_id {referrer_id} for user {user_id} in context.user_data")

    user = await get_user(user_id)
    if user:
        print(f"User {user_id} already registered with referrer_id {user.get('referrer_id')}")
        if not user.get("referrer_id"):
            print(f"Setting referrer_id {referrer_id} for existing user {user_id}")
            success = await update_user(user_id, {"referrer_id": referrer_id})
            if success:
                print(f"Successfully updated existing user {user_id} with referrer_id {referrer_id}")
            else:
                print(f"Failed to update user {user_id} with referrer_id {referrer_id} in database")
                await update.message.reply_text("Error saving referral data. Please try again or contact support.")
                return
        else:
            print(f"User {user_id} already has referrer_id {user.get('referrer_id')}, skipping update")
    else:
        print(f"Registering new user {user_id} with referrer_id {referrer_id}")
        user_data = {
            "user_id": user_id,
            "balance": 0,
            "referrals": 0,
            "referrer_id": referrer_id,
            "banned": False,
            "last_withdrawal": None,
            "withdrawn_today": 0,
            "subscribed": False,
            "referral_credited": False
        }
        success = await update_user(user_id, user_data)
        if not success:
            print(f"Failed to register user {user_id} with referrer_id {referrer_id} in database")
            await update.message.reply_text("Error registering user. Please try again.")
            return
        print(f"Successfully registered user {user_id} with referrer_id {referrer_id}")

    await prompt_subscription(update, context, user_id)

async def prompt_subscription(update: Update, context: CallbackContext, user_id: int):
    channel_links = {}
    channel_names = {}
    for channel_id in REQUIRED_CHANNELS:
        try:
            bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
            if bot_member.status not in ["member", "administrator", "creator"]:
                print(f"Bot is not a member of channel {channel_id}, cannot generate invite link")
                channel_links[channel_id] = "https://t.me/+error"
                channel_names[channel_id] = "Unknown Channel"
                continue
        except Exception as e:
            print(f"Error checking bot membership in channel {channel_id}: {e}")
            channel_links[channel_id] = "https://t.me/+error"
            channel_names[channel_id] = "Unknown Channel"
            continue

        try:
            chat = await context.bot.get_chat(chat_id=channel_id)
            channel_names[channel_id] = chat.title or "Unknown Channel"
        except Exception as e:
            print(f"Error fetching channel name for {channel_id}: {e}")
            channel_names[channel_id] = "Unknown Channel"

        try:
            invite_link = await context.bot.export_chat_invite_link(chat_id=channel_id)
            channel_links[channel_id] = invite_link
            print(f"Generated invite link for channel {channel_id}: {invite_link}")
        except Exception as e:
            print(f"Error generating invite link for channel {channel_id}: {e}")
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
    print(f"Prompting user {user_id} to subscribe to channels")

    try:
        await update.message.reply_photo(
            photo=FORCE_SUB_IMAGE,
            caption="Please subscribe to the following channels to continue: 📢",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error sending Force Subscription image: {e}")
        await update.message.reply_text(
            "Please subscribe to the following channels to continue: 📢",
            reply_markup=reply_markup
        )

async def register_user_and_credit_referrer(update: Update, context: CallbackContext, user_id: int, referrer: dict):
    print(f"Registering user {user_id} and crediting referrer {referrer['user_id']}")
    
    user = await get_user(user_id)
    if not user:
        user_data = {
            "user_id": user_id,
            "balance": 0,
            "referrals": 0,
            "referrer_id": referrer["user_id"],
            "banned": False,
            "last_withdrawal": None,
            "withdrawn_today": 0,
            "subscribed": True,
            "referral_credited": False
        }
        success = await update_user(user_id, user_data)
        if not success:
            print(f"Failed to register user {user_id} in database")
            await update.message.reply_text("Error registering user. Please try again.")
            return
    else:
        await update_user(user_id, {"subscribed": True})

    referrer_id = referrer["user_id"]
    current_referrals = referrer.get("referrals", 0)
    current_balance = referrer.get("balance", 0)
    new_referrals = current_referrals + 1
    new_balance = current_balance + PER_REFERRAL_EARNING
    success = await update_user(referrer_id, {"referrals": new_referrals, "balance": new_balance})
    if not success:
        print(f"Failed to update referrer {referrer_id} in database")
        await update.message.reply_text("Error crediting referrer. Please contact support.")
        return

    print(f"Updated referrer {referrer_id}: Referrals={new_referrals}, Balance={new_balance}")

    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=(
            f"New referral:\n"
            f"Referrer ID: {referrer_id}\n"
            f"New User ID: {user_id}\n"
            f"Reward: {PER_REFERRAL_EARNING} MMK\n"
            f"Referrer's New Balance: {new_balance} MMK\n"
            f"Referrer's Total Referrals: {new_referrals}"
        )
    )

    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=f"🎉 A new user joined using your referral link! You earned {PER_REFERRAL_EARNING} MMK. Your new balance is {new_balance} MMK."
        )
        print(f"Notified referrer {referrer_id} of new referral")
    except Exception as e:
        print(f"Failed to notify referrer {referrer_id}: {e}")

    await update_user(user_id, {"referral_credited": True})
    await update.message.reply_text("You have successfully joined! Use /start to continue.")