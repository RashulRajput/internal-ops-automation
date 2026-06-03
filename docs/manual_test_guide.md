# Manual Test Guide

This project does not need OpenAI, Gemini, Claude, or any paid API key.

It uses a local API server on your laptop:

```text
http://127.0.0.1:8000
```

The browser talks to that local API through routes like:

```text
/api/tickets
/api/leave
/api/meetings
/api/documents/query
/api/agent/chat
```

## Start The Project

Open PowerShell:

```powershell
cd "C:\Users\DELL\OneDrive\Documents\New project\internal-ops-automation"
python -m app.main
```

Keep that PowerShell window open.

Open this in Chrome:

```text
http://127.0.0.1:8000
```

If buttons still feel stuck, press:

```text
Ctrl + F5
```

That forces Chrome to load the newest JavaScript.

## Test 1: Ticket Automation

Open `Tickets`.

Fill:

```text
Title: VPN not working for remote team
Submitter: Rajesh Kumar
Email: rajesh@webvory.com
Description: The team cannot connect to VPN since morning and staging access is blocked.
```

Click:

```text
Classify ticket
```

Expected result:

```text
New ticket appears with it_support, high or critical priority, assigned owner, summary, and estimated hours.
```

## Test 2: Leave Automation

Open `Leave`.

Fill:

```text
Employee: Sneha Patel
Email: sneha@webvory.com
Department: Engineering
Leave type: Annual
Start date: 2026-06-15
End date: 2026-06-20
Reason: Family travel planned in advance.
```

Click:

```text
Analyze request
```

Expected result:

```text
Leave request appears with approved or review recommendation and a reason.
```

## Test 3: Meeting Automation

Open `Meetings`.

Fill:

```text
Title: Q2 Ops Planning
Participants: Rahul, Neha, Arjun, Priyanka
Transcript:
Rahul: Decision made, Slack leave requests are P1 for June.
Neha: I will finish the flows by Friday.
Arjun: Engineering needs API contracts by Monday.
Priyanka: I will confirm the policy wording with HR today.
```

Click:

```text
Extract summary
```

Expected result:

```text
Meeting appears with summary, decisions, action count, and sentiment.
```

## Test 4: Document Q&A

Open `Docs Q&A`.

Index this document:

```text
Document name: Leave Policy
Category: HR
Paste document text:
Annual leave should be requested seven days in advance. Sick leave can be submitted the same day. Leave longer than ten days needs manager approval and backup ownership.
```

Click:

```text
Index document
```

Ask:

```text
How much notice is needed for annual leave?
```

Click:

```text
Ask documents
```

Expected result:

```text
It answers that annual leave should be requested seven days in advance.
```

## Test 5: Ops Agent

In the right-side Ops Agent box, type:

```text
What are the current risks?
```

Expected result:

```text
It summarizes critical tickets and pending leave approvals.
```

Try:

```text
meetings today
```

Expected result:

```text
It tells you how many extracted meeting action items exist.
```

## Test 6: Reports

Open `Reports`.

Click:

```text
Generate daily report
```

Expected result:

```text
A daily operations report appears with current metrics and risks.
```

## Important

No API keys are required for this version.

The word API here means the local backend server. It is not calling paid AI services.

The AI behavior is local rule-based logic in:

```text
app/brain.py
```

Paid/free AI providers can be added later, but this submitted POC is designed to run without them.
