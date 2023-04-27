from aiogram import Bot, Dispatcher
from aiogram.types import ContentTypes as ct, Message


class TelegramManager:
    def __init__(self, config):
        self.config = config
        self.bot = Bot(token=self.config.get('TOKEN_TELEGRAM'))
        self.dp = Dispatcher(self.bot)
        self.update_id = None
        self.all_but_text = ct.AUDIO | ct.DOCUMENT | ct.GAME | ct.PHOTO | ct.STICKER | ct.VIDEO | ct.VIDEO_NOTE \
                            | ct.VOICE | ct.CONTACT | ct.LOCATION | ct.VENUE | ct.POLL | ct.DICE | ct.NEW_CHAT_MEMBERS \
                            | ct.LEFT_CHAT_MEMBER | ct.INVOICE | ct.SUCCESSFUL_PAYMENT | ct.CONNECTED_WEBSITE \
                            | ct.MIGRATE_TO_CHAT_ID | ct.MIGRATE_FROM_CHAT_ID | ct.UNKNOWN
        self.text_message = ct.TEXT

    def preprocess_for_gs(self, text_message_data: Message):
        chat_id = text_message_data.chat.id
        username = text_message_data.chat.username
        processed_data = [
            self.update_id,
            text_message_data.message_id,
            text_message_data.text,
            self.config.get('TEXT_MESSAGE_TYPE_TG'),
            chat_id,
            username,
            text_message_data.date.timestamp()
        ]

        return processed_data, self.update_id, chat_id, username
