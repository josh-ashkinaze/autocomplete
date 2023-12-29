"""
Author: Joshua Ashkinaze
Date: 2023-12-26

Description: This file contains the main Flask app that handles the autocomplete requests. A user writes in a text editor, and
the app autocompletes the user's response as if this specific user experienced a specific event.
"""

import json
import random
import re
import string

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from config import AppConfig
from forms import CharacterForm, EventForm

app = Flask(__name__)
app_config = AppConfig()
app.config['SECRET_KEY'] = app_config.flask_secret_key


@app.route('/')
def initial():
    if app_config.is_offline and app_config.is_prod:
        return render_template('offline.html'), 503  # HTTP 503 Service Unavailable
    if not app_config.hardcoded:  # Ask user to create character and event
        return redirect(url_for('user_settings'))
    else:  # Use hardcoded character and event
        session['character_description'] = app_config.character_description
        session['event_name'] = app_config.event['name']
        session['event_description'] = app_config.event_description
        return redirect(url_for('index'))


@app.route('/index')
def index():
    return render_template('index.html',
                           debounce_time=app_config.debounce_time,
                           min_sentences=app_config.min_sentences,
                           stuck_prompts=app_config.stuck_prompts)


@app.route('/autocomplete', methods=['GET', 'POST'])
def autocomplete():
    """ Handle the autocomplete request. """
    text = normalize_spacing(request.json.get('text'))
    context, incomplete_sentence = get_context_and_incomplete_sentence(normalize_spacing(text))
    context, incomplete_sentence = normalize_spacing(context), normalize_spacing(incomplete_sentence)
    include_event = random.random() <= app_config.event_relevant
    print("INCLUDE EVENT", include_event)
    if include_event:
        temperature = app_config.temperature_range[0]
    else:
        temperature = random.uniform(*app_config.temperature_range)
    completion = normalize_spacing(
        get_chat_completion(character_description=session['character_description'], event=session['event_name'],
                            event_effects=session['event_description'],
                            include_event=include_event, model=app_config.model,
                            context=context, incomplete_sentence=incomplete_sentence,
                            temperature=temperature,
                            frequency_penalty=app_config.frequency_penalty,
                            max_tokens=random.randint(*app_config.token_range), top_p=app_config.top_p))
    completion_no_prompt = remove_prompt_words(completion)
    full_word_completion = normalize_spacing(extract_complete_words(completion_no_prompt))
    de_duped_completion = normalize_spacing(remove_duplicated_completion(incomplete_sentence, full_word_completion))
    d = {'text': text, 'context': context, 'incomplete_sentence': incomplete_sentence, 'completion': completion,
         'full_word_completion': full_word_completion, 'de_duped_completion': de_duped_completion,
         'completion_no_prompt': completion_no_prompt}
    print(d)
    return jsonify(completion=de_duped_completion)


############################################################
# HANDLE CHARACTER AND EVENT CREATION
############################################################
@app.route('/user_settings', methods=['GET', 'POST'])
def user_settings():
    character_form = CharacterForm()
    event_form = EventForm()
    if request.method == 'POST':
        if character_form.validate_on_submit() and event_form.validate_on_submit():
            flash('Character and event created successfully!', 'success')
            session['character_description'] = construct_character_description(character_form)
            session['event_name'] = event_form.event.data
            session['event_description'] = get_dynamic_effects(session['character_description'], session['event_name'])
            return redirect(url_for('index'))
        else:
            flash('Please correct the errors in the form.', 'error')
    elif request.method == 'GET':
        return render_template('user_settings.html', character_form=character_form, event_form=event_form)


def get_dynamic_effects(character_description, event_description, attempt_no=0, max_attempts=2):
    if attempt_no > max_attempts:
        return None
    else:
        try:
            client = app_config.client
            response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[
                {"role": "system", "content": "You are a helpful, factual, and highly specific assistant."},
                {"role": "user",
                 "content": f"""INSTRUCTIONS\nGiven a description of a person, return an enumerated list of the likely effects of {event_description} on this person. 
                     Be very specific and very realistic. The effects can be related to any aspect of the person (their personality, demographics, hobbies, location etc.) but the effects must be realistic and specific. Do not exaggerate.
                    DESCRIPTION:
                    {character_description}"""}], temperature=0.6, max_tokens=250, top_p=1)
            answer = json.loads(response.choices[0].json())['message']['content']
            return answer
        except Exception as e:
            print(e)
            return get_dynamic_effects(character_description, event_description, attempt_no + 1, max_attempts)


def construct_character_description(form):
    return f"I am {form.age.data} years old from {form.location.data}, working as a {form.occupation.data}. My hobbies include {form.hobbies.data}. My friends describe me as {form.personality.data}."


