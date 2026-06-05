import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

def _load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_dotenv(str(Path(__file__).resolve().parents[1] / ".env"))

from app.providers import active_provider_name, benchmark_providers, get_provider_status, reset_chain  # noqa: E402
from app.rag import vector_backend_status  # noqa: E402

reset_chain()

from app.brain import (  # noqa: E402
    agent_reply, answer_question, chunk_text,
    leave_analysis, meeting_summary, report, ticket_classification, workflow_classify_ticket
)
from app.store import Store  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
FRONTEND = BASE / "frontend"

_db_env = os.environ.get("INTERNALOPS_DB", "").strip()
if _db_env:
    DB_PATH = _db_env
else:
    DB_PATH = str(Path(os.environ.get("TEMP", "C:\\tmp")) / "opspilot" / "internalops.db")

store = Store(DB_PATH)

class Handler(BaseHTTPRequestHandler):
    server_version = "InternalOps/1.0"

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PATCH(self):
        self.dispatch("PATCH")

    def dispatch(self, method):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            body = self.read_json() if method in {"POST", "PATCH"} else {}

            if path == "/health" or path == "/api/health":
                return self.json({
                    "status": "healthy",
                    "service": "OpsPilot AI",
                    "ai_provider": active_provider_name(),
                    "mode": "ai" if active_provider_name() != "Local fallback" else "fallback"
                })
            if path == "/api/ai/status":
                return self.json({
                    "active_provider": active_provider_name(),
                    "providers": get_provider_status(),
                    "vector_store": vector_backend_status(),
                    "mode": os.environ.get("AI_PROVIDER_MODE", "free-first")
                })
            if path == "/api/ai/benchmark" and method == "POST":
                return self.json({"results": benchmark_providers(body.get("prompt", "Say hello in one sentence."))})
            if path == "/api/summary":
                snap = store.snapshot()
                snap["provider"] = active_provider_name()
                snap["workflow_stats"] = store.workflow_stats()
                return self.json(snap)
            if path == "/api/tickets" and method == "GET":
                return self.json({"tickets": store.list_tickets()})
            if path == "/api/tickets/stats/summary" and method == "GET":
                return self.json(store.ticket_metrics())
            if path == "/api/tickets" and method == "POST":
                required(body, ["title", "description", "submitter_name", "submitter_email"])
                workflow = workflow_classify_ticket(body["title"], body["description"])
                final = workflow.get("final_result", {})
                analysis = {
                    "category": final.get("category", "general"),
                    "priority": final.get("priority", "medium"),
                    "ai_summary": f"Risk: {final.get('risk_level', 'low')}. Routed to {final.get('team', 'Operations Coordinator')}.",
                    "suggested_resolution": "; ".join(final.get("resolution_steps", [])) or "Review and assign to operations.",
                    "assigned_to": final.get("team", "Operations Coordinator"),
                    "estimated_hours": final.get("estimated_hours", 8),
                }
                item = store.create_ticket(body, analysis)
                store.create_workflow_run(
                    body["title"],
                    workflow.get("steps", []),
                    final.get("total_latency_ms", 0),
                    final.get("providers_used", []),
                )
                return self.json(item)
            if path.startswith("/api/tickets/"):
                ticket_id = int(path.rsplit("/", 1)[-1])
                if method == "GET":
                    item = store.get_ticket(ticket_id)
                else:
                    item = store.update_ticket(ticket_id, body)
                return self.found(item)
            if path == "/api/leave" and method == "GET":
                return self.json({"leaves": store.list_leaves()})
            if path == "/api/leave" and method == "POST":
                required(body, ["employee_name", "employee_email", "start_date", "end_date", "reason"])
                return self.json(store.create_leave(body, leave_analysis(body)))
            if path.startswith("/api/leave/") and method == "PATCH":
                leave_id = int(path.rsplit("/", 1)[-1])
                return self.found(store.update_leave(leave_id, body))
            if path == "/api/meetings" and method == "GET":
                return self.json({"meetings": store.list_meetings()})
            if path == "/api/meetings" and method == "POST":
                required(body, ["title", "transcript"])
                return self.json(store.create_meeting(body, meeting_summary(body.get("transcript", ""))))
            if path == "/api/documents" and method == "GET":
                return self.json({"documents": store.list_documents()})
            if path == "/api/documents" and method == "POST":
                required(body, ["name", "content"])
                return self.json(store.create_document(body, chunk_text(body.get("content", ""))))
            if path == "/api/documents/query" and method == "POST":
                return self.json(answer_question(body.get("question", ""), store.documents_for_search()))
            if path == "/api/tasks" and method == "GET":
                return self.json({"tasks": store.list_tasks()})
            if path == "/api/tasks" and method == "POST":
                required(body, ["title"])
                return self.json(store.create_task(body))
            if path.startswith("/api/tasks/") and method == "PATCH":
                return self.found(store.update_task(int(path.rsplit("/", 1)[-1]), body))
            if path == "/api/workflows/ticket" and method == "POST":
                required(body, ["title", "description"])
                workflow = workflow_classify_ticket(body["title"], body["description"])
                final = workflow.get("final_result", {})
                store.create_workflow_run(
                    body["title"],
                    workflow.get("steps", []),
                    final.get("total_latency_ms", 0),
                    final.get("providers_used", []),
                )
                return self.json(workflow)
            if path == "/api/workflows/runs" and method == "GET":
                return self.json({"runs": store.list_workflow_runs(), "stats": store.workflow_stats()})
            if path == "/api/audit" and method == "GET":
                return self.json({"audit": store.list_audit_log()})
            if path == "/api/reports/daily" and method == "GET":
                snap = store.snapshot()
                text = report(snap["ticket_metrics"], snap["tickets"], snap["leaves"], snap["meetings"], snap["tasks"])
                return self.json({
                    "success": True,
                    "date": store_date(),
                    "metrics": snap["ticket_metrics"],
                    "report": text,
                    "ai_provider": active_provider_name()
                })
            if path == "/api/agent/chat" and method == "POST":
                return self.json({
                    "response": agent_reply(body.get("message", ""), store.snapshot()),
                    "ai_provider": active_provider_name()
                })
            if path == "/api/demo/seed" and method == "POST":
                seed_demo()
                return self.json({"ok": True})
            if path.startswith("/api/"):
                return self.error(404, "Endpoint not found")
            return self.static(path)
        except ValueError as exc:
            return self.error(400, str(exc))
        except Exception as exc:
            return self.error(500, str(exc))

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def static(self, path):
        rel = "index.html" if path == "/" else path.lstrip("/")
        target = (FRONTEND / rel).resolve()
        if FRONTEND not in target.parents and target != FRONTEND:
            return self.error(403, "Forbidden")
        if not target.exists() or target.is_dir():
            target = FRONTEND / "index.html"
        content = target.read_bytes()
        mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.cors()
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def json(self, payload, status=200):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def found(self, item):
        if not item:
            return self.error(404, "Record not found")
        return self.json(item)

    def error(self, status, message):
        return self.json({"detail": message}, status)

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PATCH,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        return

