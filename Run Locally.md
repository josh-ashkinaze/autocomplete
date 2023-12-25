
# How to Run Locally

This document provides instructions on how to build and run the application locally using two different methods: with Docker and without Docker.

## Prerequisites

Ensure you have the following installed:
- Python 3.9 or later
- Docker (for Method 1)
- Git (optional, for cloning the repository)

## Method 1: Using Docker

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

## Method 2: Without Docker

This method requires setting up the Python environment and dependencies manually.

### Step 1: Clone the repository

```bash
git clone https://github.com/josh-ashkinaze/autocomplete
cd autocomplete
```

### Step 2: Create a virtual environment

Create and activate a virtual environment:

- On macOS or Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- On Windows:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

### Step 3: Install dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 4: Set environment variables

Set the `OPENAI_KEY` environment variable:

- On macOS or Linux:
  ```bash
  export OPENAI_KEY="your_openai_key_here"
  ```

- On Windows (using PowerShell):
  ```powershell
  $env:OPENAI_KEY="your_openai_key_here"
  ```

### Step 5: Run the application

Run the application:

```bash
python app.py
```

The application will be accessible at the URL and port specified in `app.py`.

---

**Note**: Replace `your_openai_key_here` with your actual OpenAI API key. 