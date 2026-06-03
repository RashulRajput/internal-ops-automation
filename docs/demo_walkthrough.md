# Demo Walkthrough

## Opening

Start the server and open the dashboard.

```powershell
python -m app.main
```

```text
http://127.0.0.1:8000
```

## Suggested Flow

1. Show the dashboard metrics and 3D automation model.
2. Open Tickets and submit a VPN or payroll issue.
3. Explain how category, priority, owner, summary, and resolution are generated locally.
4. Open Leave and submit annual leave with less than seven days notice to show a review flag.
5. Open Meetings and paste a short transcript with decisions and "I will" action items.
6. Open Docs Q&A, index the leave policy, and ask a policy question.
7. Open Tasks to show meeting-derived action items.
8. Open Reports and generate the daily operations summary.
9. Ask the Ops Agent: "What are the current risks?"

## Demo Script

This is an internal operations automation POC. It does not need paid APIs, so the evaluator can run it immediately. The prototype demonstrates how AI can triage tickets, review leave requests against policy, summarize meetings, extract tasks, retrieve answers from company documents, and generate an operations report from the same data model.

The current build uses local deterministic reasoning. In production, the same API can call Gemini, Ollama, Groq, OpenAI, or Claude through a provider adapter. Human approval stays in the loop for HR, payroll, and high-risk decisions.
