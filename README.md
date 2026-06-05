# OpsPilot: Internal Operations Automation

OpsPilot is a comprehensive operations automation platform designed to streamline internal team workflows. It features an AI-powered dashboard that handles ticket triage, leave request reviews, meeting summarization, intelligent task extraction, document Q&A (RAG), and daily reporting.

The system is built to run entirely locally using fallback logic or Ollama, but it truly shines when integrated with cloud AI providers (like Google Gemini) and workflow automation engines (like n8n).

## Features

- **AI Operations Dashboard**: A sleek, unified interface to manage tasks, tickets, and leave requests.
- **Smart Ticket Triage**: Automatically categorizes, prioritizes, and routes incoming IT/Ops tickets.
- **Meeting Summarization**: Extracts actionable tasks and key decisions from raw meeting transcripts.
- **Document Q&A**: A Retrieval-Augmented Generation (RAG) system for querying internal policies.
- **Workflow Automation**: Deeply integrates with n8n to automate repetitive background tasks.
- **Multi-Model Support**: Works with Google Gemini, Groq, Hugging Face, or locally via Ollama.

## Quick Start (Local Development)

To run the application locally for development:

```bash
pip install -r requirements.txt
python -m app.main
```

Once running, navigate to `http://127.0.0.1:8000` in your browser.

## Full Stack Docker Environment

To run the complete stack (OpsPilot, n8n, and Ollama) locally using Docker:

```bash
docker compose up --build
```

- **OpsPilot Dashboard**: `http://127.0.0.1:8000`
- **n8n Automation**: `http://127.0.0.1:5678` (Credentials in `.env.example`)
- **Ollama Engine**: `http://127.0.0.1:11434`

## Configuration

Copy `.env.example` to `.env` and configure your API keys. The application uses a cascading provider system.

```text
GEMINI_API_KEY=your_key_here
AI_PROVIDER_MODE=free-first
```

## Cloud Deployment (Render + n8n Cloud)

OpsPilot is configured for easy 1-click deployment to **Render.com** and seamless integration with **n8n Cloud**.

1. **Deploy the Backend:**
   Use the included `render.yaml` as a Blueprint on Render.com to deploy the application for free. Make sure to add your `GEMINI_API_KEY` to the Render environment variables during setup.

2. **Connect Automations:**
   The `n8n/workflows/` directory contains 5 ready-to-use automation templates. Import these JSON files into your n8n Cloud account, update the HTTP Request URLs to point to your new Render deployment, and set them to "Active" to enable background automations.

## Testing

Run the test suite to ensure everything is functioning correctly:

```bash
python -m unittest discover tests
node --check frontend/app.js
```
