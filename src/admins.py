from src.constants import ADMIN_USERNAMES
from telegram import Update

async def ensure_admin_rights(update: Update):
    if not await user_has_admin_rights(update):
        await update.message.reply_text("У вас нет прав на выполнение этой команды")
        return False
    return True

async def user_has_admin_rights(update: Update):
    username = update.effective_user.username
    if username:
        return username.lower() in ADMIN_USERNAMES
    return False