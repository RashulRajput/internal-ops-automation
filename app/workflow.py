from __future__ import annotations

import json
import time
from typing import Any

from app.providers import llm_json, llm_call, active_provider_name

_STATE_KEYS = [
    "title", "description", "steps",
    "classification", "risk_assessment", "routing",
    "resolution", "final_result",
]
_CATEGORIES = {
    "it_support": ["vpn", "laptop", "password", "software", "login", "email",
                   "server", "network", "device", "access", "bug", "crash"],
    "hr": ["leave", "salary", "payroll", "policy", "benefit", "joining",
           "offer", "employee", "attendance", "reimbursement"],
    "facilities": ["ac", "chair", "desk", "office", "room", "light", "clean",
                   "parking", "conference", "water", "electric"],
    "finance": ["invoice", "payment", "expense", "budget", "vendor", "bill",
                "tax", "purchase", "approval"],
    "general": ["question", "request", "help", "support", "update", "info"],
}

_TEAMS = {
    "it_support": "IT Helpdesk",
    "hr": "People Ops",
    "facilities": "Admin Desk",
    "finance": "Finance Ops",
    "general": "Operations Coordinator",
}

_CRITICAL_WORDS = ["down", "blocked", "security", "breach", "payroll",
                   "production", "urgent", "outage", "cannot work"]
_HIGH_WORDS = ["not working", "failed", "stuck", "deadline", "client",
               "today", "salary", "access"]

