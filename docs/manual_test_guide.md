# Manual Test Guide

No paid API key is required.

The app works in three levels:

```text
Best online quality: Gemini/Groq/Hugging Face free API keys
Best local privacy: Ollama running on your laptop
Guaranteed fallback: built-in local logic
```

## Start Locally

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
python -m app.main
```

Open:

```text
http://127.0.0.1:8000
```

After updates, press:

```text
Ctrl + F5
```

## Optional Full Stack With n8n And Ollama

Docker mode starts OpsPilot, n8n, and Ollama:

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
docker compose up --build
```

Open:

```text
OpsPilot: http://127.0.0.1:8000
n8n: http://127.0.0.1:5678
```

n8n login from `.env.example`:

```text
User: admin
Password: opspilot-demo
```

Pull a local Ollama model:

```powershell
docker exec -it internal-ops-automation-ollama-1 ollama pull llama3.2:3b
```

## Test 1: AI Stack

Open `AI Stack`.

Expected:

```text
It shows Gemini Free, Groq Free, Hugging Face Free, Ollama Local, or Local fallback status.
```

If no keys and no Ollama model exist, `Local fallback` is fine.

## Test 2: Ticket Workflow

Open `Tickets`.

Use:

```text
Title: VPN not working for remote team
Submitter: Rajesh Kumar
Email: rajesh@webvory.com
Description: The team cannot connect to VPN since morning and staging access is blocked.
```

Expected:

```text
Ticket appears with it_support, high or critical priority, owner, summary, and estimated hours.
```

Behind the scenes, the workflow runs classify, risk, route, and resolve steps.

## Test 3: Leave Review

Open `Leave`.

Use:

```text
Employee: Sneha Patel
Email: sneha@webvory.com
Department: Engineering
Leave type: Annual
Start date: 2026-06-15
End date: 2026-06-20
Reason: Family travel planned in advance.
```

Expected:

```text
Leave request appears with approved or review recommendation and reasoning.
```

## Test 4: Meeting Summary

Open `Meetings`.

Use:

```text
Title: Q2 Ops Planning
Participants: Rahul, Neha, Arjun, Priyanka
Transcript:
Rahul: Decision made, Slack leave requests are P1 for June.
Neha: I will finish the flows by Friday.
Arjun: Engineering needs API contracts by Monday.
Priyanka: I will confirm the policy wording with HR today.
```

Expected:

```text
Meeting appears with summary, decisions, action count, and sentiment. Tasks are created from action items.
```

## Test 5: RAG Document Q&A

Open `Docs Q&A`.

Index:

```text
Document name: Leave Policy
Category: HR
Paste document text:
Annual leave should be requested seven days in advance. Sick leave can be submitted the same day. Leave longer than ten days needs manager approval and backup ownership.
```

Ask:

```text
How much notice is needed for annual leave?
```

Expected:

```text
It answers that annual leave should be requested seven days in advance and shows a source.
```

## Test 6: Ops Agent

Ask:

```text
What are the current risks?
```

Expected:

```text
It summarizes critical tickets and pending leave approvals.
```

Ask:

```text
meetings today
```

Expected:

```text
It tells you how many meeting action items exist.
```

## Test 7: Reports

Open `Reports`.

Click:

```text
Generate daily report
```

Expected:

```text
A daily operations report appears with metrics and risks.
```
