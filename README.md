# Description 
A weird kind of AI-powered autocomplete text editor

# Key Files
- `app.py` is the main file that runs the web app
- `config.yaml` is a configuration file for settings that are global to all sessions. Modify this file to change global behavior.
- `templates/index.html` - the HTML template for the text editor
- `templates/user_and_event.hml` - the HTML template for asking for charter and event inputs

Note: When `hardcode_character_and_event` is true in the YAML file  it will read the default characters and events from the YAML file. When false, display a form for users to input the character and event. 

# Run Locally 

```bash
git clone https://github.com/osh-ashkinaze/autocomplete.git
cd autocomplete
docker build -t myapp .
docker run -e OPENAI_KEY=your_openai_key -p 4000:80 myapp
```
Replace `your_openai_key` with your actual OpenAI API key. Access the application at `http://localhost:4000`.

# ToDo
- Add prompts for user if get stuck in text editor 
- Log actions