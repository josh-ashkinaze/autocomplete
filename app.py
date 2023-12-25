from flask import Flask, request, render_template, jsonify
from openai import OpenAI
import json
import string
import random

app = Flask(__name__)

# Load OpenAI API key
with open('secrets.json') as f:
    secrets = json.load(f)
openai_key = secrets['openai_key']

def get_chat_completion(prompt, model="gpt-3.5-turbo", attempt_no=0, max_attempts=2):
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
              "content": "Your task is to project and complete the user's description of a day in their life into a scenario set in a world affected by unchecked climate change. "
                         "Draw on realistic consequences of environmental changes, such as extreme weather, resource scarcity, and ecological impacts. "
                         "Adapt the user's narrative to reflect these changes, maintaining the essence of their original story but altering the setting and events to align with the effects of climate change. "
                         "Ensure that the completion is coherent with the user's text and provides a vivid, believable depiction of life in this altered world. "
                         "Write in the first person, from the user's perspective. "
                         "Do not repeat yourself ever."

          },
          {
            "role": "user",
            "content": prompt
          }
        ],
        temperature=random.uniform(0.1, 0.4),
        max_tokens=random.randint(5, 15),
        top_p=1
      )
      answer = json.loads(response.choices[0].json())['message']['content']
      return answer
    except Exception as e:
      print(e)
      return get_chat_completion(prompt, attempt_no=attempt_no+1)

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
    completion = get_chat_completion(sanitized_text)
    full_word_completion = extract_complete_words(completion)
    print("TEXT:", text)
    print("COMPLETION:", completion)
    print("FULL WORD COMPLETION:", full_word_completion)
    return jsonify(completion=full_word_completion)


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
