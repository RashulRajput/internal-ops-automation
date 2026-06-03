import json
import sqlite3
from datetime import datetime
from pathlib import Path


class Store:
    def __init__(self, path="internalops.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def init(self):
        with self.connect() as db:
            db.executescript(
                """
                create table if not exists tickets (
                    id integer primary key autoincrement,
                    title text not null,
                    description text not null,
                    submitter_name text not null,
                    submitter_email text not null,
                    category text,
                    priority text,
                    ai_summary text,
                    suggested_resolution text,
                    assigned_to text,
                    estimated_hours integer,
                    status text default 'open',
                    created_at text,
                    updated_at text,
                    resolved_at text
                );
                create table if not exists leave_requests (
                    id integer primary key autoincrement,
                    employee_name text not null,
                    employee_email text not null,
                    department text,
                    leave_type text,
                    start_date text,
                    end_date text,
                    total_days integer,
                    reason text,
                    ai_recommendation text,
                    ai_reasoning text,
                    risk_flags text,
                    conditions text,
                    status text default 'pending',
                    created_at text
                );
                create table if not exists meetings (
                    id integer primary key autoincrement,
                    title text not null,
                    date text,
                    duration_minutes integer,
                    participants text,
                    transcript text,
                    summary text,
                    key_decisions text,
                    action_items text,
                    sentiment text,
                    created_at text
                );
                create table if not exists documents (
                    id integer primary key autoincrement,
                    name text not null,
                    category text,
                    uploaded_by text,
                    content text,
                    chunks text,
                    file_type text,
                    file_size_kb real,
                    created_at text
                );
                create table if not exists tasks (
                    id integer primary key autoincrement,
                    title text not null,
                    owner text,
                    priority text,
                    status text default 'open',
                    due_date text,
                    source text,
                    created_at text,
                    updated_at text
                );
                """
            )

    def create_ticket(self, payload, analysis):
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
                f"insert into tickets ({','.join(keys)}) values ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_ticket(cur.lastrowid)

    def list_tickets(self):
        return self.all("select * from tickets order by id desc")

    def get_ticket(self, ticket_id):
        return self.one("select * from tickets where id = ?", [ticket_id])

    def update_ticket(self, ticket_id, patch):
        allowed = {"status", "assigned_to", "priority"}
        keys = [k for k in patch if k in allowed]
        if not keys:
            return self.get_ticket(ticket_id)
        patch["updated_at"] = iso()
        keys.append("updated_at")
        with self.connect() as db:
            db.execute(
                f"update tickets set {','.join(f'{k} = ?' for k in keys)} where id = ?",
                [patch[k] for k in keys] + [ticket_id]
            )
            db.commit()
        return self.get_ticket(ticket_id)

    def ticket_metrics(self):
        rows = self.all("select status, priority from tickets")
        return {
            "total": len(rows),
            "open": len([r for r in rows if r["status"] == "open"]),
            "resolved": len([r for r in rows if r["status"] == "resolved"]),
            "critical": len([r for r in rows if r["priority"] == "critical"]),
            "high": len([r for r in rows if r["priority"] == "high"])
        }

    def create_leave(self, payload, analysis):
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
                f"insert into leave_requests ({','.join(keys)}) values ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_leave(cur.lastrowid)

    def list_leaves(self):
        return [decode(r, ["risk_flags", "conditions"]) for r in self.all("select * from leave_requests order by id desc")]

    def get_leave(self, leave_id):
        row = self.one("select * from leave_requests where id = ?", [leave_id])
        return decode(row, ["risk_flags", "conditions"]) if row else None

    def create_meeting(self, payload, analysis):
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
                f"insert into meetings ({','.join(keys)}) values ({','.join('?' for _ in keys)})",
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

    def list_meetings(self):
        return [decode(r, ["participants", "key_decisions", "action_items"]) for r in self.all("select * from meetings order by id desc")]

    def get_meeting(self, meeting_id):
        row = self.one("select * from meetings where id = ?", [meeting_id])
        return decode(row, ["participants", "key_decisions", "action_items"]) if row else None

    def create_document(self, payload, chunks):
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
                f"insert into documents ({','.join(keys)}) values ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_document(cur.lastrowid)

    def list_documents(self):
        docs = []
        for row in self.all("select * from documents order by id desc"):
            doc = decode(row, ["chunks"])
            doc["chunk_count"] = len(doc.get("chunks", []))
            doc.pop("content", None)
            doc.pop("chunks", None)
            docs.append(doc)
        return docs

    def documents_for_search(self):
        return [decode(r, ["chunks"]) for r in self.all("select id, name, chunks from documents order by id desc")]

    def get_document(self, document_id):
        row = self.one("select * from documents where id = ?", [document_id])
        if not row:
            return None
        doc = decode(row, ["chunks"])
        doc["chunk_count"] = len(doc.get("chunks", []))
        return doc

    def create_task(self, payload):
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
                f"insert into tasks ({','.join(keys)}) values ({','.join('?' for _ in keys)})",
                [data[k] for k in keys]
            )
            db.commit()
            return self.get_task(cur.lastrowid)

    def list_tasks(self):
        return self.all("select * from tasks order by id desc")

    def get_task(self, task_id):
        return self.one("select * from tasks where id = ?", [task_id])

    def update_task(self, task_id, patch):
        allowed = {"title", "owner", "priority", "status", "due_date"}
        keys = [k for k in patch if k in allowed]
        patch["updated_at"] = iso()
        keys.append("updated_at")
        with self.connect() as db:
            db.execute(
                f"update tasks set {','.join(f'{k} = ?' for k in keys)} where id = ?",
                [patch[k] for k in keys] + [task_id]
            )
            db.commit()
        return self.get_task(task_id)

    def snapshot(self):
        return {
            "ticket_metrics": self.ticket_metrics(),
            "tickets": self.list_tickets(),
            "leaves": self.list_leaves(),
            "meetings": self.list_meetings(),
            "tasks": self.list_tasks(),
            "documents": self.list_documents()
        }

    def all(self, sql, params=None):
        with self.connect() as db:
            return [dict(r) for r in db.execute(sql, params or [])]

    def one(self, sql, params=None):
        with self.connect() as db:
            row = db.execute(sql, params or []).fetchone()
            return dict(row) if row else None


def iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def dump(value):
    return json.dumps(value, ensure_ascii=False)


def decode(row, keys):
    if not row:
        return row
    out = dict(row)
    for key in keys:
        try:
            out[key] = json.loads(out.get(key) or "[]")
        except json.JSONDecodeError:
            out[key] = []
    return out
