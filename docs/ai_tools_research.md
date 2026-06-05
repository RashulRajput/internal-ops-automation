# AI Tools Research and Evaluation

## Problem

Internal operations teams spend time manually classifying support tickets, checking leave requests against policy, extracting action items from meetings, answering repeated policy questions, and preparing daily status reports. OpsPilot solves this with a free-first AI automation architecture that can run locally, optionally use free model APIs, and later scale into production.

## Evaluation Summary

| Tool | Capabilities | Pricing | Scalability | Integration | Limitations | Best Use |
|---|---|---|---|---|---|---|
| Ollama | Runs open-source LLMs locally through a REST API | Free, hardware cost only | Good for private single-server deployments | Simple local HTTP endpoint | Needs RAM/CPU/GPU and model download | Offline/private AI inference |
| Gemini Free | Fast general LLM with structured output and long context | Free tier available, paid upgrade later | Strong cloud scalability | REST API, simple key setup | Rate limits and cloud data transfer | Primary free cloud model |
| Groq Free | Very fast hosted open-source model inference | Free tier available, paid upgrade later | Strong for low-latency workloads | OpenAI-style REST API | Rate limits and narrower model choice | Real-time ticket and agent responses |
| Hugging Face Free | Hosted inference and model ecosystem | Free tier available, paid upgrade later | Good for experimentation | REST API | Free endpoints can be slower or rate-limited | Backup provider and model experiments |
| LangChain | LLM application framework and integrations | Open source | Production proven | Many providers, retrievers, tools | Full package can be heavy | LLM abstraction and tool wiring |
| LangGraph | Graph workflow engine for AI agents | Open source | Strong for auditable workflows | Python package, state graph model | Learning curve is higher than simple chains | Multi-step ticket workflow |
| n8n | Visual automation and webhook orchestration | Free self-hosted, paid cloud optional | Scales with workers and queues | 400+ nodes, webhooks, HTTP requests | Needs separate service in production | Business system integration |
| ChromaDB | Local/vector database for RAG | Free open source | Good for prototype and small production | Python package | Not as managed as Pinecone | Free local vector store |
| Weaviate | Open-source vector database with hybrid search | Free self-hosted, paid cloud optional | Strong production path | REST/GraphQL/Docker | More setup than ChromaDB | Larger self-hosted RAG systems |
| Pinecone | Managed vector database | Free starter options can vary, paid for scale | Excellent managed scaling | REST/SDK | External service and paid growth path | Enterprise RAG with low ops overhead |

## Detailed Comparison

### Ollama

Ollama is the best fit for the "no paid API" requirement because it runs models locally. It keeps sensitive operations data on the machine and exposes a local REST API compatible with simple HTTP calls. Its limitation is hardware: small models run on most laptops, but larger models need more memory and can be slow on CPU.

### Gemini Free

Gemini is a strong free cloud option for structured classification, summarization, and document Q&A. It is easy to integrate and has a clear upgrade path. The free tier is useful for demos and light workloads, but rate limits mean the system should not depend on it alone.

### Groq Free

Groq is valuable for speed. Its hosted open-source models can answer quickly, which helps in chat-style UX and ticket triage. The downside is that the free tier can be throttled and model availability can change, so it works best as part of a provider cascade.

### Hugging Face Free

Hugging Face gives access to many open-source models and is useful for experimentation. It is less predictable for latency than Groq or Gemini on free plans, but it is still useful as a fallback and research platform.

### LangChain and LangGraph

LangChain provides the standard vocabulary for LLM apps: prompts, models, parsers, tools, and retrievers. OpsPilot uses a minimal approach and keeps the provider layer simple. LangGraph is selected for the workflow engine because it models real operations work as steps: classify, assess risk, route, resolve, and record an audit trail.

### n8n

n8n is selected as the automation layer because it is free when self-hosted and can connect OpsPilot to Slack, email, Jira, Google Sheets, Notion, Shopify, CRMs, or webhooks later. The prototype includes importable n8n workflows so evaluators can see the integration pattern without needing paid accounts.

### Vector Databases

OpsPilot ships with a local TF-IDF retriever so document Q&A works immediately. It also includes an optional ChromaDB path for free local vector storage. Weaviate is the recommended self-hosted production vector database when the document corpus grows. Pinecone is a managed option if the team later accepts paid infrastructure.

## Selected Stack

| Layer | Selected Tool | Reason |
|---|---|---|
| UI | Vanilla HTML/CSS/JS | No build step, fast deployment, clean demo |
| Backend | Python HTTP server | Simple, portable, no framework lock-in |
| Workflow | LangGraph with fallback | Auditable multi-step AI workflow |
| Automation | n8n | Free visual workflow layer |
| Local AI | Ollama | Private and free inference |
| Free cloud AI | Gemini, Groq, Hugging Face | Optional quality/speed boost |
| RAG | TF-IDF now, ChromaDB optional | Works without keys, upgrades cleanly |
| Database | SQLite | Zero setup for POC |
| Deployment | Docker, Render, Railway | Free or low-cost path to public demo |

## Why This Is Practical

The architecture does not collapse when a free API is unavailable. It attempts configured providers, can use Ollama locally, and then falls back to deterministic local logic. This means the demo works today with zero keys, while the same code can become more intelligent when free keys or local models are added.
