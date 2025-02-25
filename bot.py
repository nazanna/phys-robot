import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARN,
    filename='bot.log',
    filemode='w'
)

logger = logging.getLogger(__name__)

from constants import responses_db_name, token_key
from lockbox import get_lockbox_secret
from main_questions_poll import send_question, question_answer_button_callback
from questions import fetch_questions_from_sheets
from admins import *
from update_pictures import update_pictures_conv_handler, update_pictures
from personal_questions_poll import send_personal_question, PERSONAL_QUESTIONS_STATES
from questions import fetch_questions_from_sheets
from error_handler import error_handler
from db_api import get_users_grade, NoGradeException

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором!")
    if await user_has_admin_rights(update):
        await update.message.reply_text('''По команде /update\_pictures можно заново загрузить картинки с диска.

По команде /update\_questions можно обновить список вопросов (обновлять надо в [excel файле]\
(https://docs.google.com/spreadsheets/d/10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8/))''', parse_mode=ParseMode.MARKDOWN)
    context.user_data['initial_question'] = 0
    state = await send_personal_question(update, context)
    return state

async def poll(update: Update, context: CallbackContext):
    if not update.callback_query:
        message = update.message
    else:
        message = update.callback_query.message
    try:
        await get_users_grade(update.effective_user.id, context)
        await send_question(message, update.effective_user.id, context)
    except NoGradeException:
        await update.effective_chat.send_message("Кажется, вы ответили не на все вопросы про себя. Пожалуйста, нажмите /start и ответьте на них")

async def restart(update: Update, _: CallbackContext):
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

async def update_questions(update: Update, context: CallbackContext):
    if not await ensure_admin_rights(update):
        return
    await update.message.reply_text("Началось обновление вопросов, подождите немного.")
    await fetch_questions_from_sheets()
    await update.effective_chat.send_message("Вопросы успешно обновлены!")

def main():
    token = get_lockbox_secret(token_key)
    from questions import fetch_questions_from_sheets_during_bot_start
    app = ApplicationBuilder().token(token).post_init(fetch_questions_from_sheets_during_bot_start).build()
    print("Bot successfully started!")
    logger.info("Bot successfully started!")

    app.add_handler(CommandHandler("poll", poll, block=False))
    app.add_handler(CommandHandler("restart", restart, block=False))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker_response, block=False))
    
    app.add_handler(CommandHandler("update_questions", update_questions))
    app.add_handler(CommandHandler("update_pictures", update_pictures))
    app.add_handler(CallbackQueryHandler(question_answer_button_callback, pattern="response_", block=False))
    app.add_handler(CallbackQueryHandler(handle_start_poll_button, pattern="start_poll", block=False))
    app.add_handler(CallbackQueryHandler(handle_restart_button, pattern="restart_", block=False))
    app.add_handler(update_pictures_conv_handler)
    for handlers in PERSONAL_QUESTIONS_STATES.values():
        handlers.append(CommandHandler("start", start))
    initial_questions_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=PERSONAL_QUESTIONS_STATES, 
        fallbacks=[]
    )
    app.add_handler(initial_questions_conv_handler)
    
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == '__main__':
    main()