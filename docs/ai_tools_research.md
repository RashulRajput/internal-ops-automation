# AI Tools Research and Evaluation

Date: June 3, 2026  
Use case: Internal Operations Automation

## Shortlist

| Tool | Capabilities | Pricing stance | Scalability | Integration | Limits | Best use |
| --- | --- | --- | --- | --- | --- | --- |
| Gemini API | Text, multimodal input, function calling, long context, free tier, paid production tier | Google lists a free tier and paid tier. Gemini 3.1 Flash-Lite is shown at $0.25 input and $1.50 output per 1M tokens on the standard paid tier. | Strong for production on Google infrastructure | Simple REST/SDK, good for cost-sensitive prototypes | Free tier data may be used to improve products; quotas change | Best free hosted option for a student/demo POC |
| Ollama | Runs open models locally, offline | Local usage is free except hardware. Ollama also lists cloud options with Pro and Max plans. | Scales vertically on local GPU, then via hosted Ollama/cloud | Easy local HTTP API | Quality depends on chosen model and hardware | Best privacy-first path for HR and internal docs |
| Groq | Very fast inference for open models | Groq publishes low per-token prices and links to a free API key. Llama 3.1 8B Instant is listed at $0.05 input and $0.08 output per 1M tokens. | High throughput for realtime workflows | OpenAI-style APIs, easy swap-in | Model choice smaller than frontier vendors | Best hosted low-cost speed layer |
| OpenAI | Strong frontier and mini models, structured outputs, tool ecosystem | OpenAI lists GPT-5.4 mini at $0.75 input and $4.50 output per 1M tokens; Batch API can save 50%. | Excellent production reliability | Mature SDKs and examples | Paid usage, sensitive-data review needed | Best quality upgrade for critical workflows |
| Claude | Strong long-form reasoning and report quality | Anthropic lists Claude Sonnet 4.6 at $3 input and $15 output per 1M tokens. | Strong hosted API | Good SDK and enterprise routes | Paid API; cost can rise on long contexts | Best for policy reasoning and executive reports |
| Chroma | Open-source retrieval database with metadata, dense, sparse, and hybrid search | Local/self-hosted is open source; managed Chroma Cloud is optional | Good for internal document Q&A | Python SDK, embedding-provider flexible | Requires embedding strategy and indexing pipeline | Best vector/RAG layer |
| n8n | Workflow automation and integrations | Self-hostable; cloud optional | Good for scheduled and event workflows | Webhooks and hundreds of connectors | Complex workflows need governance | Best orchestration layer |

## Recommendation

The submitted POC uses local logic so the evaluator can run it without paying for APIs. For a real deployment, the practical stack is:

- Gemini free tier or Ollama for the first live LLM upgrade.
- Groq for low-cost realtime triage.
- Chroma for RAG once document volume grows.
- n8n for workflow orchestration.
- OpenAI or Claude only for high-value tasks that need stronger reasoning.

## Source Notes

- OpenAI pricing page, accessed June 3, 2026: https://openai.com/api/pricing/
- Anthropic Claude pricing page, accessed June 3, 2026: https://platform.claude.com/docs/en/about-claude/pricing
- Google Gemini pricing page, accessed June 3, 2026: https://ai.google.dev/gemini-api/docs/pricing
- Groq pricing page, accessed June 3, 2026: https://groq.com/pricing
- Ollama homepage, accessed June 3, 2026: https://ollama.com/
- Chroma introduction, accessed June 3, 2026: https://docs.trychroma.com/docs/overview/introduction
