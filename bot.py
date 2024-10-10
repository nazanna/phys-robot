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
from constants import users_db_name, responses_db_name, token_key, workdir
from lockbox import get_lockbox_secret
from questions import QUESTIONS, IMAGES

async def send_database_files(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.username not in ['nazanna25', 'andr_zhi']:
        await update.message.reply_text("Sorry, you don't have permission to access these files.")
        logging.warning(f"Unauthorized user {user.id} ({user.username}) attempted to access database files")
        return

    responses_path = os.path.join(workdir, 'responses.db')
    user_ids_path = os.path.join(workdir, 'user_ids.db')
    
    files_to_send = []
    for file_path, file_name in [(responses_path, 'responses.db'), (user_ids_path, 'user_ids.db')]:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                files_to_send.append((file, file_name))
        else:
            await update.message.reply_text(f"Sorry, the {file_name} file is not available.")
            logging.warning(f"User {user.id} ({user.username}) requested {file_name}, but file not found")

    for file, file_name in files_to_send:
        await update.message.reply_document(document=file, filename=file_name)
        logging.info(f"User {user.id} ({user.username}) requested {file_name} file")

    if not files_to_send:
        await update.message.reply_text("Sorry, none of the requested database files are available.")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)

async def start(update: Update, _: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором! Введите /poll, чтобы начать.")

async def save_result(user_id: int, username: str, question_index: int, response: str):
    if question_index < 2:
        conn = sqlite3.connect(users_db_name)
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO users (user_id, {"last_name" if question_index == 0 else "first_name"}) 
            VALUES (?, ?)
            ON CONFLICT (user_id) DO UPDATE SET first_name = EXCLUDED.first_name
            ''', (user_id, response))
        conn.commit()
        conn.close()

    else:
        conn = sqlite3.connect(responses_db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO responses (user_id, username, question_index, response) 
            VALUES (?, ?, ?, ?)
            ''', (user_id, username, question_index, response))
        conn.commit()
        conn.close()

async def get_question_index(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    # returns index of first unanswered question for user and updates context.user_data['question_index']
    if 'question_index' in context.user_data:
        return context.user_data['question_index']
    conn = sqlite3.connect(responses_db_name)
    cursor = conn.cursor()
    cursor.execute(f'SELECT question_index from responses WHERE user_id={user_id} ORDER BY updated_at DESC LIMIT 1')
    rows = cursor.fetchall()
    conn.close()
    if len(rows) == 0:
        context.user_data['question_index'] = 0
    else:
        context.user_data['question_index'] = rows[0][0] + 1
    return context.user_data['question_index']

async def poll(update: Update, context: CallbackContext):
    await get_question_index(update.effective_user.id, context)
    await send_question(update.message, update.effective_user.id, context)

async def send_question(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = await get_question_index(user_id, context)
    if question_index < len(QUESTIONS):
        if question_index < 2:
            await message.reply_text(QUESTIONS[question_index] + " (введите ваш ответ)")
        else:
            if question_index == 2:
                await message.reply_text('Впереди будут различные физические темы с примерами задач. Твоя задача - прочитать, осознать и оценить свои познания от 0 до 3 (0 - вообще ничего не знаю)')
            
            keyboard = [
                [InlineKeyboardButton("0", callback_data=f"response_{question_index}_0"),
                InlineKeyboardButton("1", callback_data=f"response_{question_index}_1"),
                InlineKeyboardButton("2", callback_data=f"response_{question_index}_2"),
                InlineKeyboardButton("3", callback_data=f"response_{question_index}_3")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(QUESTIONS[question_index])
            await message.reply_photo(photo=open(IMAGES[question_index-2], 'rb'), reply_markup=reply_markup)
    else:
        await message.reply_text("Ура! 100500 вопросов подошли к концу, скоро будут еще 100500:) Спасибо, что на все ответили!")

async def handle_text_response(update: Update, context: CallbackContext):
    question_index = await get_question_index(update.effective_user.id, context)
    if question_index < 2:
        await save_result(update.effective_user.id, update.effective_user.name, question_index, update.message.text)
        context.user_data['question_index'] += 1
        await send_question(update.message, update.effective_user.id, context)

async def handle_sticker_response(update: Update, _: CallbackContext):
    await update.message.reply_text("Стикеры это, конечно, хорошо, но мб все же на вопросики поотвечаем?👉👈")

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) >= 2 and data[1].isdigit():
        question_index = int(data[1])
    else:
        question_index = await get_question_index(update.effective_user.id, context)
    response = data[2]
    
    await save_result(update.effective_user.id, update.effective_user.name, question_index, response)
    context.user_data['question_index'] = question_index + 1
    await send_question(query.message, update.effective_user.id, context)
def main():
    token = get_lockbox_secret(token_key)
    app = ApplicationBuilder().token(token).build()
    print("Bot successfully started!")
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler("poll", poll))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker_response))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("get_db", send_database_files))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()
