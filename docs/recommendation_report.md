# Recommendation Report

## Recommended Architecture

Use a modular internal operations platform:

- Web dashboard for operations users.
- REST API for ticket, leave, meeting, document, task, and report workflows.
- SQLite for the POC, PostgreSQL for production.
- Local deterministic AI for demo reliability.
- Optional provider adapters for Gemini, Ollama, Groq, OpenAI, or Claude.
- Chroma for document retrieval when the document set grows.
- n8n for scheduled reports and notifications.

## Why These Tools

The prototype intentionally avoids paid APIs. That makes it easy to review, record, and demonstrate. The code keeps the AI functions isolated in `app/brain.py`, so an LLM adapter can be added later without rewriting the API or UI.

Gemini and Ollama are the first upgrade choices because they keep cost low. Groq is a good second choice for fast hosted inference. OpenAI and Claude are best reserved for workflows where accuracy is worth the additional cost, such as policy interpretation, executive summaries, and complex multi-step agent tasks.

## Estimated Infrastructure Cost

POC cost: zero, apart from the developer laptop.

Small production estimate:

- App server: low-cost VPS or internal VM.
- Database: managed PostgreSQL or existing company database.
- LLM: start with Gemini free tier, Ollama local, or Groq low-cost model.
- Vector DB: self-hosted Chroma at first.
- Workflow automation: self-hosted n8n.

Expected early monthly cost can stay near zero to low double digits if local inference or free tiers are used. Paid frontier models should be budget-capped.

## Risks

- Rule-based AI is reliable but less flexible than a real LLM.
- Free API tiers can change limits and data-retention terms.
- HR, payroll, and policy data need strong access control.
- AI recommendations must not auto-reject employee requests without human review.
- Document retrieval quality depends on chunking and source freshness.

## Scaling Plan

1. Replace SQLite with PostgreSQL.
2. Add authentication and role-based access.
3. Move reasoning functions behind provider interfaces.
4. Add Chroma for document embeddings and metadata filters.
5. Add n8n webhooks for Slack and email.
6. Add audit logs for every AI recommendation.
7. Add background jobs for daily reports and SLA reminders.
8. Add evaluation datasets for tickets, leave, summaries, and Q&A.

## Business Impact

OpsPilot reduces repeated triage work, shortens response time, gives HR and admin teams a single queue, and turns meetings and documents into searchable operational knowledge. The strongest demo value is that multiple internal workflows share one automation layer instead of living as separate scripts.
