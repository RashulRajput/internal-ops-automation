# API Documentation

Base URL:

```text
http://127.0.0.1:8000
```

## Health and AI Stack

`GET /health`

Returns service health, active AI provider, and whether the app is using AI or fallback mode.

`GET /api/ai/status`

Returns configured providers, active provider, provider mode, and vector store status.

`POST /api/ai/benchmark`

```json
{
  "prompt": "Say hello from OpsPilot in one sentence."
}
```

Runs a small test prompt through available providers and returns latency/result status.

## Dashboard

`GET /api/summary`

Returns all dashboard data: ticket metrics, tickets, leave requests, meetings, documents, tasks, active provider, and workflow stats.

## Tickets

`GET /api/tickets`

Lists tickets.

`POST /api/tickets`

```json
{
  "title": "Payroll portal is not opening",
  "description": "The finance team cannot open payroll before today's salary cutoff.",
  "submitter_name": "Anika Rao",
  "submitter_email": "anika@example.com"
}
```

Creates a ticket and runs the LangGraph workflow: classify, assess risk, route, and suggest resolution.

`GET /api/tickets/stats/summary`

Returns ticket counts by status and priority.

`PATCH /api/tickets/{id}`

Updates ticket fields such as status, assigned owner, or priority.

## Workflow Runs

`GET /api/workflows/runs`

Lists recent workflow audit entries.

`POST /api/workflows/ticket`

```json
{
  "title": "VPN outage",
  "description": "Remote employees cannot connect to VPN and client delivery is blocked."
}
```

Runs only the ticket workflow and returns the full step audit.

## Leave

`GET /api/leave`

Lists leave requests.

`POST /api/leave`

```json
{
  "employee_name": "Sneha Patel",
  "employee_email": "sneha@example.com",
  "department": "Engineering",
  "leave_type": "annual",
  "start_date": "2026-06-09",
  "end_date": "2026-06-12",
  "reason": "Family travel"
}
```

Analyzes the request against policy and returns recommendation, risk flags, conditions, and total days.

## Meetings

`GET /api/meetings`

Lists analyzed meetings.

`POST /api/meetings`

```json
{
  "title": "Operations planning",
  "date": "2026-06-05T10:00:00",
  "duration_minutes": 35,
  "participants": ["Rahul", "Neha", "Amit"],
  "transcript": "Rahul: We decided to launch the support workflow today. Neha: I will validate the leave flow by Friday. Amit: I will connect n8n webhook tomorrow."
}
```

Returns summary, decisions, sentiment, and action items. Action items are stored as tasks.

## Documents and RAG

`GET /api/documents`

Lists indexed documents.

`POST /api/documents`

```json
{
  "name": "Leave Policy",
  "category": "hr",
  "content": "Annual leave requires seven days notice. Leave longer than ten days requires manager approval. Sick leave over two days requires a medical note."
}
```

Chunks and indexes a document for retrieval.

`POST /api/documents/query`

```json
{
  "question": "When does annual leave need manager review?"
}
```

Retrieves relevant chunks and returns a source-backed answer.

## Tasks

`GET /api/tasks`

Lists tasks.

`POST /api/tasks`

```json
{
  "title": "Connect n8n webhook",
  "owner": "Amit",
  "priority": "high",
  "due_date": "tomorrow"
}
```

`PATCH /api/tasks/{id}`

Updates status, owner, title, priority, or due date.

## Reports and Agent

`GET /api/reports/daily`

Generates a daily operations report from tickets, leaves, meetings, and tasks.

`POST /api/agent/chat`

```json
{
  "message": "What are the current risks?"
}
```

Returns a concise operations assistant response using current data and optional RAG context.

## Audit

`GET /api/audit`

Returns stored audit information for workflow and operational events.
