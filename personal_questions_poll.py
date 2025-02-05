import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from constants import users_db_name
from telegram.ext import CallbackContext

async def send_initial_questions(update: Update, context: CallbackContext):
    if 'initial_question' not in context.user_data:
        context.user_data['initial_question'] = 0
        
    question_index = context.user_data['initial_question']
    conn = sqlite3.connect(users_db_name)
    cursor = conn.cursor()
    cursor.execute(f'''
    INSERT INTO users (user_id, username) 
    VALUES (?, ?)
    ON CONFLICT (user_id) DO NOTHING
    ''', (update.effective_user.id, update.effective_user.username))

    conn.commit()
    conn.close()

    questions = [
        "Введите вашу фамилию:",
        "Введите ваше имя:", 
        "Введите ваше отчество:",
        "Введите ваш класс:",
        "В какой школе вы учитесь?",
        "Введите контактный телефон или email:"
    ]
    
    if question_index < len(questions):
        await update.message.reply_text(questions[question_index])
        context.user_data['initial_question'] = question_index + 1
        return True
    else:
        context.user_data['question_index'] = 5
        return False

async def save_initial_response(user_id: int, question_index: int, response: str):
    # Map question index to column name
    columns = {
        0: "surname",
        1: "name",
        2: "last_name", 
        3: "grade",
        4: "school",
        5: "contact"
    }
    
    column = columns[question_index]
    conn = sqlite3.connect(users_db_name)
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO users (user_id, {column}) 
        VALUES (?, ?)
        ON CONFLICT (user_id) DO UPDATE SET {column} = EXCLUDED.{column}
    ''', (user_id, response))
    conn.commit()
    conn.close()


async def handle_initial_text_response(update: Update, context: CallbackContext):
    question_index = context.user_data.get('initial_question', 0) - 1
    if 0 <= question_index < 6:
        await save_initial_response(update.effective_user.id, question_index, update.message.text)
        if await send_initial_questions(update, context):
            return
    if question_index == 5: # last initial question
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Ок, ясненько", callback_data="start_poll")]])
        await update.message.reply_text("Спасибо за информацию, теперь начинаем опрос! Впереди будут различные физические темы с примерами задач. \
Твоя задача - прочитать, осознать и оценить свои познания по каждой теме от 0 до 3 (0 - вообще ничего не знаю, 3 - могу сейчас сесть и написать решения к задачам)" \
                                        , reply_markup=reply_markup)
        context.user_data['initial_question'] = question_index + 10
        # await poll(update, context)
