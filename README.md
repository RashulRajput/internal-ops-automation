# OpsPilot Internal Operations Automation

OpsPilot is a complete AI operations automation POC for internal teams. It demonstrates ticket triage, leave review, meeting summarization, task extraction, document Q&A with RAG, daily reporting, workflow audit trails, n8n automation exports, and a polished dashboard UI.

It runs without paid AI APIs. By default it uses local deterministic fallback logic, so the app works immediately. Optional free keys can enable Gemini, Groq, or Hugging Face. Ollama can run fully local models. n8n and Ollama are included in Docker Compose for the full architecture.

## Project Location

```text
C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation
```

## Quick Run

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
python -m app.main
```

Open:

```text
http://127.0.0.1:8000
```

No API key is required for the demo.

## Full Stack Run

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
docker compose up --build
```

Services:

```text
OpsPilot: http://127.0.0.1:8000
n8n:      http://127.0.0.1:5678
Ollama:   http://127.0.0.1:11434
```

Default n8n credentials are in `.env.example`.

To use a local Ollama model:

```powershell
ollama pull llama3.2:3b
```

## Optional Free AI Keys

Copy `.env.example` to `.env` and fill any free keys you have:

```text
GEMINI_API_KEY=
GROQ_API_KEY=
HUGGINGFACE_API_KEY=
AI_PROVIDER_MODE=free-first
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:3b
```

Modes:

```text
free-first   Free cloud keys first, Ollama second, local fallback last
ollama-first Ollama first, free cloud keys second, local fallback last
ollama-only  Only Ollama, then local fallback
```

## Deliverables

```text
docs/ai_tools_research.md       Research and evaluation
docs/recommendation_report.md   Architecture and production recommendation
docs/architecture.md            System diagrams and deployment thinking
docs/manual_test_guide.md       Exact manual testing steps
docs/demo_walkthrough.md        Demo video/walkthrough script
docs/api_documentation.md       REST API reference
n8n/workflows/                  Importable workflow templates
```

## Tests

```powershell
python -m unittest discover tests
node --check frontend\app.js
```

## Deployment

Render and Railway configs are included:

```text
render.yaml
railway.json
Dockerfile
docker-compose.yml
```

For a free online demo, deploy the repository to Render using `render.yaml`. It will run with local fallback even without keys. Add free API keys later as environment variables.
