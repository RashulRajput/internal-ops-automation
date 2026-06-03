"""
brain.py — AI reasoning layer for OpsPilot.

Each public function tries LLM providers first (Gemini → Groq → Mistral).
If all LLM calls fail, it falls back to the local rule-based implementation.
This guarantees the app never breaks even when all API keys expire.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import date, datetime

from app.providers import llm_call, llm_json


# ---------------------------------------------------------------------------
# Shared constants (used by local fallback logic)
# ---------------------------------------------------------------------------
STOP = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with",
    "is", "are", "i", "we", "you", "it", "this", "that", "my", "our", "from",
    "as", "at", "by", "be", "can", "need", "please"
}

CATEGORIES = {
    "it_support": ["vpn", "laptop", "password", "software", "login", "email", "server", "network", "device", "access", "bug", "crash"],
    "hr": ["leave", "salary", "payroll", "policy", "benefit", "joining", "offer", "employee", "attendance", "reimbursement"],
    "facilities": ["ac", "chair", "desk", "office", "room", "light", "clean", "parking", "conference", "water", "electric"],
    "finance": ["invoice", "payment", "expense", "budget", "vendor", "bill", "tax", "purchase", "approval"],
    "general": ["question", "request", "help", "support", "update", "info"]
}

TEAMS = {
    "it_support": "IT Helpdesk",
    "hr": "People Ops",
    "facilities": "Admin Desk",
    "finance": "Finance Ops",
    "general": "Operations Coordinator"
}

CRITICAL = ["down", "blocked", "security", "breach", "payroll", "production", "urgent", "outage", "cannot work"]
HIGH = ["not working", "failed", "stuck", "deadline", "client", "today", "salary", "access"]
LOW = ["question", "minor", "when possible", "nice to have", "info"]

VALID_CATEGORIES = set(CATEGORIES.keys())
VALID_PRIORITIES = {"critical", "high", "medium", "low"}
VALID_RECOMMENDATIONS = {"approved", "review", "rejected"}
VALID_SENTIMENTS = {"positive", "neutral", "tense"}


# ---------------------------------------------------------------------------
# Text utilities (shared by both LLM and local paths)
# ---------------------------------------------------------------------------
def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def clean_sentence(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def unique(items: list) -> list:
    seen: set = set()
    out = []
    for item in items:
        key = repr(item).lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def summarize_text(text: str, limit: int = 2) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    freq = Counter(words(text))
    scored = []
    for idx, sentence in enumerate(sentences):
        score = sum(freq[w] for w in words(sentence)) / max(1, len(words(sentence)))
        scored.append((score, -idx, sentence))
    chosen = sorted(scored, reverse=True)[:limit]
    chosen = sorted(chosen, key=lambda x: -x[1])
    return " ".join(clean_sentence(x[2]) for x in chosen)


def parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None


def chunk_text(text: str, size: int = 420) -> list[str]:
    clean = clean_sentence(text)
    if not clean:
        return []
    sentences = split_sentences(clean)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) > size and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks or [clean[:size]]


# ---------------------------------------------------------------------------
# Local fallback implementations (private)
# ---------------------------------------------------------------------------
def _local_suggested_resolution(category: str, priority: str) -> str:
    base = {
        "it_support": "Check account access, device state, and recent changes before escalating to infrastructure.",
        "hr": "Verify policy, employee record, and manager approval path before responding.",
        "facilities": "Confirm location, impact, vendor need, and expected repair window.",
        "finance": "Match request against invoice, approval, and payment records.",
        "general": "Clarify owner, expected outcome, and deadline before assignment."
    }
    suffix = " Treat as same-day work." if priority in {"critical", "high"} else " Queue for normal operations review."
    return base.get(category, base["general"]) + suffix


def _local_ticket_classification(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    tokens = words(text)
    scores = {}
    for category, terms in CATEGORIES.items():
        scores[category] = sum(2 if term in text else tokens.count(term) for term in terms)
    category = max(scores, key=scores.get)
    if scores[category] == 0:
        category = "general"
    if any(term in text for term in CRITICAL):
        priority, hours = "critical", 2
    elif any(term in text for term in HIGH):
        priority, hours = "high", 6
    elif any(term in text for term in LOW):
        priority, hours = "low", 24
    else:
        priority, hours = "medium", 12
    summary = summarize_text(description, 1)
    resolution = _local_suggested_resolution(category, priority)
    return {
        "category": category,
        "priority": priority,
        "ai_summary": summary,
        "suggested_resolution": resolution,
        "assigned_to": TEAMS[category],
        "estimated_hours": hours
    }


def _local_leave_analysis(payload: dict) -> dict:
    start = parse_date(payload.get("start_date"))
    end = parse_date(payload.get("end_date"))
    today = date.today()
    if not start or not end or end < start:
        return {
            "recommendation": "review",
            "reasoning": "The date range needs correction before the request can be approved.",
            "risk_flags": ["invalid_date_range"],
            "conditions": ["Submit a valid start and end date."],
            "total_days": 0
        }
    total = (end - start).days + 1
    leave_type = str(payload.get("leave_type", "annual")).lower()
    notice = (start - today).days
    flags = []
    if leave_type == "annual" and notice < 7:
        flags.append("short_notice")
    if total > 10 and leave_type in {"annual", "unpaid"}:
        flags.append("long_absence")
    if leave_type == "sick" and start <= today:
        recommendation = "approved"
        reasoning = "Sick leave can be accepted immediately with a medical note if it extends beyond two days."
        conditions = ["Attach a medical note if the leave exceeds two days."] if total > 2 else []
    elif flags:
        recommendation = "review"
        reasoning = "The request is plausible but needs manager review because of notice period or duration."
        conditions = ["Manager approval required.", "Confirm backup ownership for active work."]
    else:
        recommendation = "approved"
        reasoning = "The request fits normal policy thresholds and has enough planning buffer."
        conditions = []
    return {
        "recommendation": recommendation,
        "reasoning": reasoning,
        "risk_flags": flags,
        "conditions": conditions,
        "total_days": total
    }


def _local_action_item(sentence: str) -> dict:
    speaker = None
    if ":" in sentence:
        speaker, sentence = sentence.split(":", 1)
    owner = speaker.strip() if speaker else "Unassigned"
    return {"owner": owner, "task": clean_sentence(sentence), "due": _infer_due(sentence)}


def _infer_due(text: str) -> str:
    low = text.lower()
    if "today" in low:
        return "today"
    if "tomorrow" in low:
        return "tomorrow"
    m = re.search(r"by ([A-Za-z]+(?: \d{1,2})?)", text)
    return m.group(1) if m else "open"


def _sentiment(text: str) -> str:
    low = text.lower()
    positive = sum(low.count(x) for x in ["great", "clear", "perfect", "approved", "good", "confirmed", "done"])
    negative = sum(low.count(x) for x in ["blocked", "risk", "late", "issue", "problem", "failed", "urgent"])
    if positive > negative + 1:
        return "positive"
    if negative > positive + 1:
        return "tense"
    return "neutral"


def _local_meeting_summary(transcript: str) -> dict:
    lines = [x.strip() for x in transcript.splitlines() if x.strip()]
    text = " ".join(lines)
    sentences = split_sentences(text)
    summary = summarize_text(text, 3)
    decisions = []
    actions = []
    for sentence in sentences:
        low = sentence.lower()
        if any(k in low for k in ["decision", "decided", "agreed", "confirmed", "deadline"]):
            decisions.append(clean_sentence(sentence))
        if any(k in low for k in ["i'll", "i will", "please", "need to", "can you", "by monday", "by friday", "today", "tomorrow"]):
            actions.append(_local_action_item(sentence))
    return {
        "summary": summary,
        "key_decisions": unique(decisions)[:6],
        "action_items": unique(actions)[:8],
        "sentiment": _sentiment(text)
    }


def _local_answer_question(question: str, docs: list[dict]) -> dict:
    q = set(words(question))
    if not q:
        return {"answer": "Ask a more specific question so I can search the indexed documents.", "sources": []}
    scored = []
    for doc in docs:
        for chunk in doc.get("chunks", []):
            c = set(words(chunk))
            if not c:
                continue
            overlap = len(q & c)
            density = overlap / math.sqrt(len(c))
            if overlap:
                scored.append((density, overlap, doc["name"], chunk))
    if not scored:
        return {"answer": "I could not find a reliable match in the uploaded documents.", "sources": []}
    scored.sort(reverse=True)
    top = scored[:3]
    answer = " ".join(item[3] for item in top)
    sources = [{"source": item[2], "match": item[1]} for item in top]
    return {"answer": summarize_text(answer, 4) or answer[:700], "sources": sources}


def _local_report(metrics: dict, tickets: list, leaves: list, meetings: list, tasks: list) -> str:
    risks = []
    if metrics.get("critical", 0):
        risks.append(f"{metrics['critical']} critical tickets need same-day attention")
    pending_leaves = len([x for x in leaves if x.get("status") == "pending"])
    if pending_leaves:
        risks.append(f"{pending_leaves} leave requests are waiting for review")
    open_tasks = len([x for x in tasks if x.get("status") != "done"])
    lines = [
        "Operations are stable with focused follow-up needed.",
        f"Ticket load is {metrics.get('total', 0)} total, with {metrics.get('open', 0)} still open.",
        f"Leave queue has {pending_leaves} pending requests.",
        f"Task board has {open_tasks} active items.",
        f"Recent meetings captured {sum(len(x.get('action_items', [])) for x in meetings)} action items."
    ]
    if risks:
        lines.append("Risks: " + "; ".join(risks) + ".")
    else:
        lines.append("No severe operational risk is visible in the current dataset.")
    return "\n".join(lines)


def _local_agent_reply(message: str, snapshot: dict) -> str:
    text = message.lower()
    if "ticket" in text:
        m = snapshot["ticket_metrics"]
        return f"There are {m['total']} tickets, {m['open']} open, {m['critical']} critical, and {m['resolved']} resolved."
    if "leave" in text:
        pending = len([x for x in snapshot["leaves"] if x.get("status") == "pending"])
        return f"{pending} leave requests are pending. Requests marked review should go to the manager first."
    if "meeting" in text or "action" in text:
        count = sum(len(x.get("action_items", [])) for x in snapshot["meetings"])
        return f"The meeting log currently contains {count} extracted action items."
    if "risk" in text:
        critical = snapshot["ticket_metrics"]["critical"]
        pending = len([x for x in snapshot["leaves"] if x.get("status") == "pending"])
        return f"Main risks: {critical} critical tickets and {pending} pending leave approvals."
    return "I can summarize tickets, leave requests, meeting actions, document answers, and daily operational risks."


# ---------------------------------------------------------------------------
# Public API — LLM-first with local fallback
# ---------------------------------------------------------------------------
def ticket_classification(title: str, description: str) -> dict:
    """Classify a support ticket using LLM, fall back to local rules."""
    system = (
        "You are an expert IT operations triage agent. Analyze the support ticket and return a JSON object with exactly these fields:\n"
        '{"category": "<it_support|hr|facilities|finance|general>", '
        '"priority": "<critical|high|medium|low>", '
        '"ai_summary": "<one sentence summary>", '
        '"suggested_resolution": "<actionable resolution steps>", '
        '"assigned_to": "<team name>", '
        '"estimated_hours": <integer hours to resolve>}\n'
        "Teams: it_support→IT Helpdesk, hr→People Ops, facilities→Admin Desk, finance→Finance Ops, general→Operations Coordinator.\n"
        "Priority: critical=system down/security breach/cannot work, high=blocked/salary/deadline, low=question/info, else medium.\n"
        "Return ONLY the JSON object, no explanation."
    )
    user = f"Title: {title}\nDescription: {description}"
    try:
        result = llm_json(system, user, max_tokens=512)
        # Validate and sanitize fields
        cat = result.get("category", "general")
        if cat not in VALID_CATEGORIES:
            cat = "general"
        pri = result.get("priority", "medium")
        if pri not in VALID_PRIORITIES:
            pri = "medium"
        team = TEAMS.get(cat, "Operations Coordinator")
        try:
            hours = int(result.get("estimated_hours", 12))
        except (ValueError, TypeError):
            hours = 12
        return {
            "category": cat,
            "priority": pri,
            "ai_summary": str(result.get("ai_summary", ""))[:500],
            "suggested_resolution": str(result.get("suggested_resolution", ""))[:1000],
            "assigned_to": team,
            "estimated_hours": hours
        }
    except Exception:
        return _local_ticket_classification(title, description)


def leave_analysis(payload: dict) -> dict:
    """Analyze a leave request using LLM, fall back to local rules."""
    start_str = payload.get("start_date", "")
    end_str = payload.get("end_date", "")
    start = parse_date(start_str)
    end = parse_date(end_str)
    today = date.today()
    total_days = ((end - start).days + 1) if (start and end and end >= start) else 0
    notice_days = (start - today).days if start else 0

    system = (
        "You are an HR policy analyst. Evaluate the leave request against company policy and return a JSON object with exactly these fields:\n"
        '{"recommendation": "<approved|review|rejected>", '
        '"reasoning": "<clear explanation>", '
        '"risk_flags": ["<flag1>", "<flag2>"], '
        '"conditions": ["<condition1>", "<condition2>"], '
        '"total_days": <integer>}\n'
        "Policy rules:\n"
        "- Annual leave requires 7 days notice. Flag 'short_notice' if notice < 7 days.\n"
        "- Leave > 10 days needs manager approval. Flag 'long_absence'.\n"
        "- Sick leave same-day is allowed; require medical note if > 2 days.\n"
        "- If recommendation is 'review', list conditions for approval.\n"
        "Return ONLY the JSON object, no explanation."
    )
    user = (
        f"Employee: {payload.get('employee_name', 'Unknown')}\n"
        f"Leave type: {payload.get('leave_type', 'annual')}\n"
        f"Start: {start_str}, End: {end_str}\n"
        f"Total days: {total_days}, Notice days: {notice_days}\n"
        f"Reason: {payload.get('reason', 'Not provided')}"
    )
    try:
        result = llm_json(system, user, max_tokens=512)
        rec = result.get("recommendation", "review")
        if rec not in VALID_RECOMMENDATIONS:
            rec = "review"
        try:
            total = int(result.get("total_days", total_days))
        except (ValueError, TypeError):
            total = total_days
        flags = result.get("risk_flags", [])
        if not isinstance(flags, list):
            flags = []
        conditions = result.get("conditions", [])
        if not isinstance(conditions, list):
            conditions = []
        return {
            "recommendation": rec,
            "reasoning": str(result.get("reasoning", ""))[:1000],
            "risk_flags": [str(f) for f in flags],
            "conditions": [str(c) for c in conditions],
            "total_days": total
        }
    except Exception:
        return _local_leave_analysis(payload)


def meeting_summary(transcript: str) -> dict:
    """Summarize a meeting transcript using LLM, fall back to local logic."""
    if not transcript.strip():
        return {"summary": "", "key_decisions": [], "action_items": [], "sentiment": "neutral"}

    system = (
        "You are a meeting analyst. Extract structured information from the meeting transcript and return a JSON object with exactly these fields:\n"
        '{"summary": "<3-4 sentence executive summary>", '
        '"key_decisions": ["<decision1>", "<decision2>"], '
        '"action_items": [{"owner": "<name or Unassigned>", "task": "<description>", "due": "<date or open>"}], '
        '"sentiment": "<positive|neutral|tense>"}\n'
        "Rules:\n"
        "- key_decisions: list of firm decisions made (max 6)\n"
        "- action_items: extract tasks assigned to specific people (max 8)\n"
        "- sentiment: positive=productive/aligned, tense=conflict/blocked, neutral=informational\n"
        "Return ONLY the JSON object, no explanation."
    )
    user = f"Transcript:\n{transcript}"
    try:
        result = llm_json(system, user, max_tokens=1024)
        decisions = result.get("key_decisions", [])
        if not isinstance(decisions, list):
            decisions = []
        actions = result.get("action_items", [])
        if not isinstance(actions, list):
            actions = []
        # Sanitize action items
        clean_actions = []
        for a in actions[:8]:
            if isinstance(a, dict):
                clean_actions.append({
                    "owner": str(a.get("owner", "Unassigned")),
                    "task": str(a.get("task", "")),
                    "due": str(a.get("due", "open"))
                })
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "neutral"
        return {
            "summary": str(result.get("summary", ""))[:2000],
            "key_decisions": [str(d) for d in decisions[:6]],
            "action_items": clean_actions,
            "sentiment": sentiment
        }
    except Exception:
        return _local_meeting_summary(transcript)


def answer_question(question: str, docs: list[dict]) -> dict:
    """Answer a document question using LLM with retrieved context, fall back to local retrieval."""
    if not question.strip():
        return {"answer": "Please ask a specific question.", "sources": []}

    # First do local retrieval to find relevant chunks (keep this regardless of LLM)
    q = set(words(question))
    scored = []
    for doc in docs:
        for chunk in doc.get("chunks", []):
            c = set(words(chunk))
            if not c:
                continue
            overlap = len(q & c)
            density = overlap / math.sqrt(len(c))
            if overlap:
                scored.append((density, overlap, doc["name"], chunk))
    scored.sort(reverse=True)
    top_chunks = scored[:5]

    if not top_chunks:
        return {"answer": "I could not find a reliable match in the uploaded documents.", "sources": []}

    context = "\n\n".join(f"[{item[2]}]: {item[3]}" for item in top_chunks)
    sources = [{"source": item[2], "match": item[1]} for item in top_chunks[:3]]

    system = (
        "You are a document Q&A assistant. Answer the user's question using ONLY the provided document excerpts. "
        "Be specific and cite relevant policy details. If the answer is not in the documents, say so clearly. "
        "Keep the answer concise (2-4 sentences)."
    )
    user = f"Question: {question}\n\nDocument excerpts:\n{context}"
    try:
        answer = llm_call(system, user, max_tokens=512)
        return {"answer": answer.strip(), "sources": sources}
    except Exception:
        return _local_answer_question(question, docs)


def report(metrics: dict, tickets: list, leaves: list, meetings: list, tasks: list) -> str:
    """Generate a daily operations report using LLM, fall back to local template."""
    pending_leaves = len([x for x in leaves if x.get("status") == "pending"])
    open_tasks = len([x for x in tasks if x.get("status") != "done"])
    total_actions = sum(len(x.get("action_items", [])) for x in meetings)

    system = (
        "You are an operations reporting assistant. Write a concise, professional daily operations report "
        "for the executive team. Use the provided metrics. Be specific about risks. Use plain paragraphs, "
        "no bullet points, no markdown headers. Max 6 sentences."
    )
    user = (
        f"Date: {date.today().isoformat()}\n"
        f"Tickets: {metrics.get('total', 0)} total, {metrics.get('open', 0)} open, "
        f"{metrics.get('critical', 0)} critical, {metrics.get('high', 0)} high, {metrics.get('resolved', 0)} resolved\n"
        f"Leave queue: {pending_leaves} pending requests\n"
        f"Tasks: {open_tasks} active items\n"
        f"Meetings: {len(meetings)} recorded, {total_actions} action items extracted\n"
        f"Top open tickets: {'; '.join(t.get('title', '') for t in tickets[:3]) or 'None'}"
    )
    try:
        return llm_call(system, user, max_tokens=512).strip()
    except Exception:
        return _local_report(metrics, tickets, leaves, meetings, tasks)


def agent_reply(message: str, snapshot: dict) -> str:
    """Generate an ops agent reply using LLM, fall back to local keyword matching."""
    metrics = snapshot.get("ticket_metrics", {})
    pending_leaves = len([x for x in snapshot.get("leaves", []) if x.get("status") == "pending"])
    open_tasks = len([x for x in snapshot.get("tasks", []) if x.get("status") != "done"])
    action_count = sum(len(x.get("action_items", [])) for x in snapshot.get("meetings", []))

    system = (
        "You are OpsPilot, an intelligent internal operations AI assistant. "
        "Answer questions about the current state of operations: tickets, leave requests, meetings, and tasks. "
        "Be concise, helpful, and specific. Use the provided operational snapshot. "
        "If asked about something outside operations, politely redirect. Max 3 sentences."
    )
    user = (
        f"User message: {message}\n\n"
        f"Current snapshot:\n"
        f"- Tickets: {metrics.get('total', 0)} total, {metrics.get('open', 0)} open, "
        f"{metrics.get('critical', 0)} critical, {metrics.get('resolved', 0)} resolved\n"
        f"- Leave: {pending_leaves} pending requests\n"
        f"- Tasks: {open_tasks} active\n"
        f"- Meeting actions: {action_count} extracted"
    )
    try:
        return llm_call(system, user, max_tokens=256).strip()
    except Exception:
        return _local_agent_reply(message, snapshot)
