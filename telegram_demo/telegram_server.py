from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse
from aiogram.types import Update
import uvicorn

from utils.config_reader import ConfigReader
from utils.logging_configuration import LoggingConfigurator

from telegram_manager import TelegramManager, Message
from google_sheets.gs_manager import GoogleSheetsManager
from chatgpt.chatgpt_manager import ChatGPTManager

config = ConfigReader(config_rel_path='resources/config.yaml').get_config()
logger = LoggingConfigurator.get_logger(config=config, log_file_name='whatsapp.log')

tg_manager = TelegramManager(config)
gs_manager = GoogleSheetsManager(credentials_path=config.get('CRED_FILE_PATH_GS'),
                                 spreadsheet_id=config.get('SPREADSHEET_ID_TG'),
                                 sheet_name=config.get('SHEET_NAME'))
chatgpt_manager = ChatGPTManager('tg', config)
app = FastAPI()


@app.post('/webhook')
async def webhook(request: Request):
    update = Update(**await request.json())
    tg_manager.update_id = update.update_id
    await tg_manager.dp.process_update(update)

    # add verification
    response = PlainTextResponse('ok', status_code=200)

    return response


@tg_manager.dp.message_handler(content_types=tg_manager.text_message)
async def text_handler(text_message_data: Message):
    logger.info('Received a text message data: %s', text_message_data)

    tg_message_data, update_id, chat_id, username = tg_manager.preprocess_for_gs(text_message_data)
    tg_manager.update_id = None
    gs_manager.save_data(data=tg_message_data)

    message_history = gs_manager.get_data_by_id(chat_id, 'chat_id')

    # chatgpt_manager.preprocess_for_myself(message_history)
    chatgpt_manager.preprocess_for_myself_davinci(message_history, chat_id)
    # cgpt_response_data = chatgpt_manager.send_request_gpt3()
    cgpt_response_data = chatgpt_manager.send_request_davinci(chat_id)

    if cgpt_response_data:
        # await tg_manager.bot.send_message(chat_id=chat_id,
        #                                   text=chatgpt_manager.preprocess_for_sending(cgpt_response_data))

        await tg_manager.bot.send_message(chat_id=chat_id,
                                          text=chatgpt_manager.preprocess_for_sending_davinci(cgpt_response_data))

        cgpt_response_data = chatgpt_manager.preprocess_data_for_gs_davinci(cgpt_response_data,
                                                                            update_id=update_id,
                                                                            chat_id=chat_id,
                                                                            username=username)
        gs_manager.save_data(data=cgpt_response_data)


@tg_manager.dp.message_handler(content_types=tg_manager.all_but_text)
async def all_but_text_handler(message_data: Message):
    logger.info('Received an unsupported message type: %s', message_data)
    await tg_manager.bot.send_message(chat_id=message_data.chat.id, text=config.get('REPLY_WRONG_TYPE'))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
