# app.py
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
import json

app = Flask(__name__)

with open('secrets.json') as f:
    secrets = json.load(f)
openai_key = secrets['openai_key']

# Set your OpenAI API key

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
            "content": "You will auto-complate a user's sentence to make it highly creative."
          },
          {
            "role": "user",
            "content": prompt
          }
        ],
        temperature=0.7,
        max_tokens=64,
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

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    text = request.json.get('text')
    prompt = "You are an expert writer. You will help finish this sentence and say nothing else." + text
    completion = get_chat_completion(prompt)
    return jsonify(completion=completion)

if __name__ == '__main__':
    app.run(debug=True)
