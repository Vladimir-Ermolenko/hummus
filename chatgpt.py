import yaml
import openai
from pathlib import Path

curr_dir = Path(__file__).parent

with open(curr_dir.joinpath('config.yaml')) as config_file:
    config = yaml.safe_load(config_file)

API_KEY_CHATGPT = config['API_KEY_CHATGPT']
ORG_KEY_CHATGPT = config['ORG_KEY_CHATGPT']

openai.organization = ORG_KEY_CHATGPT
openai.api_key = API_KEY_CHATGPT