############################################################
# FUNCTIONS FOR PROCESSING TEXT
############################################################
def get_chat_completion(character_description, event, event_effects, context, incomplete_sentence, model, temperature,
                        max_tokens, top_p, include_event, frequency_penalty=0, attempt_no=0, max_attempts=1):
    if attempt_no > max_attempts:
        return None
    else:
        try:
            client = app_config.client
            if include_event:
                system_instructions = f"INSTRUCTIONS\nA character is describing a day in their life. Finish a sentence in the style of a CHARACTER who is affected by {event} and feeling the effects of this event.\n\nCHARACTER\n{character_description}\nEVENT\n{event}\nEVENT EFFECTS\n{event_effects}.\n\nCONSTRAINTS\n-Given the CONTEXT of what was written, finish the INCOMPLETE SENTENCE in the style of the character, affected by the event.\n- Use clear, plain, simple language that a simple person would use.\n- Everything you write should be highly realistic and not imaginative.\n-Do not be overly emotional. Be realistic."
            else:
                system_instructions = f"INSTRUCTIONS\nA character is describing a day in their life. Finish a sentence in the style of the CHARACTER.\n\nCHARACTER\n{character_description}\n\nCONSTRAINTS\n-Given the CONTEXT of what was written, finish the INCOMPLETE SENTENCE in the style of the character.\n- Use clear, plain, simple language that a simple person would use.\n- Everything you write should be highly realistic and not imaginative.\n-Do not be overly emotional. Be realistic."
            response = client.chat.completions.create(model=model,
                                                      messages=[{"role": "system", "content": system_instructions},
                                                                {"role": "user",
                                                                 "content": f"CONTEXT:{context}\n\nINCOMPLETE SENTENCE:{incomplete_sentence}"}],
                                                      temperature=temperature, max_tokens=max_tokens, top_p=top_p)
            print(system_instructions)
            print(f"CONTEXT:{context}\n\nINCOMPLETE SENTENCE:{incomplete_sentence}")

            answer = json.loads(response.choices[0].json())['message']['content']
            return answer
        except Exception as e:
            return get_chat_completion(context=context, incomplete_sentence=incomplete_sentence, model=model,
                                       temperature=temperature, max_tokens=max_tokens, top_p=top_p,frequency_penalty=frequency_penalty,
                                       include_event=include_event, attempt_no=attempt_no + 1, max_attempts=2)


def remove_duplicated_completion(incomplete_sentence, completion):
    if not incomplete_sentence or not completion:
        return completion

    incomplete_sentence = incomplete_sentence.strip()
    completion = completion.strip()

    # Case 1: Direct overlap
    if completion.startswith(incomplete_sentence):
        return completion[len(incomplete_sentence):].lstrip()

    # Case 2: Completion is a subset of incomplete
    elif incomplete_sentence.endswith(completion):
        return ""

    # Case 3: Non Direct Overlap
    else:
        for i in range(len(completion)):
            if incomplete_sentence.endswith(completion[:i]):
                return completion[i:].lstrip()

        # Case 4: No overlap
        return completion


def normalize_spacing(text):
    if text is None:
        return None
    text = text.replace(u'\xa0', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def remove_prompt_words(text):
    """Remove any prompt wods that LLM accidently included in answer"""
    bad_words = ['INSTRUCTIONS', 'CONTEXT', 'INCOMPLETE SENTENCE', 'CHARACTER DESCRIPTION', 'EVENT', 'EVENT EFFECTS']
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, bad_words)) + r')\b')
    text = pattern.sub('', text)
    return text


def get_context_and_incomplete_sentence(text):
    """
    We feed into the model both the prior context for what was written and the current
    sentence to complete. This function splits those things.
    """
    sentence_terminators = r"[.!?]"
    sentences = re.split('({})'.format(sentence_terminators), text)
    sentences = [sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '') for i in
                 range(0, len(sentences), 2)]

    if len(sentences) == 1:
        # Single sentence which could be complete or incomplete
        if text.endswith(tuple(sentence_terminators)):
            return sentences[0].strip(), ''
        else:
            return '', sentences[0].strip()
    else:
        if text.endswith(tuple(sentence_terminators)):
            context = ' '.join(sentences)
            incomplete_sentence = ""
        else:
            context = ' '.join(sentences[:-1])
            incomplete_sentence = sentences[-1]

    return context.strip(), incomplete_sentence.strip()


def extract_complete_words(text):
    """
    Extracts complete words from the given text since sometimes the LLM returns
    incomplete words depending on tokens. But in practice, it is expensive to accurately check if a word is complete,
    so a simple heuristic is used:

    - If the immediate character before the last word is whitespace or punctuation, then the word is necessarily complete.
    - If the word is not necessarily complete, then it is assumed to be incomplete.
    - Note: This means in practice we often just delete the last word of the completion.

    EXAMPLES
    "I went to the store to buy some mil" -> "I went to the store to buy some"
    "I went to the store to buy some milk" -> "I went to the store to buy some"

    """
    if not text:
        return text
    words = text.split()
    if not words:
        return text
    if text[-1] in string.whitespace + string.punctuation:
        return text
    else:
        return ' '.join(words[:-1])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app_config.port, debug=not app_config.is_prod)
