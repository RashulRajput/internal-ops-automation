# API Documentation

Base URL:

```text
http://127.0.0.1:8000
```

## Health

`GET /health`

Returns service status.

## Summary

`GET /api/summary`

Returns dashboard data for tickets, leave requests, meetings, documents, tasks, and metrics.

## Tickets

`GET /api/tickets`

Lists tickets.

`POST /api/tickets`

```json
{
  "title": "VPN not working",
  "description": "Cannot connect from home",
  "submitter_name": "Rajesh Kumar",
  "submitter_email": "rajesh@webvory.com"
}
```

`GET /api/tickets/stats/summary`

Returns total, open, resolved, high, and critical counts.

## Leave

`GET /api/leave`

Lists leave requests.

`POST /api/leave`

```json
{
  "employee_name": "Sneha Patel",
  "employee_email": "sneha@webvory.com",
  "department": "Engineering",
  "leave_type": "annual",
  "start_date": "2026-06-15",
  "end_date": "2026-06-20",
  "reason": "Family travel"
}
```

## Meetings

`GET /api/meetings`

Lists analyzed meetings.

`POST /api/meetings`

```json
{
  "title": "Q2 Planning",
  "date": "2026-06-01T10:00:00",
  "duration_minutes": 45,
  "participants": ["Rahul", "Neha"],
  "transcript": "Rahul: Decision made. Neha: I will finish the flow by Friday."
}
```

## Documents

`GET /api/documents`

Lists indexed documents.

`POST /api/documents`

```json
{
  "name": "Leave Policy",
  "category": "hr",
  "content": "Annual leave requires seven days notice."
}
```

`POST /api/documents/query`

```json
{
  "question": "How much notice is needed for annual leave?"
}
```

## Tasks

`GET /api/tasks`

Lists tasks.

`POST /api/tasks`

```json
{
  "title": "Review Slack leave workflow",
  "owner": "Arjun",
  "priority": "high",
  "due_date": "Friday"
}
```

`PATCH /api/tasks/{id}`

Updates title, owner, priority, status, or due date.

## Reports

`GET /api/reports/daily`

Returns metrics and a local AI operations report.

`POST /api/agent/chat`

```json
{
  "message": "What are the current risks?"
}
```
