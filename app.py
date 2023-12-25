from flask import Flask, request, render_template, jsonify
from openai import OpenAI
import json
import string

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
            "content": "Given a sentence, you will auto-complete a user's sentence to make it in the style of a New Jersey italian. Be very Italian. Make sure the sentence fits with what the user wrote before. "
                       "Return the rest of the sentence with a period at the end."

          },
          {
            "role": "user",
            "content": prompt
          }
        ],
        temperature=0.8,
        max_tokens=20,
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
