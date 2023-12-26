
# How to Run Locally

This document provides instructions on how to build and run the application with docker. 


This method uses Docker to build and run the application, which simplifies the setup process and ensures consistency across different environments.

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


---

**Note**: Replace `your_openai_key_here` with your actual OpenAI API key. 