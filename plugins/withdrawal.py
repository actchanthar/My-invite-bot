import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from config import ADMIN_IDS, DEFAULT_EARNINGS_MMK

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

async def handle_withdraw(client, message):
    try:
        user = await db.get_user(message.from_user.id)
        if not user or user["earnings_mmk"] < DEFAULT_EARNINGS_MMK:
            await message.reply(f"You need at least {DEFAULT_EARNINGS_MMK} MMK to withdraw! Current balance: {user['earnings_mmk'] if user else 0} MMK")
            return
        buttons = [
            [InlineKeyboardButton("KBZ Pay", callback_data="withdraw_kbz")],
            [InlineKeyboardButton("Wave Pay", callback_data="withdraw_wave")]
        ]
        await message.reply(
            "Choose your withdrawal method:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in withdraw command: {e}")
        await message.reply("Error processing withdrawal request. Please try again later.")

async def handle_withdraw_callback(client, callback_query):
    try:
        user = await db.get_user(callback_query.from_user.id)
        if not user or user["earnings_mmk"] < DEFAULT_EARNINGS_MMK:
            await callback_query.message.reply(f"You need at least {DEFAULT_EARNINGS_MMK} MMK to withdraw! Current balance: {user['earnings_mmk'] if user else 0} MMK")
            await callback_query.answer()
            return
        buttons = [
            [InlineKeyboardButton("KBZ Pay", callback_data="withdraw_kbz")],
            [InlineKeyboardButton("Wave Pay", callback_data="withdraw_wave")]
        ]
        await callback_query.message.reply(
            "Choose your withdrawal method:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in withdraw callback: {e}")
        await callback_query.message.reply("Error processing withdrawal request. Please try again later.")

async def withdraw_method_callback(client, callback_query, method):
    try:
        user_id = callback_query.from_user.id
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return

        # Prompt user for account details based on method
        if method == "KBZ Pay":
            prompt = "Please send your address, KBZ Pay Number, and Account Name in the format:\nAddress, KBZ Pay Number, Account Name\nExample: 123 Main St, 09987654321, John Doe"
        else:  # Wave Pay
            prompt = "Please send your Wave Pay Account and Name in the format:\nWave Pay Account, Name\nExample: 09987654321, John Doe"

        # Store the pending withdrawal request in the database
        await db.add_pending_withdrawal(user_id, method, user["earnings_mmk"])

        await callback_query.message.reply(prompt)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in withdraw method callback: {e}")
        await callback_query.message.reply("Error sending withdrawal request. Please try again later.")

async def handle_account_details(client, message):
    try:
        user_id = message.from_user.id
        # Check if there's a pending withdrawal for this user
        pending_withdrawal = await db.get_pending_withdrawal(user_id)
        if not pending_withdrawal:
            await message.reply("No pending withdrawal request found. Please start the withdrawal process again.")
            return

        method = pending_withdrawal["method"]
        amount = pending_withdrawal["amount"]
        details = message.text

        # Validate the details format (basic check)
        if method == "KBZ Pay" and len(details.split(",")) != 3:
            await message.reply("Invalid format. Please send your address, KBZ Pay Number, and Account Name in the format:\nAddress, KBZ Pay Number, Account Name")
            return
        elif method == "Wave Pay" and len(details.split(",")) != 2:
            await message.reply("Invalid format. Please send your Wave Pay Account and Name in the format:\nWave Pay Account, Name")
            return

        # Update the pending withdrawal with the user's details
        await db.update_pending_withdrawal_details(user_id, details)

        # Notify the admin
        user = await db.get_user(user_id)
        for admin_id in ADMIN_IDS:
            buttons = [
                [InlineKeyboardButton("Approve", callback_data=f"approve_withdraw_{user_id}")],
                [InlineKeyboardButton("Deny", callback_data=f"deny_withdraw_{user_id}")]
            ]
            await client.send_message(
                admin_id,
                f"Withdrawal Request:\n"
                f"User ID: {user_id}\n"
                f"Username: @{user['username']}\n"
                f"Amount: {amount} MMK\n"
                f"Method: {method}\n"
                f"Details: {details}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        await message.reply("Withdrawal request sent to admin. You'll be notified soon!")
    except Exception as e:
        logger.error(f"Error handling account details: {e}")
        await message.reply("Error processing your details. Please try again later.")

async def approve_withdraw_callback(client, callback_query, user_id):
    try:
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("Unauthorized!")
            return
        user = await db.get_user(user_id)
        if not user:
            await callback_query.message.reply("User not found!")
            await callback_query.answer()
            return
        pending_withdrawal = await db.get_pending_withdrawal(user_id)
        if not pending_withdrawal:
            await callback_query.message.reply("No pending withdrawal request found for this user.")
            await callback_query.answer()
            return

        amount = pending_withdrawal["amount"]
        method = pending_withdrawal["method"]
        details = pending_withdrawal["details"]

        # Notify the admin to upload the receipt screenshot
        await callback_query.message.reply(
            "Please upload the receipt screenshot for this withdrawal.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel", callback_data=f"cancel_withdraw_{user_id}")]
            ])
        )
        # Store the approval state (waiting for screenshot)
        await db.update_pending_withdrawal_status(user_id, "awaiting_screenshot")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in approve withdraw callback: {e}")
        await callback_query.message.reply("Error approving withdrawal. Please try again later.")

async def handle_receipt_screenshot(client, message):
    try:
        admin_id = message.from_user.id
        if admin_id not in ADMIN_IDS:
            await message.reply("Unauthorized!")
            return
        if not message.photo:
            await message.reply("Please upload a photo of the receipt.")
            return

        # Find the user whose withdrawal is awaiting a screenshot
        pending_withdrawal = await db.get_pending_withdrawal_by_status("awaiting_screenshot")
        if not pending_withdrawal:
            await message.reply("No withdrawal request awaiting a screenshot.")
            return

        user_id = pending_withdrawal["user_id"]
        amount = pending_withdrawal["amount"]
        method = pending_withdrawal["method"]

        # Deduct the amount from the user's balance
        await db.update_earnings(user_id, -amount)

        # Send confirmation and screenshot to the user
        await client.send_photo(
            user_id,
            photo=message.photo.file_id,
            caption=f"Your withdrawal of {amount} MMK via {method} has been approved and processed!"
        )

        # Notify the admin
        await message.reply("Withdrawal processed successfully. Receipt sent to the user.")

        # Remove the pending withdrawal
        await db.remove_pending_withdrawal(user_id)
    except Exception as e:
        logger.error(f"Error handling receipt screenshot: {e}")
        await message.reply("Error processing the receipt. Please try again later.")

async def cancel_withdraw_callback(client, callback_query, user_id):
    try:
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("Unauthorized!")
            return
        # Remove the pending withdrawal
        await db.remove_pending_withdrawal(user_id)
        await callback_query.message.reply("Withdrawal request canceled.")
        await client.send_message(user_id, "Your withdrawal request was canceled by the admin.")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in cancel withdraw callback: {e}")
        await callback_query.message.reply("Error canceling withdrawal. Please try again later.")

async def deny_withdraw_callback(client, callback_query, user_id):
    try:
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("Unauthorized!")
            return
        await client.send_message(user_id, "Your withdrawal request was denied by the admin.")
        await callback_query.message.reply("Withdrawal denied.")
        # Remove the pending withdrawal
        await db.remove_pending_withdrawal(user_id)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in deny withdraw callback: {e}")
        await callback_query.message.reply("Error denying withdrawal. Please try again later.")