import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import (
    CallbackContext,
    ContextTypes,
)
from constants import RESPONSES_DB_NAME, UPLOAD_FREQUENCY, WORKDIR, MAX_IMAGES_PER_QUESTION
from upload_to_google_sheets import upload_student_answers_to_sheets
import questions
from db_api import get_users_grade
from error_handler import send_message_to_ann

logger = logging.getLogger(__name__)

def get_main_questions_keyboard(question_index):
    return [[
        InlineKeyboardButton("0", callback_data=f"response_{question_index}_0"),
        InlineKeyboardButton("1", callback_data=f"response_{question_index}_1"),
        InlineKeyboardButton("2", callback_data=f"response_{question_index}_2"),
        ]]

async def question_answer_button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    if len(data) >= 2 and data[1].isdigit():
        question_index = int(data[1])
    else:
        raise ValueError(f'Incorrect format of question answer button: {data}')
    response = int(data[2])
    
    keyboard = get_main_questions_keyboard(question_index)
    keyboard[0][response] = InlineKeyboardButton(f"✅{response}", callback_data=f"response_{question_index}_{response}")
    try:
        await update.callback_query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
    except error.BadRequest as e:
        if "Message is not modified" not in str(e):
            raise
    
    await save_answer(update.effective_user.id, question_index, response)
    current_question_index = await get_current_question_index(update.effective_user.id, context)
    if question_index == current_question_index:
        context.user_data['question_index'] = question_index + 1
        await send_question(query.message, update.effective_user.id, context)
    if question_index % UPLOAD_FREQUENCY == 0 and question_index > 0:
        await upload_student_answers_to_sheets(update.effective_user.id)

async def save_answer(user_id: int, question_index: int, response: str):
    conn = sqlite3.connect(RESPONSES_DB_NAME)
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
    if 'question_index' in context.user_data:
        return context.user_data['question_index']
    conn = sqlite3.connect(RESPONSES_DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'SELECT COUNT(*) FROM responses WHERE user_id={user_id}')
    rows = cursor.fetchall()
    conn.close()
    context.user_data['question_index'] = rows[0][0]
    return context.user_data['question_index']

async def get_images_for_question(question_number: int):
    current_images = []
    image_name_prefix = f"{'0' * (3 - len(str(question_number)))}{question_number}"
    for i in range(1, MAX_IMAGES_PER_QUESTION):  
        image_path = os.path.join(WORKDIR, "Problems", f"{image_name_prefix}_{i}.png")
        if not os.path.exists(image_path):
            break
        current_images.append(image_path)
    image_path = os.path.join(WORKDIR, "Problems", f"{image_name_prefix}.png")
    if os.path.exists(image_path):
        current_images.append(image_path)
    return current_images

async def send_question(message, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    question_index = await get_current_question_index(user_id, context)
    grade = await get_users_grade(user_id, context)
    if len(questions.QUESTIONS) == 0:
        logger.error(f'QUESTIONS are empty!')
        raise IndexError("QUESTIONS are empty, but we are sending them!")
    if question_index < len(questions.QUESTIONS_FOR_GRADE[grade]):
        keyboard = get_main_questions_keyboard(question_index)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        from telegram import InputMediaPhoto
        question_number = int(questions.QUESTIONS_FOR_GRADE[grade][question_index])
        logger.info(f'Processing question {question_number}')
        current_images = await get_images_for_question(question_number)
        if len(current_images) == 0:
            await send_message_to_ann(f"For question {question_number} no pictures were found", context)

        if len(current_images) == 1:
            await message.reply_photo(photo=open(current_images[0], 'rb'), caption=questions.QUESTIONS[question_number], reply_markup=reply_markup)
        else:
            media = []
            for i, image_path in enumerate(current_images):
                with open(image_path, 'rb') as photo:
                    media.append(InputMediaPhoto(photo))
            
            if media:
                await message.reply_media_group(media=media)
            await message.reply_text(questions.QUESTIONS[question_number], reply_markup=reply_markup)
    else:
        await message.reply_text("Ура, 100500 вопросов подошли к концу! Спасибо за прохождение опроса, вы помогаете нам лучше вас учить😄")
        await upload_student_answers_to_sheets(user_id)

