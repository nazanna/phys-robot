import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from constants import responses_db_name, token_key
from lockbox import get_lockbox_secret
from personal_questions_poll import send_initial_questions, handle_initial_text_response
from main_questions import send_question, get_current_question_index, question_answer_button_callback

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором!")
    await send_initial_questions(update, context)

async def poll(update: Update, context: CallbackContext):
    if not update.callback_query:
        message = update.message
    else:
        message = update.callback_query.message
    await send_question(message, update.effective_user.id, context)

async def restart(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="restart_confirm"),
         InlineKeyboardButton("Нет", callback_data="restart_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вы действительно хотите удалить все ваши ответы и начать заново?", reply_markup=reply_markup)

async def handle_restart_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "restart_confirm":
        user_id = update.effective_user.id        
        conn = sqlite3.connect(responses_db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM responses WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        context.user_data['question_index'] = 1
        
        await query.message.edit_text("Ваши ответы удалены. Используйте /poll, чтобы начать заново.")
    else:
        await query.message.edit_text("Отмена операции.")

async def handle_sticker_response(update: Update, _: CallbackContext):
    await update.message.reply_text("Стикеры это, конечно, хорошо, но мб все же на вопросики поотвечаем?👉👈")

async def handle_start_poll_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_poll":
        await poll(update, context)

def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker_response))
    app.add_handler(CallbackQueryHandler(question_answer_button_callback, pattern="response_"))
    app.add_handler(CallbackQueryHandler(handle_start_poll_button, pattern="start_poll"))
    app.add_handler(CallbackQueryHandler(handle_restart_button, pattern="restart_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_text_response))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()
