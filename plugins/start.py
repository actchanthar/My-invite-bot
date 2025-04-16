import logging
import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from config import FORCE_SUB_CHANNELS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

# URL for the start image (replace with your actual image URL)
START_IMAGE_URL = "https://i.imghippo.com/files/fgmj5944fE.jpg"

async def check_subscription(client, user_id):
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            logger.info(f"User {user_id} status in {channel}: {member.status}")
            if member.status not in ["member", "administrator", "creator"]:
                logger.info(f"User {user_id} is not subscribed to {channel}")
                return False
            logger.info(f"User {user_id} is subscribed to {channel}")
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id} in {channel}: {e}")
            return False
    return True

async def handle_start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    referral_id = None

    try:
        logger.info(f"Handling /start for user {user_id}, referral_id: {message.command[1] if len(message.command) > 1 else None}")
        if len(message.command) > 1:
            encoded_referral = message.command[1]
            try:
                # Decode the Base64-encoded referral ID
                decoded_referral = base64.b64decode(encoded_referral).decode('utf-8')
                # Extract the actual referral ID (assuming format like "get-<referrer_id>")
                if decoded_referral.startswith("get-"):
                    referral_id = int(decoded_referral.split("-")[1])
                else:
                    logger.warning(f"Invalid referral format for user {user_id}: {decoded_referral}")
            except (base64.binascii.Error, ValueError) as e:
                logger.error(f"Error decoding referral for user {user_id}: {e}")

        user = await db.get_user(user_id)
        if not user:
            logger.info(f"User {user_id} not found in database, adding new user")
            await db.add_user(user_id, username, referral_id)
            if referral_id:
                await db.update_referrals(referral_id)
        else:
            logger.info(f"User {user_id} already exists in database: {user}")

        if not await check_subscription(client, user_id):
            buttons = []
            for channel in FORCE_SUB_CHANNELS:
                invite_link = await client.export_chat_invite_link(channel)
                buttons.append([InlineKeyboardButton(f"Join {channel}", url=invite_link)])
            buttons.append([InlineKeyboardButton("Check Subscription", callback_data="check_sub")])
            await message.reply(
                "Please join the following channels to proceed:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        # Send welcome message with image and navigation buttons
        buttons = [
            [InlineKeyboardButton("Profile", callback_data="profile")],
            [InlineKeyboardButton("Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("Invite Link", callback_data="invite")]
        ]
        await client.send_photo(
            chat_id=user_id,
            photo=START_IMAGE_URL,
            caption="Welcome! Use the buttons below to navigate.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in handle_start for user {user_id}: {e}")
        await message.reply("Error processing your request. Please try again later.")