def required(payload, keys):
    missing = [k for k in keys if not str(payload.get(k, "")).strip()]
    if missing:
        raise ValueError("Missing required field: " + ", ".join(missing))

def store_date():
    from datetime import date
    return date.today().isoformat()

def seed_demo():
    existing_tickets = store.list_tickets()
    if any(t.get("title") == "VPN access fails for remote team" for t in existing_tickets):
        return
    tickets = [
        {
            "title": "VPN access fails for remote team",
            "description": "The product team cannot connect to the VPN since morning and is blocked from staging.",
            "submitter_name": "Rajesh Kumar",
            "submitter_email": "rajesh@webvory.com"
        },
        {
            "title": "Conference room AC not cooling",
            "description": "Conference Room B has been warm for three days and client meetings are uncomfortable.",
            "submitter_name": "Neha Joshi",
            "submitter_email": "neha@webvory.com"
        },
        {
            "title": "March payroll difference",
            "description": "My salary is lower than expected even though no leave was taken.",
            "submitter_name": "Priya Singh",
            "submitter_email": "priya@webvory.com"
        }
    ]
    for item in tickets:
        store.create_ticket(item, ticket_classification(item["title"], item["description"]))
    store.create_leave({
        "employee_name": "Sneha Patel",
        "employee_email": "sneha@webvory.com",
        "department": "Engineering",
        "leave_type": "annual",
        "start_date": "2026-06-15",
        "end_date": "2026-06-20",
        "reason": "Family travel planned in advance."
    }, leave_analysis({
        "leave_type": "annual",
        "start_date": "2026-06-15",
        "end_date": "2026-06-20"
    }))
    transcript = """
Rahul: Decision made, Slack leave requests are P1 for June.
Neha: I will finish the flows by Friday.
Arjun: Engineering needs API contracts by Monday.
Priyanka: I will confirm the policy wording with HR today.
Rahul: Great, follow-up next Friday.
"""
    store.create_meeting({
        "title": "Q2 Ops Automation Planning",
        "date": "2026-06-01T10:00:00",
        "duration_minutes": 45,
        "participants": ["Rahul", "Neha", "Arjun", "Priyanka"],
        "transcript": transcript
    }, meeting_summary(transcript))
    store.create_document({
        "name": "Leave Policy",
        "category": "hr",
        "uploaded_by": "People Ops",
        "content": "Annual leave should be requested seven days in advance. Sick leave can be submitted the same day. Leave longer than ten days needs manager approval and backup ownership."
    }, chunk_text("Annual leave should be requested seven days in advance. Sick leave can be submitted the same day. Leave longer than ten days needs manager approval and backup ownership."))

def main():
    seed_demo()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), Handler)
    provider = active_provider_name()
    print(f"OpsPilot AI running at http://{host}:{port}")
    print(f"AI Provider: {provider}")
    server.serve_forever()

if __name__ == "__main__":
    main()
