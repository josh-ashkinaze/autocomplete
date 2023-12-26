# Description 
This is a simple web app that uses OpenAI to autocomplate text for given 'character', as if that character experienced a 
certain situation.

# File Structure
- `app.py` is the main file that runs the web app
- `config.py`is the configuration file for the web app
- `forms.py` is the Flask-WTF file for forms (e.g: character/event input, pre-test questions)
- `config.yaml` is a configuration file for settings that are global to all sessions, whereas Flask session object store user-specific settings 
- `templates/index.html` - the HTML template for the web app
- `templates/char_and_event.hml` - the HTML template for asking for charter and event inputs

Note: When `hardcode_character_and_event` is false it defaults to asking users for character and event inputs. Otherwise it reads this from the YAML file (e.g: for testing). 

# Run Locally 

### Step 1: Clone the repository

```bash
git clone https://github.com/josh-ashkinaze/autocomplete
cd autocomplete
```

### Step 2: Input your OpenAI API Key

- On macOS or Linux:
  ```bash
  export OPENAI_KEY="your_openai_key_here"
  ```

- On Windows (using PowerShell):
  ```powershell
  $env:OPENAI_KEY="your_openai_key_here"
  ```

### Step 3: Build docker image

```bash
docker build -t my-python-app .
```

### Step 4: Run Docker container

```bash
docker run -p 4000:80 -e OPENAI_KEY="${OPENAI_KEY}" my-python-app
```

The application will be accessible at `http://localhost:4000`.

