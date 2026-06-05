# OpsPilot Architecture

OpsPilot is an internal operations automation platform for ticket triage, leave review, meeting summarization, document Q&A, task extraction, daily reporting, and operations chat.

The design is free-first. It can use free cloud AI APIs when keys are available, local Ollama when installed, and deterministic fallback logic when nothing else is configured.

```mermaid
flowchart LR
    UI["Dashboard"] --> API["Python REST API"]
    API --> Store["SQLite data store"]
    API --> Agent["Ops agent"]
    API --> WF["LangGraph workflow layer"]
    API --> RAG["RAG retrieval layer"]
    WF --> Providers["AI provider cascade"]
    Providers --> Gemini["Gemini Free API"]
    Providers --> Groq["Groq Free API"]
    Providers --> HF["Hugging Face Free API"]
    Providers --> Ollama["Ollama local model"]
    Providers --> Local["Local deterministic fallback"]
    RAG --> Chroma["ChromaDB optional local vector DB"]
    RAG --> TFIDF["TF-IDF fallback"]
    N8N["n8n Cloud workflows"] --> API
```

## Runtime Components

| Component | Technology | Role |
|---|---|---|
| Dashboard | HTML, CSS, JavaScript | User-facing operations console |
| API | Python stdlib HTTP server | Serves frontend and REST endpoints with zero hard dependency on paid services |
| Workflow engine | LangGraph when installed, sequential fallback otherwise | Multi-step ticket processing: classify, assess risk, route, resolve |
| LLM layer | Gemini Free, Groq Free, Hugging Face Free, Ollama | Free-first AI reasoning |
| RAG layer | Local TF-IDF today, ChromaDB optional | Search policy and operations documents |
| Automation | n8n Cloud | Webhooks, scheduled reports, no-code workflow proof |
| Storage | SQLite (Persistent Disk) | Tickets, leave requests, meetings, documents, tasks, workflow runs |

## Provider Cascade

```mermaid
sequenceDiagram
    participant App as OpsPilot
    participant Gemini as Gemini Free
    participant Groq as Groq Free
    participant HF as Hugging Face
    participant Ollama as Ollama Local
    participant Local as Local Fallback

    App->>Gemini: Try if GEMINI_API_KEY exists
    alt Gemini works
        Gemini-->>App: Structured AI output
    else Missing key or failure
        App->>Groq: Try if GROQ_API_KEY exists
        alt Groq works
            Groq-->>App: Structured AI output
        else Missing key or failure
            App->>HF: Try if HUGGINGFACE_API_KEY exists
            alt HF works
                HF-->>App: AI output
            else Missing key or failure
                App->>Ollama: Try local model
                alt Ollama running
                    Ollama-->>App: Local model output
                else Not installed or unavailable
                    App->>Local: Run deterministic fallback
                    Local-->>App: Guaranteed output
                end
            end
        end
    end
```

## Workflow Flow

```mermaid
flowchart TD
    A["Ticket submitted"] --> B["Classify category and priority"]
    B --> C["Assess operational risk"]
    C --> D["Route to team"]
    D --> E["Suggest resolution"]
    E --> F["Create ticket record"]
    F --> G["Save workflow audit trail"]
```

## RAG Flow

```mermaid
flowchart TD
    A["Upload or paste document"] --> B["Clean and chunk text"]
    B --> C["Index chunks"]
    C --> D["User asks question"]
    D --> E["Retrieve relevant chunks"]
    E --> F["Generate answer with sources"]
```

## n8n Cloud Flow

![n8n Cloud Workflows](images/n8n_workflows.png)

```mermaid
flowchart LR
    W["Webhook or schedule"] --> N["n8n Cloud workflow"]
    N --> API["OpsPilot Cloud API (Render)"]
    API --> DB["SQLite"]
    API --> AI["AI workflow"]
    AI --> R["Response or report"]
```

## Deployment Modes

| Mode | Cost | AI behavior | Best for |
|---|---:|---|---|
| Local no-key | $0 | Local fallback, optional Ollama | Guaranteed evaluator demo |
| Local full AI | $0 | Ollama + n8n + workflow engine | Strongest assignment walkthrough |
| Online free demo | $0 | Free APIs if configured, fallback if not | Manager/public link |
| Online production | Low paid infra | Free APIs or paid upgrade, hosted database | Team use |

## Production Notes

- Use Render or Hugging Face Spaces for a public demo URL.
- Use free Gemini/Groq keys for online AI quality without paid billing.
- Use Ollama for local/private AI because most free hosts cannot run LLMs reliably.
- Add authentication before using real HR or payroll data.
- Move from SQLite to PostgreSQL once multiple real users write concurrently.
