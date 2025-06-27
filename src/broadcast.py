from __future__ import annotations        
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, ContextTypes, filters
)
from constants import ADMIN_USERNAMES
from db_api import get_all_user_ids

ASK_TEXT, CONFIRM = range(2)

async def start_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if user is None or user.username not in ADMIN_USERNAMES:
        await update.message.reply_text("⛔️ Команда разрешена только администраторам.") # type: ignore
        return ConversationHandler.END

    await update.message.reply_text( # type: ignore
        "Режим рассылки активирован. Пожалуйста, отправьте текст, который вы хотите разослать.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")]]),
    )
    return ASK_TEXT

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Рассылка отменена\\.")
    elif update.message:
        await update.message.reply_text("❌ Рассылка отменена\\.")
    return ConversationHandler.END

async def on_text_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    ctx.user_data["src_msg_id"]  = msg.id # type: ignore
    ctx.user_data["src_chat_id"] = msg.chat_id # type: ignore

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel"),
        ]
    ])
    await msg.reply_text( # type: ignore
        "Это сообщение будет отправлено всем пользователям. Продолжить?",
        reply_markup=keyboard,
    )
    return CONFIRM

async def confirm_and_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer() # type: ignore

    src_chat_id = ctx.user_data["src_chat_id"] # type: ignore
    src_msg_id  = ctx.user_data["src_msg_id"] # type: ignore
    all_ids     = await get_all_user_ids()

    sent = failed = 0

    for i, chat_id in enumerate(all_ids, 1):
        try:
            await ctx.bot.copy_message(chat_id, src_chat_id, src_msg_id)
            sent += 1
        except (Forbidden, BadRequest):
            failed += 1

    await query.edit_message_text(f"Готово. Отправлено {sent} сообщений, не удалось отправить {failed}.") # type: ignore
    return ConversationHandler.END


broadcast_conv = ConversationHandler(
    entry_points=[CommandHandler("broadcast", start_broadcast)],
    states={
        ASK_TEXT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, on_text_received),
            CallbackQueryHandler(cancel, pattern="^broadcast_cancel$")
        ],
        CONFIRM: [
            CallbackQueryHandler(confirm_and_broadcast, pattern="^broadcast_confirm$"),
            CallbackQueryHandler(cancel, pattern="^broadcast_cancel$")
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern="^broadcast_cancel$")],
    name="broadcast_conv",
)

