import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

class Store:
    def __init__(self, path: str = "internalops.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    submitter_name TEXT NOT NULL,
                    submitter_email TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    ai_summary TEXT,
                    suggested_resolution TEXT,
                    assigned_to TEXT,
                    estimated_hours INTEGER,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    resolved_at TEXT
                );
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name TEXT,
                    employee_email TEXT,
                    department TEXT,
                    leave_type TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    total_days INTEGER,
                    reason TEXT,
                    ai_recommendation TEXT,
                    ai_reasoning TEXT,
                    risk_flags TEXT,
                    conditions TEXT,
                    status TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    date TEXT,
                    duration_minutes INTEGER,
                    participants TEXT,
                    transcript TEXT,
                    summary TEXT,
                    key_decisions TEXT,
                    action_items TEXT,
                    sentiment TEXT,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category TEXT,
                    uploaded_by TEXT,
                    content TEXT,
                    chunks TEXT,
                    file_type TEXT,
                    file_size_kb REAL,
                    created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    owner TEXT,
                    priority TEXT,
                    status TEXT,
                    due_date TEXT,
                    source TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    action TEXT,
                    provider TEXT,
                    latency_ms INTEGER,
                    input_summary TEXT,
                    output_summary TEXT,
                    success INTEGER
                );
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_title TEXT,
                    steps_json TEXT,
                    total_latency_ms INTEGER,
                    providers_used TEXT,
                    created_at TEXT
                );
                """
            )
    def create_ticket(self, payload: dict, analysis: dict) -> dict:
        now = iso()
        data = {
            **payload,
            **analysis,
            "status": payload.get("status", "open"),
            "created_at": now,
            "updated_at": now,
            "resolved_at": None
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO tickets ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_ticket(cur.lastrowid)

    def list_tickets(self) -> list[dict]:
        return self.all("SELECT * FROM tickets ORDER BY id DESC")

    def get_ticket(self, ticket_id: int) -> dict | None:
        return self.one("SELECT * FROM tickets WHERE id = ?", [ticket_id])

    def update_ticket(self, ticket_id: int, patch: dict) -> dict | None:
        allowed = {"status", "assigned_to", "priority"}
        keys = [k for k in patch if k in allowed]
        if not keys:
            return self.get_ticket(ticket_id)
        patch["updated_at"] = iso()
        keys.append("updated_at")
        with self.connect() as db:
            db.execute(
                f"UPDATE tickets SET {','.join(f'{k} = ?' for k in keys)} WHERE id = ?",
                [patch[k] for k in keys] + [ticket_id]
            )
            db.commit()
        return self.get_ticket(ticket_id)

    def ticket_metrics(self) -> dict:
        rows = self.all("SELECT status, priority FROM tickets")
        return {
            "total": len(rows),
            "open": len([r for r in rows if r["status"] == "open"]),
            "resolved": len([r for r in rows if r["status"] == "resolved"]),
            "critical": len([r for r in rows if r["priority"] == "critical"]),
            "high": len([r for r in rows if r["priority"] == "high"])
        }
    def create_leave(self, payload: dict, analysis: dict) -> dict:
        data = {
            "employee_name": payload.get("employee_name", ""),
            "employee_email": payload.get("employee_email", ""),
            "department": payload.get("department", ""),
            "leave_type": payload.get("leave_type", "annual"),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
            "total_days": analysis["total_days"],
            "reason": payload.get("reason", ""),
            "ai_recommendation": analysis["recommendation"],
            "ai_reasoning": analysis["reasoning"],
            "risk_flags": dump(analysis["risk_flags"]),
            "conditions": dump(analysis["conditions"]),
            "status": "pending" if analysis["recommendation"] == "review" else analysis["recommendation"],
            "created_at": iso()
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO leave_requests ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_leave(cur.lastrowid)

    def list_leaves(self) -> list[dict]:
        return [decode(r, ["risk_flags", "conditions"]) for r in self.all("SELECT * FROM leave_requests ORDER BY id DESC")]

    def get_leave(self, leave_id: int) -> dict | None:
        row = self.one("SELECT * FROM leave_requests WHERE id = ?", [leave_id])
        return decode(row, ["risk_flags", "conditions"]) if row else None
    def create_meeting(self, payload: dict, analysis: dict) -> dict:
        data = {
            "title": payload.get("title", ""),
            "date": payload.get("date", iso()),
            "duration_minutes": payload.get("duration_minutes") or 0,
            "participants": dump(payload.get("participants", [])),
            "transcript": payload.get("transcript", ""),
            "summary": analysis["summary"],
            "key_decisions": dump(analysis["key_decisions"]),
            "action_items": dump(analysis["action_items"]),
            "sentiment": analysis["sentiment"],
            "created_at": iso()
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO meetings ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            meeting = self.get_meeting(cur.lastrowid)
        for item in meeting["action_items"]:
            self.create_task({
                "title": item.get("task", ""),
                "owner": item.get("owner", "Unassigned"),
                "priority": "medium",
                "due_date": item.get("due", "open"),
                "source": f"meeting:{meeting['id']}"
            })
        return meeting

    def list_meetings(self) -> list[dict]:
        return [decode(r, ["participants", "key_decisions", "action_items"]) for r in self.all("SELECT * FROM meetings ORDER BY id DESC")]

    def get_meeting(self, meeting_id: int) -> dict | None:
        row = self.one("SELECT * FROM meetings WHERE id = ?", [meeting_id])
        return decode(row, ["participants", "key_decisions", "action_items"]) if row else None
    def create_document(self, payload: dict, chunks: list[str]) -> dict:
        content = payload.get("content", "")
        data = {
            "name": payload.get("name", "Document"),
            "category": payload.get("category", "general"),
            "uploaded_by": payload.get("uploaded_by", "user"),
            "content": content,
            "chunks": dump(chunks),
            "file_type": payload.get("file_type", "text"),
            "file_size_kb": round(len(content.encode("utf-8")) / 1024, 2),
            "created_at": iso()
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO documents ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_document(cur.lastrowid)

    def list_documents(self) -> list[dict]:
        docs = []
        for row in self.all("SELECT * FROM documents ORDER BY id DESC"):
            doc = decode(row, ["chunks"])
            doc["chunk_count"] = len(doc.get("chunks", []))
            doc.pop("content", None)
            doc.pop("chunks", None)
            docs.append(doc)
        return docs

    def documents_for_search(self) -> list[dict]:
        return [decode(r, ["chunks"]) for r in self.all("SELECT id, name, chunks FROM documents ORDER BY id DESC")]

    def get_document(self, document_id: int) -> dict | None:
        row = self.one("SELECT * FROM documents WHERE id = ?", [document_id])
        if not row:
            return None
        doc = decode(row, ["chunks"])
        doc["chunk_count"] = len(doc.get("chunks", []))
        return doc
    def create_task(self, payload: dict) -> dict:
        data = {
            "title": payload.get("title", ""),
            "owner": payload.get("owner", "Unassigned"),
            "priority": payload.get("priority", "medium"),
            "status": payload.get("status", "open"),
            "due_date": payload.get("due_date", ""),
            "source": payload.get("source", "manual"),
            "created_at": iso(),
            "updated_at": iso()
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO tasks ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_task(cur.lastrowid)

    def list_tasks(self) -> list[dict]:
        return self.all("SELECT * FROM tasks ORDER BY id DESC")

    def get_task(self, task_id: int) -> dict | None:
        return self.one("SELECT * FROM tasks WHERE id = ?", [task_id])

    def update_task(self, task_id: int, patch: dict) -> dict | None:
        allowed = {"title", "owner", "priority", "status", "due_date"}
        keys = [k for k in patch if k in allowed]
        patch["updated_at"] = iso()
        keys.append("updated_at")
        with self.connect() as db:
            db.execute(
                f"UPDATE tasks SET {','.join(f'{k} = ?' for k in keys)} WHERE id = ?",
                [patch[k] for k in keys] + [task_id]
            )
            db.commit()
        return self.get_task(task_id)
    def create_audit_entry(
        self,
        action: str,
        provider: str,
        latency_ms: int,
        input_summary: str,
        output_summary: str,
        success: bool = True,
    ) -> dict:
        data = {
            "timestamp": iso(),
            "action": action,
            "provider": provider,
            "latency_ms": latency_ms,
            "input_summary": input_summary[:500],
            "output_summary": output_summary[:500],
            "success": 1 if success else 0,
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO audit_log ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.one("SELECT * FROM audit_log WHERE id = ?", [cur.lastrowid])

    def list_audit_log(self, limit: int = 50) -> list[dict]:
        return self.all(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", [limit]
        )
    def create_workflow_run(
        self,
        title: str,
        steps: list[dict],
        total_latency: int,
        providers: list[str],
    ) -> dict:
        data = {
            "ticket_title": title,
            "steps_json": dump(steps),
            "total_latency_ms": total_latency,
            "providers_used": dump(providers),
            "created_at": iso(),
        }
        keys = list(data)
        with self.connect() as db:
            cur = db.execute(
                f"INSERT INTO workflow_runs ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self._get_workflow_run(cur.lastrowid)

    def _get_workflow_run(self, run_id: int) -> dict | None:
        row = self.one("SELECT * FROM workflow_runs WHERE id = ?", [run_id])
        return decode(row, ["steps_json", "providers_used"]) if row else None

    def list_workflow_runs(self, limit: int = 20) -> list[dict]:
        rows = self.all(
            "SELECT * FROM workflow_runs ORDER BY id DESC LIMIT ?", [limit]
        )
        return [decode(r, ["steps_json", "providers_used"]) for r in rows]

    def workflow_stats(self) -> dict:
        rows = self.all("SELECT total_latency_ms, providers_used FROM workflow_runs")
        if not rows:
            return {"total_runs": 0, "avg_latency_ms": 0, "providers_used": {}}

        total = len(rows)
        avg_latency = round(sum(r["total_latency_ms"] for r in rows) / total)

        provider_counts: Counter = Counter()
        for row in rows:
            try:
                providers = json.loads(row["providers_used"]) if isinstance(row["providers_used"], str) else row["providers_used"]
                if isinstance(providers, list):
                    for p in providers:
                        provider_counts[str(p)] += 1
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "total_runs": total,
            "avg_latency_ms": avg_latency,
            "providers_used": dict(provider_counts),
        }
    def snapshot(self) -> dict:
        return {
            "ticket_metrics": self.ticket_metrics(),
            "tickets": self.list_tickets(),
            "leaves": self.list_leaves(),
            "meetings": self.list_meetings(),
            "tasks": self.list_tasks(),
            "documents": self.list_documents()
        }
    def all(self, sql: str, params: list | None = None) -> list[dict]:
        with self.connect() as db:
            return [dict(r) for r in db.execute(sql, params or [])]

    def one(self, sql: str, params: list | None = None) -> dict | None:
        with self.connect() as db:
            row = db.execute(sql, params or []).fetchone()
            return dict(row) if row else None
def iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)

def decode(row: dict | None, keys: list[str]) -> dict | None:
    if not row:
        return row
    out = dict(row)
    for key in keys:
        try:
            out[key] = json.loads(out.get(key) or "[]")
        except json.JSONDecodeError:
            out[key] = []
    return out
