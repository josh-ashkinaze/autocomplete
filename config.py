import yaml
import json
from openai import OpenAI
import os
import secrets
from litellm import completion
from concurrent.futures import ThreadPoolExecutor, as_completed

class AppConfig:
    def __init__(self, config_file='config.yaml'):
        self.config = self.load_yaml_config(config_file)
        self.hardcoded = self.config['hardcode_character_and_event']
        self.experiment_enabled = self.config['enable_experiment']

        # ################################
        # LLM settings
        # ################################

        # Default settings are for gpt models
        self.effects_generator_model = self.config['event']['effects_generator_model']
        self.model = self.config['llm']['model']
        self.temperature_range = (self.config['llm']['temperature_min'], self.config['llm']['temperature_max'])
        self.token_range = (self.config['llm']['max_tokens_min'], self.config['llm']['max_tokens_max'])
        self.frequency_penalty = self.config['llm']['frequency_penalty']
        self.max_attempts = self.config['llm']['max_attempts']
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        # Change settings for Anthropic
        # OPENAI temperature is in [0,2] and Anthropic is in [0,1]
        if "claude" in self.model.lower():
            self.frequency_penalty = None
            self.temperature_range = (min(self.config['llm']['temperature_min'],0), min(self.config['llm']['temperature_max'],1))
            print(f"Anthropic model detected. Adjusting temperature range to {self.temperature_range}")

        for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            # if model has 'gpt' in it ensure openai key else if 'claude' enssure anthropic
            if "gpt" in self.model.lower() and not os.getenv('OPENAI_API_KEY'):
                raise ValueError(f"{key} environment variable not set. "
                                 f"To set it:\n"
                                 f"- On macOS or Linux, use: export {key}=\"key\"\n"
                                 f"- On Windows (PowerShell), use: $env:{key}=\"key\""
                                 f"\nReplace 'key' with your actual API key.")
            elif "claude" in self.model.lower() and not os.getenv('ANTHROPIC_API_KEY'):
                raise ValueError(f"{key} environment variable not set. "
                                 f"To set it:\n"
                                 f"- On macOS or Linux, use: export {key}=\"key\"\n"
                                 f"- On Windows (PowerShell), use: $env:{key}=\"key\""
                                 f"\nReplace 'key' with your actual API key.")

        self.client = OpenAI(api_key=self.openai_key)
        self.event_constraints = "\n" + "\n-".join(self.config['autocomplete']['constraints'])
        self.non_event_constraints = "\n" + "-\n".join(x for x in self.config['autocomplete']['constraints']if "{event}" not in x)


        # ################################
        # Character and event settings
        # ################################
        if self.hardcoded:
            self.event = self.config['event']
            self.character = self.config['characters']['p1']
            self.character_description = self.construct_character_description()

            with ThreadPoolExecutor(max_workers=2) as executor:
                future_dynamic_effects = executor.submit(self.get_dynamic_effects)
                future_predicted_event = executor.submit(self.get_predicted_event)
                event_description = future_dynamic_effects.result()
                predicted_event = future_predicted_event.result()

            self.event_description = event_description
            self.predicted_event = predicted_event

            print(self.event_description)
            print(self.predicted_event)



        elif self.experiment_enabled:
            self.event = self.config['event']
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
        return f"I am {char_info['age']} years old from {char_info['location']}, working as a {char_info['occupation']}. My hobbies include {char_info['hobbies']}. Here is how I describe myself: '''{char_info['personality']}'''"

    def get_dynamic_effects(self, attempt_no=0, max_attempts=2):
        if attempt_no > max_attempts:
            return None
        else:
            try:
                client = self.client
                response = client.chat.completions.create(model=self.effects_generator_model, messages=[
                    {"role": "system", "content": "You are a helpful, factual, and highly specific assistant."},
                    {"role": "user",
                     "content": f"""INSTRUCTIONS\nGiven a description of a person, return an enumerated list of the likely effects of {self.event} on this person. 
                         Be very specific and very realistic. The effects can be related to any aspect of the person (their personality, demographics, hobbies, location etc.) but the effects must be concrete, realistic and specific. Do not exaggerate. Write 100 words.
                        DESCRIPTION:
                        {self.character_description}"""}], temperature=0.6, max_tokens=1000, top_p=1)
                answer = json.loads(response.choices[0].json())['message']['content']
                return answer
            except Exception as e:
                print(e)
                return self.get_dynamic_effects(attempt_no + 1, max_attempts)

    def get_predicted_event(self):
        client = self.client
        response = client.chat.completions.create(
            model=self.effects_generator_model,
            messages=[
                {"role": "system", "content": "You are a helpful, factual, and highly specific assistant."},
                {"role": "user", "content": (
                    f"INSTRUCTIONS\n"
                    f"Given a description of a person, return a realistic scenario that would cause this person to experience {self.event}. Rely ONLY on what is in the description."
                    f"Be very specific and very realistic. Do not exaggerate. Write 20-30 words. DO NOT write about the effect of this event, but only focus on the scenario and how "
                    f"that would make them experience {self.event}. Return one such event. Write in second person.\n"
                    f"DESCRIPTION:\n"
                    f"{self.character_description}"
                )}
            ],
            temperature=0.6,
            max_tokens=1000,
            top_p=1
        )
        return json.loads(response.choices[0].json())['message']['content']