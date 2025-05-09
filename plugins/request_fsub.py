# plugins/request_fsub.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database.database import *
from config import OWNER_ID
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    return user_id == OWNER_ID

async def add_force_sub(update: Update, context: CallbackContext):
    if not await check_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    temp = await update.message.reply_text("<b><i>Wait a sec...</i></b>", quote=True)
    args = update.message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit_text(
            "<b>Usage:</b> <code>/addchnl -100XXXXXXXXXX</code>\n<b>Add only one channel at a time.</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        )

    try:
        channel_id = int(args[1])
    except ValueError:
        return await temp.edit_text("<b>❌ Invalid Channel ID!</b>")

    all_channels = await show_channels()
    channel_ids_only = [cid[0] for cid in all_channels]
    if channel_id in channel_ids_only:
        return await temp.edit_text(f"<b>Channel already exists:</b> <code>{channel_id}</code>")

    try:
        chat = await context.bot.get_chat(channel_id)
        if chat.type != "channel":
            return await temp.edit_text("<b>❌ Only public or private channels are allowed.</b>")

        member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if member.status not in ["administrator", "creator"]:
            return await temp.edit_text("<b>❌ Bot must be an admin in that channel.</b>")

        invite_link = await get_channel_invite_link(channel_id)
        if not invite_link:
            if chat.username:
                invite_link = f"https://t.me/{chat.username}"
            else:
                try:
                    invite_link = await context.bot.export_chat_invite_link(chat.id)
                except Exception:
                    invite_link = f"https://t.me/c/{str(chat.id)[4:]}"
            await add_channel(channel_id, invite_link)
        else:
            await add_channel(channel_id, invite_link)

        return await temp.edit_text(
            f"<b>✅ Force-sub channel added successfully!</b>\n\n"
            f"<b>Name:</b> <a href='{invite_link}'>{chat.title}</a>\n"
            f"<b>ID:</b> <code>{channel_id}</code>",
            disable_web_page_preview=True
        )
    except Exception as e:
        return await temp.edit_text(f"<b>❌ Failed to add channel:</b>\n<code>{channel_id}</code>\n\n<i>{e}</i>")

async def del_force_sub(update: Update, context: CallbackContext):
    if not await check_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    temp = await update.message.reply_text("<b><i>Wait a sec...</i></b>", quote=True)
    args = update.message.text.split(maxsplit=1)
    all_channels = await show_channels()

    if len(args) != 2:
        return await temp.edit_text("<b>Usage:</b> <code>/delchnl <channel_id | all></code>")

    if args[1].lower() == "all":
        if not all_channels:
            return await temp.edit_text("<b>❌ No force-sub channels found.</b>")
        for ch_id, _ in all_channels:
            await rem_channel(ch_id)
        return await temp.edit_text("<b>✅ All force-sub channels have been removed.</b>")

    try:
        ch_id = int(args[1])
    except ValueError:
        return await temp.edit_text("<b>❌ Invalid Channel ID</b>")

    if ch_id in [cid[0] for cid in all_channels]:
        await rem_channel(ch_id)
        return await temp.edit_text(f"<b>✅ Channel removed:</b> <code>{ch_id}</code>")
    else:
        return await temp.edit_text(f"<b>❌ Channel not found in force-sub list:</b> <code>{ch_id}</code>")

async def list_force_sub_channels(update: Update, context: CallbackContext):
    if not await check_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    temp = await update.message.reply_text("<b><i>Wait a sec...</i></b>", quote=True)
    channels = await show_channels()

    if not channels:
        return await temp.edit_text("<b>❌ No force-sub channels found.</b>")

    result = "<b>⚡ Force-sub Channels:</b>\n\n"
    for ch_id, invite_link in channels:
        try:
            chat = await context.bot.get_chat(ch_id)
            link = invite_link or (chat.invite_link or await context.bot.export_chat_invite_link(ch_id))
            result += f"<b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]\n"
        except Exception:
            result += f"<b>•</b> <code>{ch_id}</code> — <i>Unavailable</i>\n"

    await temp.edit_text(
        result,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
    )

async def change_force_sub_mode(update: Update, context: CallbackContext):
    if not await check_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    temp = await update.message.reply_text("<b><i>Wait a sec...</i></b>", quote=True)
    channels = await show_channels()

    if not channels:
        return await temp.edit_text("<b>❌ No force-sub channels found.</b>")

    buttons = []
    for ch_id, _ in channels:
        try:
            chat = await context.bot.get_chat(ch_id)
            mode = await get_channel_mode(ch_id)
            status = "🟢" if mode == "on" else "🔴"
            title = f"{status} {chat.title}"
            buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
        except:
            buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])

    buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])

    await temp.edit_text(
        "<b>⚡ Select a channel to toggle Force-Sub Mode:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

async def handle_chat_member_updated(update: Update, context: CallbackContext):
    message = update.message
    if not message:
        return

    chat_id = message.chat.id
    if await reqChannel_exist(chat_id):
        for member in message.new_chat_members or []:
            if member.id == context.bot.id:
                logger.info(f"Bot added to channel {chat_id}")
                return
        if message.left_chat_member:
            user_id = message.left_chat_member.id
            if await req_user_exist(chat_id, user_id):
                await del_req_user(chat_id, user_id)
                logger.info(f"Removed join request for user {user_id} in channel {chat_id}")