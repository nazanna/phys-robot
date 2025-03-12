import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from src.admins import user_has_admin_rights
from src.google_drive_api import GoogleDriveAPI, FileNotFoundException

async def update_pictures(update: Update, _: CallbackContext):
    if not await user_has_admin_rights(update):
        return
    keyboard = [
        [InlineKeyboardButton("1. Обновить одну картинку", callback_data=f"update_pictures_one")],
        [InlineKeyboardButton("2. Загрузить все новые картинки", callback_data=f"update_pictures_new")],
        [InlineKeyboardButton("3. Загрузить все картинки", callback_data=f"update_pictures_all")],
        [InlineKeyboardButton("Отмена", callback_data=f"update_pictures_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("""
Выберите опцию загрузки, которая вам нужна:

*1. Обновить одну картинку.* Для этого вам надо загрузить ее на [гугл диск](https://drive.google.com/drive/folders/1JghtLbJ7MEvD-33LNtbf6Q2iiy6oEysf), выбрать нужную опцию по кнопке ниже \
и затем написать в бота ее номер. 

*2. Загрузить все новые картинки.* Команда скачает все новые картинки, которые были загружены на гугл диск. \
При этом картинки, которые уже были на диске, но были обновлены, не обновятся.   

*3. Загрузить все картинки.* Эта команда обновит все картинки в боте картинками с гугл диска. Обратите внимание,\
что эта команда может выполняться *очень долго* (20 минут). Советуем использовать ее тогда, когда нужно обновить \
действительно много картинок.

К сожалению, *ограничения Google диска не позволяют* легко и быстро обновить картинки после их загрузки на диск. \
Приносим свои извинения за неудобства.

Если передумали, нажмите "Отмена".
""", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

WAITING_FOR_PICTURE_NUMBER_STATE = 1

async def handle_pictures_update_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    option = query.data.split('_')[-1]
    if option == "one":
        await update.get_bot().send_message(update.effective_message.chat_id, "Введите номер картинки, \
которую хотите обновить, без расширения файла. Например, для обновления `018_1.png` \
введите `018_1`.\n\nЕсли хотите отменить, просто нажмите /cancel.")
        return WAITING_FOR_PICTURE_NUMBER_STATE
    elif option == "new":
        await update.get_bot().send_message(update.effective_message.chat_id, "Началась загрузка картинок. Пожалуйста, подождите, это может занять некоторое время. После окончания загрузки придет сообщение.")
        api = GoogleDriveAPI()
        await api.download_files_from_drive(new_only=True)
        await update.get_bot().send_message(update.effective_message.chat_id, "Загрузка завершена, спасибо за ожидание!")
    elif option == "all":
        await update.get_bot().send_message(update.effective_message.chat_id, "Началось обновление картинок. Пожалуйста, подождите, это может занять некоторое время. После окончания загрузки придет сообщение.")
        api = GoogleDriveAPI()
        await api.download_files_from_drive()
        await update.get_bot().send_message(update.effective_message.chat_id, "Все картинки обновлены, спасибо за ожидание!")
    elif option == "cancel":
        await update.get_bot().send_message(update.effective_message.chat_id, "Ок, отменяем")

async def get_updated_picture_number(update: Update, context: CallbackContext):
    pattern = "^([0-9])*(_[0-9])?$"
    if not re.match(pattern, update.message.text):
        await update.message.reply_text("Пожалуйста, введите корректный номер картинки. Это либо число, либо число с индексом в конце, например, 123_1.")
        return WAITING_FOR_PICTURE_NUMBER_STATE
    picture_number = update.message.text    
    await update.message.reply_text("Спасибо! Обновление картинки началось.")
    api = GoogleDriveAPI()
    try:
        await api.download_file_by_name(f'{picture_number}.png')
        await update.message.reply_text(f"Юхуу, картинка {picture_number}.png обновлена!")
        return ConversationHandler.END
    except FileNotFoundException:
        await update.message.reply_text(f"Упс, кажется, картинки {picture_number}.png нет на диске. Возможно, \
проблема в расширении, должно быть .png. Проверьте, пожалуйста, и снова напишите номер нужной картинки, \
или отмените действие с помощью /cancel.")
        return WAITING_FOR_PICTURE_NUMBER_STATE
        
async def cancel_picture_update(update: Update, context: CallbackContext):
    await update.message.reply_text("Галя, у нас отмена!")
    # await update.get_bot().send_message(update.effective_message.chat_id, "Галя, у нас отмена!")
    return ConversationHandler.END

update_pictures_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_pictures_update_buttons, pattern="update_pictures_")],
        states={
            WAITING_FOR_PICTURE_NUMBER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_updated_picture_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel_picture_update)],
    )