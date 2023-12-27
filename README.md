# Description 
Fill here

# File Structure
- `app.py` is the main file that runs the web app
- `config.py`is the configuration file for the web app
- `forms.py` is the Flask-WTF file for forms (e.g: character/event input, pre-test questions)
- `config.yaml` is a configuration file for settings that are global to all sessions. Modify this file to change behavior.
- `templates/index.html` - the HTML template for the web app
- `templates/user_and_event.hml` - the HTML template for asking for charter and event inputs

Note: When `hardcode_character_and_event` is false in the YAML file it defaults to asking users for character and event inputs. Otherwise it reads this from the YAML file (e.g: for testing). 

# Run Locally 

### Clone repo

```bash
git clone https://github.com/osh-ashkinaze/autocomplete.git
cd auto
```

### Build docker image

Build the Docker image from the Dockerfile:

```bash
docker build -t myapp .
```

This command builds the Docker image and tags it as `myapp`. You can replace `myapp` with a name of your choice.

### Run docker container

```bash
docker run -e OPENAI_KEY=your_openai_key -p 4000:80 myapp
```

Replace `your_openai_key` with your actual OpenAI API key. This command runs the container, sets the `OPENAI_KEY` environment variable inside it, and maps port 80 of the container to port 4000 on your host machine. Access the application at `http://localhost:4000`.

.