def _fallback_classify(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    best_cat = "general"
    best_score = 0
    for cat, terms in _CATEGORIES.items():
        score = sum(1 for t in terms if t in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    if any(w in text for w in _CRITICAL_WORDS):
        priority = "critical"
    elif any(w in text for w in _HIGH_WORDS):
        priority = "high"
    else:
        priority = "medium"
    return {"category": best_cat, "priority": priority}

def _fallback_risk(classification: dict) -> dict:
    priority = classification.get("priority", "medium")
    risk_map = {
        "critical": ("high", ["service_disruption", "immediate_attention"]),
        "high": ("medium", ["potential_escalation"]),
        "medium": ("low", []),
        "low": ("minimal", []),
    }
    level, factors = risk_map.get(priority, ("low", []))
    return {"risk_level": level, "risk_factors": factors}

def _fallback_route(classification: dict) -> dict:
    cat = classification.get("category", "general")
    return {
        "team": _TEAMS.get(cat, "Operations Coordinator"),
        "category": cat,
        "escalation": classification.get("priority") in ("critical", "high"),
    }

def _fallback_resolve(classification: dict, routing: dict) -> dict:
    cat = classification.get("category", "general")
    resolutions = {
        "it_support": ["Verify account/device status", "Check recent changes", "Restart affected service", "Escalate to infrastructure if unresolved"],
        "hr": ["Review employee record", "Check policy compliance", "Forward to manager for approval"],
        "facilities": ["Log maintenance request", "Confirm location and impact", "Schedule vendor if needed"],
        "finance": ["Match against invoice records", "Verify approval chain", "Process or flag discrepancy"],
        "general": ["Clarify scope and ownership", "Assign to appropriate team", "Set follow-up deadline"],
    }
    return {
        "steps": resolutions.get(cat, resolutions["general"]),
        "estimated_hours": 2 if classification.get("priority") == "critical" else 8,
        "notes": f"Routed to {routing.get('team', 'Operations')}",
    }
def classify_node(state: dict) -> dict:
    start = time.time()
    provider = active_provider_name()
    try:
        system = (
            "You are an IT operations triage agent. Classify the support ticket "
            "and return a JSON object with exactly these fields:\n"
            '{"category": "<it_support|hr|facilities|finance|general>", '
            '"priority": "<critical|high|medium|low>"}\n'
            "Return ONLY the JSON object."
        )
        user = f"Title: {state['title']}\nDescription: {state['description']}"
        result = llm_json(system, user, max_tokens=256)
        valid_cats = set(_CATEGORIES.keys())
        valid_pris = {"critical", "high", "medium", "low"}
        cat = result.get("category", "general")
        if cat not in valid_cats:
            cat = "general"
        pri = result.get("priority", "medium")
        if pri not in valid_pris:
            pri = "medium"
        classification = {"category": cat, "priority": pri}
    except Exception:
        provider = "local-fallback"
        classification = _fallback_classify(state["title"], state["description"])

    latency = round((time.time() - start) * 1000)
    state["classification"] = classification
    state["steps"].append({
        "step": "classify",
        "provider": provider,
        "latency_ms": latency,
        "result": classification,
    })
    return state

def risk_node(state: dict) -> dict:
    start = time.time()
    provider = active_provider_name()
    try:
        system = (
            "You are a risk assessment agent. Given the ticket classification, "
            "assess the operational risk and return a JSON object with:\n"
            '{"risk_level": "<high|medium|low|minimal>", '
            '"risk_factors": ["<factor1>", "<factor2>"]}\n'
            "Return ONLY the JSON object."
        )
        user = (
            f"Title: {state['title']}\n"
            f"Description: {state['description']}\n"
            f"Classification: {json.dumps(state['classification'])}"
        )
        result = llm_json(system, user, max_tokens=256)
        risk_assessment = {
            "risk_level": str(result.get("risk_level", "low")),
            "risk_factors": result.get("risk_factors", []),
        }
        if not isinstance(risk_assessment["risk_factors"], list):
            risk_assessment["risk_factors"] = []
    except Exception:
        provider = "local-fallback"
        risk_assessment = _fallback_risk(state["classification"])

    latency = round((time.time() - start) * 1000)
    state["risk_assessment"] = risk_assessment
    state["steps"].append({
        "step": "assess_risk",
        "provider": provider,
        "latency_ms": latency,
        "result": risk_assessment,
    })
    return state

def route_node(state: dict) -> dict:
    start = time.time()
    provider = active_provider_name()
    try:
        system = (
            "You are a ticket routing agent. Based on the classification and risk, "
            "determine the best team to handle this ticket. Return a JSON object:\n"
            '{"team": "<team name>", "category": "<category>", "escalation": <true|false>}\n'
            "Teams: IT Helpdesk, People Ops, Admin Desk, Finance Ops, Operations Coordinator.\n"
            "Return ONLY the JSON object."
        )
        user = (
            f"Title: {state['title']}\n"
            f"Classification: {json.dumps(state['classification'])}\n"
            f"Risk: {json.dumps(state['risk_assessment'])}"
        )
        result = llm_json(system, user, max_tokens=256)
        routing = {
            "team": str(result.get("team", "Operations Coordinator")),
            "category": str(result.get("category", state["classification"].get("category", "general"))),
            "escalation": bool(result.get("escalation", False)),
        }
    except Exception:
        provider = "local-fallback"
        routing = _fallback_route(state["classification"])

    latency = round((time.time() - start) * 1000)
    state["routing"] = routing
    state["steps"].append({
        "step": "route",
        "provider": provider,
        "latency_ms": latency,
        "result": routing,
    })
    return state

def resolve_node(state: dict) -> dict:
    start = time.time()
    provider = active_provider_name()
    try:
        system = (
            "You are a resolution advisor. Suggest concrete steps to resolve the ticket. "
            "Return a JSON object:\n"
            '{"steps": ["<step1>", "<step2>", ...], '
            '"estimated_hours": <integer>, '
            '"notes": "<any additional notes>"}\n'
            "Return ONLY the JSON object."
        )
        user = (
            f"Title: {state['title']}\n"
            f"Description: {state['description']}\n"
            f"Classification: {json.dumps(state['classification'])}\n"
            f"Routing: {json.dumps(state['routing'])}"
        )
        result = llm_json(system, user, max_tokens=512)
        resolution = {
            "steps": result.get("steps", []),
            "estimated_hours": int(result.get("estimated_hours", 8)),
            "notes": str(result.get("notes", "")),
        }
        if not isinstance(resolution["steps"], list):
            resolution["steps"] = [str(resolution["steps"])]
    except Exception:
        provider = "local-fallback"
        resolution = _fallback_resolve(state["classification"], state["routing"])

    latency = round((time.time() - start) * 1000)
    state["resolution"] = resolution
    state["steps"].append({
        "step": "resolve",
        "provider": provider,
        "latency_ms": latency,
        "result": resolution,
    })
    return state
_LANGGRAPH_AVAILABLE = False
_workflow: Any = None

try:
    from langgraph.graph import StateGraph, START, END
    from typing import TypedDict

    class TicketWorkflowState(TypedDict):
        title: str
        description: str
        steps: list
        classification: dict
        risk_assessment: dict
        routing: dict
        resolution: dict
        final_result: dict

    def build_ticket_workflow() -> Any:
        graph = StateGraph(TicketWorkflowState)
        graph.add_node("classify", classify_node)
        graph.add_node("assess_risk", risk_node)
        graph.add_node("route", route_node)
        graph.add_node("resolve", resolve_node)
        graph.add_edge(START, "classify")
        graph.add_edge("classify", "assess_risk")
        graph.add_edge("assess_risk", "route")
        graph.add_edge("route", "resolve")
        graph.add_edge("resolve", END)
        return graph.compile()

    _LANGGRAPH_AVAILABLE = True

except ImportError:

    class TicketWorkflowState(dict):  # type: ignore[no-redef]
        pass

    def build_ticket_workflow() -> Any:
        class _SequentialWorkflow:
            def invoke(self, state: dict) -> dict:
                state = classify_node(state)
                state = risk_node(state)
                state = route_node(state)
                state = resolve_node(state)
                return state

        return _SequentialWorkflow()

def get_workflow() -> Any:
    global _workflow
    if _workflow is None:
        _workflow = build_ticket_workflow()
    return _workflow

def run_ticket_workflow(title: str, description: str) -> dict:
    wf = get_workflow()
    initial: dict[str, Any] = {
        "title": title,
        "description": description,
        "steps": [],
        "classification": {},
        "risk_assessment": {},
        "routing": {},
        "resolution": {},
        "final_result": {},
    }

    start = time.time()
    result = wf.invoke(initial)
    total_latency = round((time.time() - start) * 1000)
    providers_used = list({s.get("provider", "unknown") for s in result.get("steps", [])})
    result["final_result"] = {
        "title": title,
        "category": result.get("classification", {}).get("category", "general"),
        "priority": result.get("classification", {}).get("priority", "medium"),
        "risk_level": result.get("risk_assessment", {}).get("risk_level", "low"),
        "team": result.get("routing", {}).get("team", "Operations Coordinator"),
        "escalation": result.get("routing", {}).get("escalation", False),
        "resolution_steps": result.get("resolution", {}).get("steps", []),
        "estimated_hours": result.get("resolution", {}).get("estimated_hours", 8),
        "total_latency_ms": total_latency,
        "providers_used": providers_used,
        "step_count": len(result.get("steps", [])),
        "workflow_engine": "langgraph" if _LANGGRAPH_AVAILABLE else "sequential",
    }
    return result
