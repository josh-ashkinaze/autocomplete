"""
Author: Joshua Ashkinaze
Date: 2023-12-26

Description: This file contains the main Flask app that handles the autocomplete requests. A user writes in a text editor, and
the app autocompletes the user's response as if this specific user experienced a specific event.
"""

from flask import Flask, request, render_template, jsonify
from config import AppConfig
import json
import string
import random
import re

app = Flask(__name__)
app_config = AppConfig()


def get_chat_completion(character_description,
                        event,
                        event_effects,
                        context,
                        incomplete_sentence,
                        model,
                        temperature,
                        max_tokens,
                        top_p,
                        attempt_no=0,
                        max_attempts=2):
    if attempt_no > max_attempts:
        return None
    else:
        try:
            client = app_config.client
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"INSTRUCTIONS\nFinish a sentence in the style of a character who is affected by {event}.\nCHARACTER DESCRIPTION:\n{character_description}\nEVENT:\n{event}\nEVENT EFFECTS:\n{event_effects}.\n\nGiven the CONTEXT of what the user finish the INCOMPLETE SENTENCE to sound like the character who is affected by the event."
                    },
                    {
                        "role": "user",
                        "content": f"CONTEXT:{context}\n\nINCOMPLETE SENTENCE:{incomplete_sentence}"
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            answer = json.loads(response.choices[0].json())['message']['content']
            return answer
        except Exception as e:
            print(e)
            return get_chat_completion(context=context, incomplete_sentence=incomplete_sentence, model=model,
                                       attempt_no=attempt_no + 1, max_attempts=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    """ Handle the autocomplete request. """
    text = request.json.get('text')
    context, incomplete_sentence = get_context_and_incomplete_sentence(text)
    completion = get_chat_completion(
        character_description=app_config.character_description,
        event=app_config.event['name'],
        event_effects=app_config.event['effects'],
        model=app_config.model,
        context=context,
        incomplete_sentence=incomplete_sentence,
        temperature=random.uniform(*app_config.temperature_range),
        max_tokens=random.randint(*app_config.token_range),
        top_p=app_config.top_p
    )
    # Make sure LLM didn't stop mid-word
    full_word_completion = extract_complete_words(completion)
    de_duped_completion = remove_duplicated_completion(context, full_word_completion)
    print("TEXT:", text)
    print("CONTEXT:", context)
    print("INCOMPLETE SENTENCE:", incomplete_sentence)
    print("COMPLETION:", completion)
    print("FULL WORD COMPLETION:", full_word_completion)
    print("REMOVE DUPLICATED COMPLETION:", de_duped_completion)
    return jsonify(completion=de_duped_completion)


############################################################
# HELPER FUNCTIONS #
############################################################
def remove_duplicated_completion(text, completion):
    """
    Sometimes the completion includes parts of the sentence it was supposed to complete,
    so this function returns the completion removing any duplicated parts.
    """
    if not text or not completion:
        return completion

    text = text.strip()
    completion = completion.strip()

    # Find the shortest possible overlap
    overlap = ""
    for i in range(1, min(len(text), len(completion)) + 1):
        if text.endswith(completion[:i]):
            overlap = completion[:i]

    # Remove the overlapping part from the completion
    return completion[len(overlap):]


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
    incomplete words. In practice, it is expensive to accurately check if a word is complete (would require spell-check or something)
    so a simple heuristic is used: if the word ends with a space or punctuation, it is complete. Else, assume it could be
    incomplete and remove that word.
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
