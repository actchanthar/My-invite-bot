from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import FORCE_SUB_CHANNELS
from database.database import Database

db = Database()

async def resolve_channel_id(client, channel):
    """Resolve a channel username or ID to a chat ID."""
    try:
        if isinstance(channel, str) and channel.startswith("@"):
            chat = await client.get_chat(channel)
            return chat.id
        return int(channel)  # Assume it's already a chat ID
    except Exception as e:
        print(f"Error resolving channel {channel}: {e}")
        return None

async def check_subscription(client, user_id):
    for channel in FORCE_SUB_CHANNELS:
        channel_id = await resolve_channel_id(client, channel)
        if not channel_id:
            continue
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

async def handle_start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    referral_id = message.command[1] if len(message.command) > 1 else None

    if await db.get_user(user_id) is None:
        await db.add_user(user_id, username, referral_id)
        if referral_id:
            await db.update_referrals(int(referral_id))

    if not await check_subscription(client, user_id):
        buttons = []
        for channel in FORCE_SUB_CHANNELS:
            channel_id = await resolve_channel_id(client, channel)
            if channel_id:
                chat = await client.get_chat(channel_id)
                invite_link = chat.username if chat.username else f"https://t.me/c/{str(channel_id)[4:]}"
                buttons.append([InlineKeyboardButton(f"Join {chat.title or 'Channel'}", url=f"https://t.me/{invite_link}")])
        buttons.append([InlineKeyboardButton("Check Subscription", callback_data="check_sub")])
        await message.reply_photo(
            photo="https://example.com/welcome.jpg",
            caption="Please join all required channels to use the bot!",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    buttons = [
        [InlineKeyboardButton("Profile", callback_data="profile")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("Invite Link", callback_data="invite")]
    ]
    await message.reply_photo(
        photo="https://example.com/welcome.jpg",
        caption=f"Welcome, @{username}!\nUse the buttons below to navigate.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )