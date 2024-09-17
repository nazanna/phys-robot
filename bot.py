import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
import pandas as pd

# Функция start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Сейчас начнется большой опрос. Пожалуйста, отвечайте честно и думайте перед выбором! Введите /poll_1_part, чтобы начать.")

token = "7318204882:AAGQ1HpJwL2YeiUgdRU8EIIR_tNOL-nLy_0"

N_img = 53

df = pd.read_csv('темы - 7 класс.csv')
QUESTIONS = df['тема'].tolist()

IMAGES = ['Примеры задач/'+'00'+str(num)+'.png' for num in range(1, 10)]
for num in range(10, N_img):
    IMAGES.append('Примеры задач/'+'0'+str(num)+'.png')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

async def save_result(user_id: int, question_index: int, response: str):
    conn = sqlite3.connect('user_responses.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO responses (user_id, question_index, response) VALUES (?, ?, ?)', (user_id, question_index, response))
    conn.commit()
    conn.close()

async def poll(update: Update, context: CallbackContext):
    context.user_data['question_index'] = 0
    await send_question(update.message, context)

async def send_question(message, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['question_index']

    if question_index < len(QUESTIONS):
        # Первые два вопроса требуют текстового ввода
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
            await message.reply_photo(photo=open(IMAGES[question_index], 'rb'), reply_markup=reply_markup)
    else:
        await message.reply_text("Ура! 100500 вопросов первой части подошли к концу, скоро будет вторая:). Спасибо, что на все ответили!")

async def handle_text_response(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    question_index = context.user_data['question_index']

    # Сохраняем текстовый ответ
    await save_result(user_id, question_index, update.message.text)

    # Переход к следующему вопросу
    context.user_data['question_index'] += 1
    await send_question(update.message, context)

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    query.answer()

    data = query.data.split("_")
    question_index = int(data[1])
    response = data[2]

    # Сохраняем ответ пользователя в базу данных
    await save_result(user_id, question_index, response)

    # Переход к следующему вопросу
    context.user_data['question_index'] += 1
    await send_question(query.message, context)

def main():
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler("poll_1_part", poll))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_response))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
    app.idle()

if __name__ == '__main__':
    main()
