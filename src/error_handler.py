import logging
import traceback
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__) # type: ignore
    tb_string = "".join(tb_list)

    developer_chat_id = 816623670
    await context.bot.send_message(chat_id=developer_chat_id, text=f"An exception occurred:\n{tb_string}")

async def send_message_to_ann(text: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    ann_chat_id = 966497557
    await context.bot.send_message(chat_id=ann_chat_id, text=text)
