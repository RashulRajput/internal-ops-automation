# OpsPilot Internal Operations Automation

OpsPilot is a working POC for an AI-powered internal operations system. It handles ticket triage, leave request review, meeting summarization, document Q&A, task extraction, daily reporting, and an operations chat agent.

The demo runs without paid APIs. The AI layer is local and deterministic so the project works immediately on any laptop. The architecture report explains how the same interfaces can later connect to Gemini, OpenAI, Claude, Groq, Ollama, Chroma, Slack, or n8n.

## Run

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
python -m app.main
```

Open:

```text
http://127.0.0.1:8000
```

The server seeds demo data on startup. Press `Seed demo` in the UI if you reset the database.

Manual testing steps are in [manual_test_guide.md](docs/manual_test_guide.md).

## What Works

- Local REST backend with SQLite
- Ticket classification with category, priority, owner, summary, and suggested resolution
- Leave policy analysis with recommendation, flags, and conditions
- Meeting transcript summary with decisions and action-item extraction
- Document indexing and keyword retrieval Q&A
- Task board with meeting-derived tasks
- Daily operations report
- Agent chat for status and risk questions
- Dark dimensional dashboard UI
- n8n workflow JSON examples
- Documentation and tests

## Project Map

```text
internal-ops-automation/
  app/
    brain.py
    main.py
    store.py
  frontend/
    index.html
    styles.css
    app.js
  docs/
    architecture.md
    ai_tools_research.md
    recommendation_report.md
    api_documentation.md
    demo_walkthrough.md
  n8n/workflows/
  scripts/
  tests/
```

## Tests

```powershell
python -m unittest discover tests
```

## Notes

No API key is required. By default the local database is stored under the system temp folder to avoid OneDrive file locks on Windows. `INTERNALOPS_DB` can point the server at another SQLite file. `PORT` changes the local server port.
