# Medical Transcript Summarizer

A simple service for doctors to summarize and translate medical transcripts.

## Features

- Paste text into a text field
- Summarize text into a single paragraph
- Choose language for summary (English or Finnish)
- Summary persists on page refresh until new text is summarized

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Create a .env file and set your Google (Gemini) API key:
```
GOOGLE_API_KEY=your-api-key-here
```
Alternatively, you can use environment variables.

3. Run the server:
```bash
uv run --env-file .env main.py
```

4. Open your browser to `http://localhost:8888`

5. Run tests:
```bash
uv run pytest
```