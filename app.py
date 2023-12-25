from flask import Flask, request, render_template, jsonify
from openai import OpenAI
import json
import string
import random
import re

app = Flask(__name__)

# Load OpenAI API key
with open('secrets.json') as f:
    secrets = json.load(f)
openai_key = secrets['openai_key']

def get_chat_completion(context, incomplete_sentence, model="gpt-3.5-turbo", attempt_no=0, max_attempts=2):
  if attempt_no > max_attempts:
    return None
  else:
    try:
      client = OpenAI(api_key=openai_key)
      response = client.chat.completions.create(
        model=model,
        messages=[
          {
            "role": "system",
              "content": f"INSTRUCTIONS\nWrite in the first person. You will autocomplete a character's sentence, as that character, writing in the first person. Adopt the character's characteristics, beliefs, attitudes, idioms, slang, ways of speaking, and general language style. When I provide you with CONTEXT and an INCOMPLETE SENTENCE, you will return the COMPLETED SENTENCE that is consistent with CONTEXT and the user's character. Write in the first person."
          },
          {
            "role": "user",
            "content": f"\nCHARACTER:\nA 25 year old very Italian guido from New Jersey who lives the Yankees and Israel.\nCONTEXT:{context}\n\nINCOMPLETE SENTENCE:{incomplete_sentence}"
          }
        ],
        temperature=random.uniform(0.8, 0.9),
        max_tokens=random.randint(10, 15),
        top_p=1
      )
      answer = json.loads(response.choices[0].json())['message']['content']
      return answer
    except Exception as e:
      print(e)
      return get_chat_completion(context, incomplete_sentence, model="gpt-3.5-turbo", attempt_no=attempt_no+1, max_attempts=2)

@app.route('/')
def index():
    return render_template('index.html')

def extract_complete_words(text):
    """
    Extracts complete words from the given text.
    A word is considered complete if it's followed by a space or punctuation.
    """
    if not text:
        return text

    words = text.split()
    if not words:
        return text

    # Check if the last character of the original text is a space or punctuation
    if text[-1] in string.whitespace + string.punctuation:
        return text  # The last word is complete
    else:
        # Return the text excluding the last word, which might be incomplete
        return ' '.join(words[:-1])

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    """ Handle the autocomplete request. """
    text = request.json.get('text')
    sanitized_text = sanitize_text(text)
    context, incomplete_sentence = get_context_and_incomplete_sentence(sanitized_text)
    completion = get_chat_completion(context=context, incomplete_sentence=incomplete_sentence)
    full_word_completion = remove_duplicated_completion(context, completion)
    print("TEXT:", text)
    print("CONTEXT:", context)
    print("INCOMPLETE SENTENCE:", incomplete_sentence)

    print("COMPLETION:", completion)
    print("FULL WORD COMPLETION:", full_word_completion)
    print("REMOVE DUPLICATED COMPLETION:", remove_duplicated_completion(context, completion))
    return jsonify(completion=remove_duplicated_completion(incomplete_sentence, completion))

def remove_duplicated_completion(text, completion):
    """
    Removes the duplicated part from the beginning of the completion
    if it overlaps with the end of the text.
    """
    # In case of some kind of error
    if not text or not completion:
        return ''

    # Remove the duplicated part from the beginning of the completion
    if completion.startswith(text):
        return completion.split(text)[-1]

    # In some cases the prior sentence contains a comma, colon, or semicolon and this
    # is removed by the LLM. In this case, we need to remove the punctuation from the
    # text as well.
    # EX:
    # >> text = "And here's the thing: "
    # >> completion = "And here's the thing, I don't remember."
    # >> Desired completion: "I don't remember"
    # Need to strip `text` of puncuation so we recognize it as duplication.
    else:
        if text[-1] in [',', ':', ';']:
            text = text[:-1]
        return completion.split(text)[-1]


def get_context_and_incomplete_sentence(text):
    """
    Extracts context and incomplete sentence from the given text.
    Further adjusted to correctly identify incomplete sentences at the end.
    """
    sentence_terminators = r"[.!?]"

    # Split the text using the sentence terminators and keep the terminators
    sentences = re.split('({})'.format(sentence_terminators), text)
    # Reassemble sentences with their terminators
    sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') for i in range(0, len(sentences), 2)]

    if len(sentences) == 1:
        # Single sentence which could be complete or incomplete
        if text.endswith(tuple(sentence_terminators)):
            return sentences[0].strip(), ''
        else:
            return '', sentences[0].strip()
    else:
        # Multiple sentences
        if text.endswith(tuple(sentence_terminators)):
            # Text ends with a full stop, question mark, or exclamation mark
            context = ' '.join(sentences)
            incomplete_sentence = ""
        else:
            # Text ends with an incomplete sentence
            context = ' '.join(sentences[:-1])
            incomplete_sentence = sentences[-1]

    return context.strip(), incomplete_sentence.strip()

def is_partial_word(sentence):
    """ Check if the sentence ends with a partial word. """
    return not sentence.endswith(' ')

def sanitize_text(text):
    """
    Sanitize the input text before sending to the LLM.
    This includes checking for and handling partial words.
    """
    print("text", text)
    words = text.split()
    if not text.endswith(' '):
        # Remove the last word (potential partial word)
        sanitized =  ' '.join(words[:-1])
        print(sanitized)
    return text

if __name__ == '__main__':
    app.run(debug=True)
