from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from uvicorn import run

from utils.config_reader import ConfigReader
from utils.logging_configuration import LoggingConfigurator

from whatsapp_manager import WhatsAppManager
from google_sheets.gs_manager import GoogleSheetsManager
from chatgpt.chatgpt_manager import ChatGPTManager


config = ConfigReader(config_rel_path='resources/config.yaml').get_config()
logger = LoggingConfigurator.get_logger(config=config, log_file_name='whatsapp.log')
whatsapp_manager = WhatsAppManager(config)
gs_manager = GoogleSheetsManager(credentials_path=config.get('CRED_FILE_PATH_GS'),
                                 spreadsheet_id=config.get('SPREADSHEET_ID'),
                                 sheet_name=config.get('SHEET_NAME'))
chatgpt_manager = ChatGPTManager('wa', config)
app = FastAPI()


@app.get('/')
async def verify_token(request: Request):
    if request.query_params.get('hub.verify_token') == config.get('VERIFY_TOKEN_WHATSAPP'):
        logger.info('Verified webhook')
        response = PlainTextResponse(request.query_params.get('hub.challenge'), status_code=200)

        return response

    logger.error('Webhook Verification failed')

    return 'Invalid verification token'


@app.post('/')
async def hook(request: Request):
    # Handle Webhook Subscriptions
    wa_message_data = await request.json()
    logger.info('Received webhook data: %s', wa_message_data)
    # mobile = whatsapp_manager.messenger.get_mobile(wa_message_data)
    mobile = '789231558945'
    # mobile = '789198897172'
    # mobile = '789516789404'
    event_data = whatsapp_manager.get_event_data(wa_message_data)

    if event_data.get('message_type'):
        if not gs_manager.is_duplicate(event_data.get('timestamp'), 'timestamp'):
            logger.info('Received a text message, sending for processing.')

            wa_message_data, conversation_id, client_phone = whatsapp_manager.preprocess_for_gs(wa_message_data)
            # configs need to be different for different entities as class attributes
            gs_manager.save_data(data=wa_message_data)

            last_message_timestamp = chatgpt_manager.last_timestamp
            message_history = gs_manager.get_data_by_id(conversation_id, 'conversation_id',
                                                        last_message_timestamp, 'timestamp')

            chatgpt_manager.preprocess_for_myself(message_history)
            cgpt_response_data = chatgpt_manager.send_request_gpt3()

            whatsapp_manager.send(mobile=mobile,
                                  message=chatgpt_manager.preprocess_for_sending(cgpt_response_data))

            cgpt_response_data = chatgpt_manager.preprocess_data_for_gs(cgpt_response_data,
                                                                        conversation_id=conversation_id,
                                                                        client_phone=client_phone)
            gs_manager.save_data(data=cgpt_response_data)

        else:
            logger.info('Received duplicate webhook message.')

    return 'OK'


if __name__ == '__main__':
    run(app, host="0.0.0.0", port=8000)
