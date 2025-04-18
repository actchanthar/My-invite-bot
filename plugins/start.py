import logging
import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNELS
from database.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def resolve_channel_id(client, channel):
    try:
        if isinstance(channel, str) and channel.startswith("@"):
            chat = await client.get_chat(channel)
            logger.info(f"Resolved {channel} to chat ID {chat.id}")
            return chat.id
        return int(channel)
    except Exception as e:
        logger.error(f"Error resolving channel {channel}: {e}")
        return None

async def check_subscription(client, user_id):
    for channel in FORCE_SUB_CHANNELS:
        channel_id = await resolve_channel_id(client, channel)
        if not channel_id:
            logger.warning(f"Skipping invalid channel: {channel}")
            continue
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR, ChatMemberStatus.RESTRICTED]:
                logger.info(f"User {user_id} not subscribed to {channel_id}, status: {member.status}")
                return False
            logger.info(f"User {user_id} is subscribed to {channel_id}, status: {member.status}")
        except Exception as e:
            logger.error(f"Error checking subscription for {channel_id}: {e}")
            return False
    return True

async def handle_start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    referral_id = None

    logger.info(f"Handling /start for user {user_id}, referral_id: {message.command[1] if len(message.command) > 1 else None}")

    if len(message.command) > 1:
        encoded_referral = message.command[1]
        try:
            decoded_referral = base64.b64decode(encoded_referral).decode('utf-8')
            if decoded_referral.startswith("get-"):
                referral_id = int(decoded_referral.split("-")[1])
            else:
                logger.warning(f"Invalid referral format for user {user_id}: {decoded_referral}")
        except (base64.binascii.Error, ValueError) as e:
            logger.error(f"Error decoding referral for user {user_id}: {e}")

    if await db.get_user(user_id) is None:
        await db.add_user(user_id, username, referral_id)
        if referral_id:
            try:
                await db.update_referrals(referral_id)
                logger.info(f"Processed referral for {referral_id}")
            except Exception as e:
                logger.error(f"Error processing referral {referral_id}: {e}")

    if not await check_subscription(client, user_id):
        buttons = []
        for channel in FORCE_SUB_CHANNELS:
            channel_id = await resolve_channel_id(client, channel)
            if channel_id:
                try:
                    chat = await client.get_chat(channel_id)
                    invite_link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(channel_id)
                    buttons.append([InlineKeyboardButton(f"Join {chat.title or 'Channel'}", url=invite_link)])
                    logger.info(f"Generated join button for {channel_id}: {invite_link}")
                except Exception as e:
                    logger.error(f"Error generating invite link for {channel_id}: {e}")
        buttons.append([InlineKeyboardButton("Check Subscription", callback_data="check_sub")])
        await message.reply_photo(
            photo="https://i.imghippo.com/files/fgmj5944fE.jpg",
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
        photo="https://i.imghippo.com/files/fgmj5944fE.jpg",
        caption=f"Welcome, @{username}!\nUse the buttons below to navigate.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def check_sub_callback(client, callback_query):
    user_id = callback_query.from_user.id
    logger.info(f"Checking subscription for user {user_id} via callback")
    if await check_subscription(client, user_id):
        await callback_query.message.delete()
        message = callback_query.message
        message.from_user.id = user_id
        message.command = ["start"]
        await handle_start(client, message)
    else:
        await callback_query.answer("You haven't joined all channels yet!")
