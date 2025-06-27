import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CallbackContext, 
    MessageHandler,
    ConversationHandler,
    filters
)
from constants import USERS_DB_NAME
from db_api import get_users_grade

logger = logging.getLogger(__name__)

LAST_NAME = int(0)
FIRST_NAME = int(1)
SURNAME = int(2)
GRADE = int(3)
SCHOOL = int(4)
CONTACT = int(5)
END = int(6)

PERSONAL_QUESTIONS = [
    "Введите вашу фамилию:",
    "Введите ваше имя:", 
    "Введите ваше отчество:",
    "Введите ваш класс:",
    "В какой школе вы учитесь?",
    "Введите контактный email:"
]

async def send_personal_question(update: Update, context: CallbackContext):
    if 'initial_question' not in context.user_data: # type: ignore
        context.user_data['initial_question'] = 0 # type: ignore
    
    question_index = context.user_data['initial_question'] # type: ignore
    if question_index == 0:
        conn = sqlite3.connect(USERS_DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f'''
        INSERT INTO users (user_id, username) 
        VALUES (?, ?)
        ON CONFLICT (user_id) DO NOTHING
        ''', (update.effective_user.id, update.effective_user.username)) # type: ignore
        conn.commit()
        conn.close()
    
    if question_index > 0:
        await _save_personal_question_response(update.effective_user.id, question_index - 1, update.message.text) # type: ignore
        # if question_index == CONTACT:
        #     await send_main_poll_notification(update, context)
    
    if question_index < len(PERSONAL_QUESTIONS):
        if question_index == GRADE:
            reply_markup = ReplyKeyboardMarkup([[InlineKeyboardButton(grade, callback_data=f"student_grade_{grade}") for grade in [7,8,9]],  # type: ignore
                                                 [InlineKeyboardButton(grade, callback_data=f"student_grade_{grade}") for grade in [10,11]]]) # type: ignore
            await update.message.reply_text(PERSONAL_QUESTIONS[question_index], reply_markup=reply_markup) # type: ignore 
        elif question_index == GRADE + 1:
            await update.message.reply_text(PERSONAL_QUESTIONS[question_index], reply_markup=ReplyKeyboardRemove()) # type: ignore
        else:
            await update.message.reply_text(PERSONAL_QUESTIONS[question_index]) # type: ignore
        logger.info(f'Sent question `{PERSONAL_QUESTIONS[question_index]}`')
        if question_index != len(PERSONAL_QUESTIONS) - 1:
            context.user_data['initial_question'] = question_index + 1 # type: ignore
            return question_index
    return END

async def _save_personal_question_response(user_id: int, question_index: int, response: str):
    columns = {
        0: "last_name", 
        1: "name",
        2: "surname",
        3: "grade",
        4: "school",
        5: "contact"
    }
    column = columns[question_index]
    conn = sqlite3.connect(USERS_DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO users (user_id, {column}) 
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET {column} = EXCLUDED.{column}
    ''', (user_id, response))
    conn.commit()
    conn.close()
    logger.info(f'Saved into db question {question_index} response {response}')

async def send_main_poll_notification(update: Update, context: CallbackContext):
    await _save_personal_question_response(update.effective_user.id, CONTACT, update.message.text) # type: ignore
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Ок, понятно", callback_data="start_poll")]])
    
    await update.message.reply_text( # type: ignore
        '''Спасибо за информацию, теперь начинаем опрос! Впереди будут различные физические темы с примерами задач.
Твоя задача - прочитать, осознать и оценить свои познания по каждой теме от 0 до 2 (0 - вообще ничего не знаю, 1 - что-то слышал, но надо бы повторить, 2 - могу сейчас сесть и написать решения к задачам).

Если хочешь сбросить ответы на все тестовые вопросы, нажми /restart.

Если хочешь заново ответить на личные вопросы (имя, фамилия и т.п.), нажми /start.''', reply_markup=reply_markup)
    context.user_data['initial_question'] = 10 # type: ignore
    await get_users_grade(update.effective_user.id, context, force_db=True) # type: ignore
    return ConversationHandler.END

PERSONAL_QUESTIONS_STATES = {
    LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_personal_question)],
    FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_personal_question)],
    SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_personal_question)],
    SCHOOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_personal_question)],
    GRADE: [MessageHandler(filters.Regex("^(7|8|9|10|11)$"), send_personal_question)],
    CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_personal_question)],
    END: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_main_poll_notification)],
}
