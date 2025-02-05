import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from constants import users_db_name, responses_db_name, token_key, workdir, ADMIN_USERNAMES, MAX_IMAGES_PER_QUESTION, GOOGLE_SHEET_ANSWERS_ID
from lockbox import get_lockbox_secret
from questions import QUESTIONS
from google_sheets_api import GoogleSheetsAPI

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором!")
    if update.effective_user.username in ADMIN_USERNAMES:
        await update.message.reply_text("Чтобы скачать базы данных, нажми /get_db.")
    await send_initial_questions(update, context)

async def save_answer(user_id: int, username: str, question_index: int, response: str):
    conn = sqlite3.connect(responses_db_name)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO responses (user_id, question_index, response) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, question_index) DO UPDATE SET 
            response = excluded.response
        ''', (user_id, question_index, response))
    conn.commit()
    conn.close()

async def get_current_question_index(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    # returns index of first unanswered question for user and updates context.user_data['question_index']
    if 'question_index' in context.user_data:
        return context.user_data['question_index']
    conn = sqlite3.connect(responses_db_name)
    cursor = conn.cursor()
    cursor.execute(f'SELECT question_index from responses WHERE user_id={user_id} ORDER BY updated_at DESC LIMIT 1')
    rows = cursor.fetchall()
    conn.close()
    if len(rows) == 0:
        context.user_data['question_index'] = 1 
    else:
        context.user_data['question_index'] = rows[0][0] + 1
    return context.user_data['question_index']

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



async def poll(update: Update, context: CallbackContext):
    await get_current_question_index(update.effective_user.id, context)
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

async def send_question(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = await get_current_question_index(user_id, context)
    if question_index < len(QUESTIONS):
        keyboard = [
            [InlineKeyboardButton("0", callback_data=f"response_{question_index}_0"),
             InlineKeyboardButton("1", callback_data=f"response_{question_index}_1"),
             InlineKeyboardButton("2", callback_data=f"response_{question_index}_2"),
             InlineKeyboardButton("3", callback_data=f"response_{question_index}_3")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        from telegram import InputMediaPhoto
        current_images = []
        image_name_prefix = f"{'0' * (3 - len(str(question_index)))}{question_index}"
        for i in range(1, MAX_IMAGES_PER_QUESTION):  
            image_path = os.path.join(workdir, "Problems", f"{image_name_prefix}_{i}.png")
            if not os.path.exists(image_path):
                break
            current_images.append(image_path)
        image_path = os.path.join(workdir, "Problems", f"{image_name_prefix}.png")
        if os.path.exists(image_path):
            current_images.append(image_path)

        if len(current_images) == 1:
            await message.reply_photo(photo=open(current_images[0], 'rb'), caption=QUESTIONS[question_index], reply_markup=reply_markup)
        else:
            media = []
            for i, image_path in enumerate(current_images):
                with open(image_path, 'rb') as photo:
                    media.append(InputMediaPhoto(photo))
            
            if media:
                await message.reply_media_group(media=media)
            await message.reply_text(QUESTIONS[question_index], reply_markup=reply_markup)
    else:
        await message.reply_text("Ура! 100500 вопросов подошли к концу, скоро будут еще 100500:) Спасибо, что на все ответили!")

async def handle_sticker_response(update: Update, _: CallbackContext):
    await update.message.reply_text("Стикеры это, конечно, хорошо, но мб все же на вопросики поотвечаем?👉👈")

async def question_answer_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) >= 2 and data[1].isdigit():
        question_index = int(data[1])
    else:
        question_index = await get_current_question_index(update.effective_user.id, context)
    response = data[2]
    
    await save_answer(update.effective_user.id, update.effective_user.name, question_index, response)
    context.user_data['question_index'] = question_index + 1
    await send_question(query.message, update.effective_user.id, context)

async def handle_initial_text_response(update: Update, context: CallbackContext):
    question_index = context.user_data.get('initial_question', 0) - 1
    if question_index >= 0 and question_index < 6:
        await save_initial_response(update.effective_user.id, question_index, update.message.text)
        if await send_initial_questions(update, context):
            return
    if question_index == 5:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Ок, ясненько", callback_data="start_poll")]])
        await update.message.reply_text("Спасибо за информацию, теперь начинаем опрос! Впереди будут различные физические темы с примерами задач. \
Твоя задача - прочитать, осознать и оценить свои познания по каждой теме от 0 до 3 (0 - вообще ничего не знаю, 3 - могу сейчас сесть и написать решения к задачам)" \
                                        , reply_markup=reply_markup)
        context.user_data['initial_question'] = question_index + 10
        # await poll(update, context)

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
    app.add_handler(CallbackQueryHandler(question_answer_button, pattern="response_"))
    app.add_handler(CallbackQueryHandler(handle_start_poll_button, pattern="start_poll"))
    app.add_handler(CallbackQueryHandler(handle_restart_button, pattern="restart_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_text_response))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()
