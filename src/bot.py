import logging
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from constants import RESPONSES_DB_NAME, TOKEN_KEY, WORKDIR
from lockbox import get_lockbox_secret
from main_questions_poll import send_question, question_answer_button_callback
from questions import fetch_questions_from_sheets
from admins import *
from update_pictures import update_pictures_conv_handler, update_pictures
from personal_questions_poll import send_personal_question, PERSONAL_QUESTIONS_STATES
from error_handler import error_handler
from db_api import get_users_grade, NoGradeException
from broadcast import broadcast_conv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=os.path.join(WORKDIR, f'bot.log'),
    # filename=os.path.join(WORKDIR, f'bot-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'),
    filemode='w'
)
logging.getLogger('httpx').setLevel(logging.WARNING) 
logging.getLogger('googleapiclient').setLevel(logging.WARNING) 

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    if await user_has_admin_rights(update) and update.message is not None:
        await update.message.reply_text('''По команде /broadcast можно разослать сообщение всем пользователям\\.

По команде /start\\_poll можно начать опрос, который будут проходить ученики\\.

По команде /update\\_pictures можно заново загрузить картинки с диска\\.

По команде /update\\_questions можно обновить список вопросов \\(обновлять надо в [excel файле]\
(https://docs.google.com/spreadsheets/d/10H3dZbEEVLgHWH3xB9t8HPxAT7tW3QP8VXGvFFSOuD8/)\\)''', parse_mode=ParseMode.MARKDOWN_V2)
    else:
        state = await start_poll(update, context)
        return state

async def start_poll(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором!") # type: ignore
    if context.user_data is None:
        context.user_data = {}
    context.user_data['initial_question'] = 0
    state = await send_personal_question(update, context) # type: ignore
    return state


async def poll(update: Update, context: CallbackContext):
    if not update.callback_query:
        message = update.message
    else:
        message = update.callback_query.message
    try:
        await get_users_grade(update.effective_user.id, context) # type: ignore
        await send_question(message, update.effective_user.id, context) # type: ignore
    except NoGradeException:
        await update.effective_chat.send_message("Кажется, вы ответили не на все вопросы про себя. Пожалуйста, нажмите /start и ответьте на них") # type: ignore

async def restart(update: Update, _: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="restart_confirm"),
         InlineKeyboardButton("Нет", callback_data="restart_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Вы действительно хотите удалить все ваши ответы и начать заново?", reply_markup=reply_markup) # type: ignore

async def handle_restart_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer() # type: ignore
    
    if query.data == "restart_confirm": # type: ignore
        user_id = update.effective_user.id         # type: ignore
        conn = sqlite3.connect(RESPONSES_DB_NAME) # type: ignore
        cursor = conn.cursor()
        cursor.execute('DELETE FROM responses WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        context.user_data['question_index'] = 0 # type: ignore
        
        await query.edit_message_text("Ваши ответы удалены. Используйте /poll, чтобы начать заново.") # type: ignore
    else:
        await query.edit_message_text("Отмена операции.") # type: ignore

async def handle_sticker_response(update: Update, _: CallbackContext):
    await update.message.reply_text("Стикеры это, конечно, хорошо, но мб все же на вопросики поотвечаем?👉👈") # type: ignore

async def handle_start_poll_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer() # type: ignore
    
    if query.data == "start_poll": # type: ignore
        await poll(update, context)

async def update_questions(update: Update, context: CallbackContext):
    if not await ensure_admin_rights(update):
        return
    await update.message.reply_text("Началось обновление вопросов, подождите немного.") # type: ignore
    await fetch_questions_from_sheets()
    await update.effective_chat.send_message("Вопросы успешно обновлены!") # type: ignore

async def post_init(app: Application):
    await fetch_questions_from_sheets()
    # await send_feedback_messages(app.bot)

async def empty_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pass

    
def main():
    token = get_lockbox_secret(TOKEN_KEY)
    # app = ApplicationBuilder().token(token).build()
    app = ApplicationBuilder().token(token).post_init(post_init).build()
    print("Bot successfully started!")
    logger.info("Bot successfully started!")
    app.add_handler(broadcast_conv, group=0)

    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker_response))
    
    app.add_handler(CommandHandler("update_questions", update_questions))
    app.add_handler(CommandHandler("update_pictures", update_pictures))
    app.add_handler(CallbackQueryHandler(question_answer_button_callback, pattern="response_")) # type: ignore
    app.add_handler(CallbackQueryHandler(handle_start_poll_button, pattern="start_poll"))
    app.add_handler(CallbackQueryHandler(handle_restart_button, pattern="restart_"))
    initial_questions_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start_poll", start_poll)],
        states=PERSONAL_QUESTIONS_STATES,  # type: ignore
        fallbacks=[CommandHandler("broadcast", empty_handler)],
        allow_reentry=True
    )
    app.add_handler(update_pictures_conv_handler, group=1)
    app.add_handler(initial_questions_conv_handler, group=1)
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == '__main__':
    main()