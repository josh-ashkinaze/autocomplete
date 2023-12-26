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
    """Redirect to character and event creation page."""
    if not app_config.hardcoded:
        # Ask for character and event from user
        return redirect(url_for('char_and_event'))
    else:
        # Read this stuff from YAML file
        session['character_description'] = app_config.character_description
        session['event_name'] = app_config.event
        session['event_description'] = app_config.event_description
        return redirect(url_for('index'))


@app.route('/index')
def index():
    return render_template('index.html', debounce_time=app_config.debounce_time, min_sentences=app_config.min_sentences)


@app.route('/autocomplete', methods=['GET', 'POST'])
def autocomplete():
    """ Handle the autocomplete request. """
    text = normalize_spacing(request.json.get('text'))
    context, incomplete_sentence = get_context_and_incomplete_sentence(normalize_spacing(text))
    context, incomplete_sentence = normalize_spacing(context), normalize_spacing(incomplete_sentence)
    ct = random.random()
    print(ct)
    print(app_config.event_relevant)
    include_event = random.random() <= app_config.event_relevant
    print("include_event", include_event)
    completion = normalize_spacing(
        get_chat_completion(character_description=session['character_description'], event=session['event_name'],
                            event_effects=session['event_description'], include_event=include_event, model=app_config.model,
                            context=context, incomplete_sentence=incomplete_sentence,
                            temperature=random.uniform(*app_config.temperature_range),
                            max_tokens=random.randint(*app_config.token_range), top_p=app_config.top_p))
    # Make sure LLM didn't stop mid-word
    full_word_completion = normalize_spacing(extract_complete_words(completion))
    de_duped_completion = normalize_spacing(remove_duplicated_completion(incomplete_sentence, full_word_completion))
    d = {'text': text, 'context': context, 'incomplete_sentence': incomplete_sentence, 'completion': completion,
         'full_word_completion': full_word_completion, 'de_duped_completion': de_duped_completion}
    # print(d)
    return jsonify(completion=de_duped_completion)


############################################################
# HANDLE CHARACTER CREATION
############################################################
@app.route('/char_and_event', methods=['GET', 'POST'])
def char_and_event():
    character_form = CharacterForm()
    event_form = EventForm()
    if request.method == 'POST':
        if character_form.validate_on_submit() and event_form.validate_on_submit():
            flash('Character and event created successfully!', 'success')
            session['character_description'] = construct_character_description(character_form)
            session['event_name'] = event_form.event_name.data
            session['event_description'] = get_dynamic_effects(session['character_description'], session['event_name'])
            return redirect(url_for('index'))  # Redirect to the index route
        else:
            flash('Please correct the errors in the form.', 'error')
    elif request.method == 'GET':
        return render_template('char_and_event.html', character_form=character_form, event_form=event_form)


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
    return f"{form.name.data}, a {form.age.data}-year-old {form.gender.data.lower()} from {form.location.data}, working as a {form.occupation.data}, with hobbies including {form.hobbies.data}. Known for being {form.personality.data}."


############################################################
# FUNCTIONS FOR PROCESSING TEXT
############################################################
def get_chat_completion(character_description, event, event_effects, context, incomplete_sentence, model, temperature,
                        max_tokens, top_p, include_event, attempt_no=0, max_attempts=1):
    if attempt_no > max_attempts:
        return None
    else:
        try:
            client = app_config.client
            if include_event:
                system_instructions = f"INSTRUCTIONS\nFinish a sentence in the style of a character who is affected by {event}.\nCHARACTER DESCRIPTION:\n{character_description}\nEVENT:\n{event}\nEVENT EFFECTS:\n{event_effects}.\n\nGiven the CONTEXT of what the character wrote, finish the INCOMPLETE SENTENCE to sound like the character who is affected by the event."
            else:
                system_instructions = f"INSTRUCTIONS\nFinish a sentence in the style of a character.\nCHARACTER DESCRIPTION:\n{character_description}.\n\nGiven the CONTEXT of what the character wrote, finish the INCOMPLETE SENTENCE to sound like the character, consistent with what was written."

            response = client.chat.completions.create(model=model,
                                                      messages=[{"role": "system", "content": system_instructions},
                                                                {"role": "user", "content": f"CONTEXT:{context}\n\nINCOMPLETE SENTENCE:{incomplete_sentence}"}],
                                                      temperature=temperature, max_tokens=max_tokens, top_p=top_p)
            answer = json.loads(response.choices[0].json())['message']['content']

            return answer
        except Exception as e:
            print(e)
            return get_chat_completion(context=context, incomplete_sentence=incomplete_sentence, model=model,
                                       temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                                       include_event=include_event, attempt_no=attempt_no + 1, max_attempts=2)


def remove_duplicated_completion(incomplete_sentence, completion):
    """
    Sometimes the LLM returns a completion that is a duplicate of the incomplete sentence. This function removes that duplication.
    """
    if not incomplete_sentence or not completion:
        return None

    incomplete_sentence = normalize_spacing(incomplete_sentence.strip())
    completion = normalize_spacing(completion.strip())

    # Case 1: Starts With Overlap
    # Incomplete sentence = But
    # Completion = But I want to go
    # Desired Completion = I want to go to
    # Solution: Strip from the length of incomplete sentence onwards
    if completion.startswith(incomplete_sentence):
        return completion[len(incomplete_sentence):].lstrip()

    # Case 2: Total Overlap But Non-Starting
    # Incomplete sentence = But I went to the mall
    # Completion = went to the mall
    # Desired Completion = None
    # Solution: Check if the start of incomplete_sentence is the same as the completion
    elif incomplete_sentence[:len(completion)] == completion:
        return None

    else:
        overlap_len = 0
        for i in range(len(incomplete_sentence)):
            if completion.startswith(incomplete_sentence[i:]):
                overlap_len = len(incomplete_sentence) - i
                break

        # Case 3: Non Direct Overlap
        # Incomplete sentence = I just want to go
        # Completion = just want to go to the store
        # Desired Completion = to the store
        # Solution: Remove the length of the overlap plus trailing space
        if overlap_len > 0:
            print("Case2")
            return completion[overlap_len:].strip()

        # Case 4: No Overlap
        # Incomplete sentence = Now I spend my days
        # Completion = playing guitar
        # Desired Completion = playing guitar
        else:
            return completion


def normalize_spacing(text):
    if text is None:
        return None
    text = text.replace(u'\xa0', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
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

    - If the immediate character before the last word is whitespace or punctuation, then the word is neceesarily complete.
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
    app.run(debug=True)
