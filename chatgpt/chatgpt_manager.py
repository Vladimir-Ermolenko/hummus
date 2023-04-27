import openai
from collections import defaultdict


class ChatGPTManager:
    def __init__(self, platform, config):
        self.config = config
        self.platform = platform
        self.message_history_base_gpt3 = [
            # try to put rules a a system parameter
            # can there be one more role so that GPT can understand that the customer is not the same person who gave the rules?
            {'role': 'system', 'content': self.config.get('PERSONALITY')},
            {'role': 'user', 'content': self.config.get('RULES_DEMO')},
            # {'role': 'assistant', 'content': 'Sure, waiting for product description.'},
            {'role': 'user', 'content': self.config.get('PRODUCT_DESCRIPTION')},
            # {'role': 'assistant', 'content': 'Sure, waiting for audience description.'},
            # {'role': 'user', 'content': self.config.get('AUDIENCE_DESCRIPTION')},
            # {'role': 'assistant', 'content': 'Sure, waiting for the list of clients problems.'},
            # {'role': 'user', 'content': self.config.get('CLIENTS_PROBLEMS')},
            # {'role': 'assistant', 'content': 'Sure, waiting for the list of questions.'},
            {'role': 'user', 'content': self.config.get('CUSTDEV_QUESTIONS')},
            # {'role': 'assistant', 'content': 'Sure, waiting for the list of facts about HUMMUS.'},
            # {'role': 'user', 'content': self.config.get('SOLUTIONS_COMPARISON')},
            # {'role': 'assistant', 'content': 'Sure, waiting for the greeting message.'},
            {'role': 'user', 'content': self.config.get('GREETING')},
            # {'role': 'assistant', 'content': 'Great, let\'s get started! I will start the conversation with this greeting.'}
        ]
        self.message_history_base_davinci = [
            f'{self.config.get("PERSONALITY")}',
            f'{self.config.get("RULES_DEMO")}',
            f'{self.config.get("PRODUCT_DESCRIPTION")}',
            f'{self.config.get("CUSTDEV_QUESTIONS")}',
            f'{self.config.get("GREETING")}',
            # 'HUMAN: Hello!',
            # 'JACKY: Hello! My name is Jacky, I\'m here to answer your questions about the HUMMUS service.',
        ]
        self.message_history = defaultdict(list)
        self.message_history_davinci = defaultdict(list)

        openai.organization = self.config.get('ORG_KEY_CHATGPT')
        openai.api_key = self.config.get('API_KEY_CHATGPT')

    # accepts the list with all the previous messages
    def send_request_gpt3(self, chat_id):
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=self.message_history.get(chat_id),
                temperature=0.1,
                top_p=1,
                n=1,
                stream=False,
                stop=['stop'],
                max_tokens=300,
                presence_penalty=0.6,
                frequency_penalty=0.5,
            )

            return response

        except openai.error.RateLimitError as e:
            print('Got an error, please resubmit your request.')
            print(e)

    def send_request_davinci(self, chat_id):
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt='\n'.join(self.message_history_davinci.get(chat_id)) + '\n',
            max_tokens=300,
            n=1,
            stop=[' HUMAN:', ' AI:', ' JACKY:'],
            temperature=0.3,
            presence_penalty=2,
            frequency_penalty=0.5,
        )

        return response

    def preprocess_data_for_gs(self, cgpt_response: dict, **kwargs):
        # move getters to functions
        processed_data = []
        if self.platform == 'wa':
            processed_data = [
                cgpt_response.get('id'),
                cgpt_response.get('choices')[0].get('message').get('content'),
                self.config.get('TEXT_MESSAGE_TYPE_GPT'),
                kwargs.get('conversation_id'),
                kwargs.get('client_phone'),
                cgpt_response.get('created')
            ]
        elif self.platform == 'tg':
            processed_data = [
                kwargs.get('update_id'),
                cgpt_response.get('id'),
                cgpt_response.get('choices')[0].get('message').get('content'),
                self.config.get('TEXT_MESSAGE_TYPE_GPT'),
                kwargs.get('chat_id'),
                kwargs.get('username'),
                cgpt_response.get('created')
            ]

        return processed_data

    def preprocess_data_for_gs_davinci(self, cgpt_response: dict, **kwargs):
        processed_data = []
        if self.platform == 'wa':
            processed_data = [
                cgpt_response.get('id'),
                cgpt_response.get('choices')[0].get('text'),
                self.config.get('TEXT_MESSAGE_TYPE_GPT'),
                kwargs.get('conversation_id'),
                kwargs.get('client_phone'),
                cgpt_response.get('created')
            ]

        elif self.platform == 'tg':
            processed_data = [
                kwargs.get('update_id'),
                cgpt_response.get('id'),
                self.clear(cgpt_response.get('choices')[0].get('text')),
                self.config.get('TEXT_MESSAGE_TYPE_GPT'),
                kwargs.get('chat_id'),
                kwargs.get('username'),
                cgpt_response.get('created')
            ]

        return processed_data

    @staticmethod
    def preprocess_for_sending(cgpt_response):
        return cgpt_response.get("choices")[0].get("message").get("content")

    @staticmethod
    def clear(text):
        index = text.find('JACKY: ')
        if index != -1:
            text = text[index + 7:]

        return text

    def preprocess_for_sending_davinci(self, cgpt_response):
        completion = cgpt_response.get("choices")[0].get("text")
        completion = self.clear(completion)

        return completion

    def preprocess_for_myself(self, message_history, chat_id):
        # should accept rows with messages from gs, make a list of  dicts out of it and add it to self.message_history
        sorted_data = sorted(message_history, key=lambda x: int(x[-1]))

        # create a list of dictionaries
        output_data = []
        if self.platform == 'tg':
            for item in sorted_data:
                if item[3] == 'tg_text':
                    output_data.append({'role': 'user', 'content': item[2]})
                elif item[3] == 'gpt_text':
                    output_data.append({'role': 'assistant', 'content': item[2]})

        elif self.platform == 'wa':
            for item in sorted_data:
                if item[2] == 'wa_text':
                    output_data.append({'role': 'user', 'content': item[1]})
                elif item[2] == 'gpt_text':
                    output_data.append({'role': 'assistant', 'content': item[1]})

        self.message_history[chat_id].extend(output_data)

        # if sorted_data:
        #     self.last_timestamp = int(sorted_data[-1][-1])

    def preprocess_for_myself_davinci(self, message_history, chat_id):
        sorted_data = sorted(message_history, key=lambda x: int(x[-1]))

        # create a list of dictionaries
        output_data = []
        if self.platform == 'tg':
            for item in sorted_data:
                if item[3] == 'tg_text':
                    output_data.append(f'HUMAN: {item[2]}')
                elif item[3] == 'gpt_text':
                    output_data.append(f'JACKY: {item[2]}')

        if not self.message_history_davinci.get(chat_id):
            self.message_history_davinci[chat_id].extend(self.message_history_base_davinci)

        self.message_history_davinci[chat_id].extend(output_data)


if __name__ == '__main__':
    pass
