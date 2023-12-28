import yaml
import json
from openai import OpenAI
import os
import secrets


class AppConfig:
    def __init__(self, config_file='config.yaml'):
        self.config = self.load_yaml_config(config_file)
        self.hardcoded = self.config['hardcode_character_and_event']

        # ################################
        # OpenAI settings
        # ################################
        self.model = self.config['openai']['model']
        self.temperature_range = (self.config['openai']['temperature_min'], self.config['openai']['temperature_max'])
        self.token_range = (self.config['openai']['max_tokens_min'], self.config['openai']['max_tokens_max'])
        self.top_p = self.config['openai']['top_p']
        self.max_attempts = self.config['openai']['max_attempts']
        self.openai_key = os.getenv('OPENAI_KEY')
        if not self.openai_key:
            raise ValueError(
                "OPENAI_KEY environment variable not set. "
                "To set it:\n"
                "- On macOS or Linux, use: export OPENAI_KEY=\"your_openai_key_here\"\n"
                "- On Windows (PowerShell), use: $env:OPENAI_KEY=\"your_openai_key_here\""
                "\nReplace 'your_openai_key_here' with your actual OpenAI API key."
            )
        self.client = OpenAI(api_key=self.openai_key)

        # ################################
        # Character and event settings
        # ################################
        if self.hardcoded:
            self.event = self.config['event']
            self.character = self.config['characters']['p1']
            self.character_description = self.construct_character_description()
            self.event_description = self.get_dynamic_effects()
            print(self.event_description)
        else:
            #raise NotImplementedError("Dynamic character and event creation is WIP")
            pass

        # ################################
        # Environment settings
        # ################################
        self.is_offline = self.config['app_is_offline']
        self.port = int(os.environ.get('PORT', 5000))
        self.is_prod = os.environ.get('RAILWAY_ENVIRONMENT_NAME') is not None
        self.flask_secret_key = secrets.token_hex(16)

        # ################################
        # Autocomplete behavior settings
        # ################################
        self.debounce_time = self.config['autocomplete']['debounce_time']
        self.min_sentences = self.config['autocomplete']['min_sentences']
        self.event_relevant = self.config['autocomplete']['event_relevant']
        self.stuck_prompts = self.config['stuck_prompts']
        assert self.min_sentences >= 1, "min_sentences must be at least 1"
        assert self.event_relevant > 0 and self.event_relevant <= 1, "min_sentences must be in (0, 1]"

    def load_yaml_config(self, filepath):
        """ Load configuration from a YAML file. """
        with open(filepath, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

    def construct_character_description(self):
        char_info = self.character
        description = (
            f"I am {char_info['age']} years old, from {char_info['location']}. "
            f"I work as a {char_info['occupation']}. "
            f"My hobbies include {' and '.join(char_info['hobbies'])}. "
            f"People describe me as {char_info['personality']}.")
        return description

    def get_dynamic_effects(self, attempt_no=0, max_attempts=2):
        if attempt_no > max_attempts:
            return None
        else:
            try:
                client = self.client
                response = client.chat.completions.create(model="gpt-3.5-turbo",
                                                          messages=[
                                                              {"role": "system",
                                                               "content": "You are a helpful, factual, and highly specific assistant."},
                                                              {"role": "user",
                                                               "content": f"""INSTRUCTIONS\nGiven a description of a person, return an enumerated list of the likely effects of {self.event['name'].lower()} on this person. 
                         Be very specific and very realistic. The effects can be related to any aspect of the person (their personality, demographics, hobbies, location etc.) but the effects must be realistic and specific. Do not exaggerate. Answer in 50 words.
                        DESCRIPTION:
                        {self.character_description}"""}],
                                                          temperature=0.8, max_tokens=200, top_p=1)
                answer = json.loads(response.choices[0].json())['message']['content']
                return answer
            except Exception as e:
                print(e)
                # Corrected recursive call here
                return self.get_dynamic_effects(attempt_no + 1, max_attempts)
