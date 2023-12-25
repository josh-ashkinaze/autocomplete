import yaml
import json
from openai import OpenAI
import os

class AppConfig:
    def __init__(self, config_file='config.yaml', secrets_file='secrets.json'):
        self.config = self.load_yaml_config(config_file)
        self.secrets = self.load_json_config(secrets_file)

        # OpenAI settings
        self.model = self.config['openai']['model']
        self.temperature_range = (self.config['openai']['temperature_min'], self.config['openai']['temperature_max'])
        self.token_range = (self.config['openai']['max_tokens_min'], self.config['openai']['max_tokens_max'])
        self.top_p = self.config['openai']['top_p']
        self.max_attempts = self.config['openai']['max_attempts']
        self.event = self.config['event']

        # ToDo: make this dynamic
        self.character = self.config['characters']['alan']
        self.character_description = self.construct_character_description()

        # Use an environment variable for the OpenAI key
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


        if self.event['effects'] is None:
            self.event['effects'] = self.get_dynamic_effects()
        else:
            self.event['effects'] = self.config['event']['effects']

    def load_yaml_config(self, filepath):
        """ Load configuration from a YAML file. """
        with open(filepath, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

    def load_json_config(self, filepath):
        """ Load configuration from a JSON file. """
        with open(filepath) as jsonfile:
            return json.load(jsonfile)

    def construct_character_description(self):
        # ToDo: make this dynamic
        char_info = self.character
        description = (
            f"{char_info['name']}, {char_info['age']} years old, {char_info['gender']} from {char_info['location']}. "
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
                     Be very specific and very realistic. The effects can be related to any aspect of the person (their personality, demographics, hobbies, location etc.) but the effects must be realistic and specific. Do not exaggerate.
                    DESCRIPTION:
                    {self.character_description}"""}],
                                                          temperature=0.6, max_tokens=250, top_p=1)
                answer = json.loads(response.choices[0].json())['message']['content']
                return answer
            except Exception as e:
                print(e)
                # Corrected recursive call here
                return self.get_dynamic_effects(attempt_no + 1, max_attempts)

a = AppConfig()
