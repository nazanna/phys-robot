import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from constants import responses_db_name, token_key, ADMIN_USERNAMES
from lockbox import get_lockbox_secret
from personal_questions_poll import send_initial_questions, handle_initial_text_response
from main_questions import send_question, question_answer_button_callback
from google_drive_api import GoogleDriveAPI
from questions import fetch_questions_from_sheets

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором!")
    if await user_has_admin_rights(update):
        await update.message.reply_text('''По команде /update\_pictures можно заново загрузить картинки с диска. \

По команде /update\_questions можно обновить список вопросов (обновлять надо в [excel файле]\
(https://docs.google.com/spreadsheets/d/10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8/))''', parse_mode=ParseMode.MARKDOWN)
    context.user_data['initial_question'] = 0
    await send_initial_questions(update, context)

async def poll(update: Update, context: CallbackContext):
    if not update.callback_query:
        message = update.message
    else:
        message = update.callback_query.message
    await send_question(message, update.effective_user.id, context)

async def ensure_admin_rights(update: Update):
    if not await user_has_admin_rights(update):
        await update.message.reply_text("У вас нет прав на выполнение этой команды")
        return False
    return True

async def user_has_admin_rights(update: Update):
    username = update.effective_user.username
    return username.lower() in ADMIN_USERNAMES


async def restart(update: Update, _: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="restart_confirm"),
         InlineKeyboardButton("Нет", callback_data="restart_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вы действительно хотите удалить все ваши ответы и начать заново?", reply_markup=reply_markup)

async def update_pictures(update: Update, _: CallbackContext):
    if not user_has_admin_rights(update):
        return
    await update.message.reply_text("Началось обновление картинок. Пожалуйста, подождите, это может занять некоторое время. После окончания загрузки придет сообщение.")
    api = GoogleDriveAPI()
    await api.download_files_from_drive()
    await update.message.reply_text("Загрузка завершена, спасибо за ожидание!")

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
        
        context.user_data['question_index'] = 0
        
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

async def update_questions(update: Update, _: CallbackContext):
    if not await ensure_admin_rights(update):
        return
    await fetch_questions_from_sheets()
    await update.message.reply_text("Вопросы успешно обновлены!")

def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("update_pictures", update_pictures))
    app.add_handler(CommandHandler("update_questions", update_questions))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker_response))
    app.add_handler(CallbackQueryHandler(question_answer_button_callback, pattern="response_"))
    app.add_handler(CallbackQueryHandler(handle_start_poll_button, pattern="start_poll"))
    app.add_handler(CallbackQueryHandler(handle_restart_button, pattern="restart_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_text_response))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()
