from heyoo import WhatsApp


class WhatsAppManager:
    def __init__(self, config):
        self.config = config
        self.messenger = WhatsApp(token=self.config.get('TOKEN_WHATSAPP'),
                                  phone_number_id=self.config.get('PHONE_NUMBER_ID_WHATSAPP'))

    def send(self, message, mobile):
        self.messenger.send_message(message, mobile)

    def get_event_data(self, wa_data):
        result = dict()

        result['changed_field'] = self.messenger.changed_field(wa_data)
        result['event_type'] = self.messenger.get_event_type(wa_data)

        if result['event_type'] == 'messages':
            result['message_type'] = self.messenger.get_message_type(wa_data)

        return result

    def preprocess_for_gs(self, data):
        conversation_id = self.messenger.get_mobile(data)
        client_phone = self.messenger.preprocess(data).get('metadata').get('display_phone_number')
        processed_data = [
                self.messenger.get_message_id(data),
                self.messenger.get_message(data),
                self.config.get('TEXT_MESSAGE_TYPE_WA'),
                conversation_id,
                client_phone,
                self.messenger.get_message_timestamp(data)
        ]

        return processed_data, conversation_id, client_phone
