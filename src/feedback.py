import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CallbackContext, 
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from constants import USERS_DB_NAME
from main_questions_poll import save_answer
from db_api import run_select

logger = logging.getLogger(__name__)

PERSONAL_QUESTIONS = [
    "Являлись ли вы участником заключительного этапа ВсОШ по физике в этом году?",
    "Насколько удобным для вас было прохождение опроса? (1 - совсем неудобно, 5 - очень удобно)", 
    "Помог ли вам опрос найти пробелы в своих знаниях и подготовке? (1 - совсем не помог, 5 - много что нашел)", 
    "Насколько подобранный для вас набор занятий был полезен? (1 - ничего нового не узнал, 5 - закрыл много пробелов в знаниях)", 
    "Тут вы можете написать любые комментарии, впечатления, пожелания, предложения по улучшению, или кто вам больше нравится, котики или собачки",
]

async def send_feedback_messages(bot):
    result = await run_select("SELECT user_id FROM users", USERS_DB_NAME)
    user_ids = [x[0] for x in result]
    for id in user_ids:
        try:
            await bot.send_message(chat_id=id, text="Привет! Наша команда поздравляет тебя с завершением олимпиадного сезона, ты большой молодец! Пожалуйста, ответь на несколько вопросов про нашего ботика, так ты поможешь нам сделать систему еще лучше в следующем году.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ок, погнали!", callback_data=f"feedback_ok")]]))
        except:
            logger.exception(f"Couldn't send message to a user with id {id}")

async def feedback_poll(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_user.id, text="Привет! Наша команда поздравляет тебя с завершением олимпиадного сезона, ты большой молодец! Пожалуйста, ответь на несколько вопросов про нашего ботика, так ты поможешь нам сделать систему еще лучше в следующем году.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Ок, погнали!", callback_data=f"feedback_ok")]]))
    return 0

async def save_feedback(user_id, username, question_index, response):
    await save_answer(user_id, 1_000_000+question_index, response)

async def first_question(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=update.effective_user.id, text=PERSONAL_QUESTIONS[0], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Да", callback_data=f"feedback_1_1"),
        InlineKeyboardButton("Нет", callback_data=f"feedback_1_0")]]))
    return 1

async def second_question(update: Update, context: CallbackContext):
    state = 2
    query = update.callback_query
    await query.answer()
    response = query.data.split("_")[-1]
    await save_feedback(update.effective_user.id, update.effective_user.username, state-1, response)
    await context.bot.send_message(chat_id=update.effective_user.id, text=PERSONAL_QUESTIONS[state-1], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=f"feedback_{state}_{i}") for i in range(1,6)]]))
    return state

async def third_question(update: Update, context: CallbackContext):
    state = 3
    query = update.callback_query
    await query.answer()
    response = query.data.split("_")[-1]
    await save_feedback(update.effective_user.id, update.effective_user.username, state-1, response)
    await context.bot.send_message(chat_id=update.effective_user.id, text=PERSONAL_QUESTIONS[state-1], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=f"feedback_{state}_{i}") for i in range(1,6)]]))
    return state

async def forth_question(update: Update, context: CallbackContext):
    state = 4
    query = update.callback_query
    await query.answer()
    response = query.data.split("_")[-1]
    await save_feedback(update.effective_user.id, update.effective_user.username, state-1, response)
    await context.bot.send_message(chat_id=update.effective_user.id, text=PERSONAL_QUESTIONS[state-1], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=f"feedback_{state}_{i}") for i in range(1,6)]]))
    return state

async def fifth_question(update: Update, context: CallbackContext):
    state = 5
    query = update.callback_query
    await query.answer()
    response = query.data.split("_")[-1]
    await save_feedback(update.effective_user.id, update.effective_user.username, state-1, response)
    await context.bot.send_message(chat_id=update.effective_user.id, text=PERSONAL_QUESTIONS[state-1])
    return state

async def save_last_question_answer(update: Update, context: CallbackContext):
    state = 6
    response = update.message.text
    await save_feedback(update.effective_user.id, update.effective_user.username, state-1, response)
    await context.bot.send_message(chat_id=update.effective_user.id, text="Большое спасибо за обратную связь!")
    return ConversationHandler.END

FEEDBACK_QUESTIONS_STATES = {    
    0: [CallbackQueryHandler(first_question, pattern="feedback_ok", block=False)],
    1: [CallbackQueryHandler(second_question, pattern="feedback_", block=False)],
    2: [CallbackQueryHandler(third_question, pattern="feedback_", block=False)],
    3: [CallbackQueryHandler(forth_question, pattern="feedback_", block=False)],
    4: [CallbackQueryHandler(fifth_question, pattern="feedback_", block=False)],
    5: [MessageHandler(filters.TEXT, save_last_question_answer, block=False)],
}
