# SQL Agentic Chat

An agent that can generate SQL Queries to interact with structured data in your database.

A ChatGPT-like web interface for interacting with an AI agent that can:
- Analyze the Titanic dataset
- Analyze Financial Trasnaction Data
- Get human input when needed

![SQL Agentic Chat Interface](Screenshot%202025-08-02%20at%203.33.07%20PM.png)

## Setup

### Option 1: Automated Setup (Recommended)

Run the setup script to automatically configure everything:

```bash
./setup.sh
```

This script will:
- Create and activate the conda environment
- Prompt for your Gemini API key
- Download the Titanic dataset (if not already present)
- Start the Flask web server

### Option 2: Manual Setup

1. Setup Conda ENV:
```
conda env create -f setup/environment.yml
```

2. Set your Gemini API key as an environment variable:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

3. Make sure you have the Titanic database:
```bash
python download_titanic.py
```

4. Start the Flask web server:
```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000`

## Example Queries

- "What's the weather in Berlin today?"
- "How many people survived the Titanic?"
- "What percentage of Titanic passengers were female?"
- "What age group of men had the best survival rate on the Titanic?"
- "How many buildings are there in San Francisco?"

## Architecture

- **Frontend**: HTML/CSS/JavaScript with a modern chat interface
- **Backend**: Flask web server
- **Agent**: LangGraph-based agent with multiple tools
- **Database**: SQLite database with Titanic dataset or BYO CSV Dataset