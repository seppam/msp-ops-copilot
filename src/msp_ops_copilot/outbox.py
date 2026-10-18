"""A tiny file-backed outbox: one JSON file per ticket holding the email waiting to be sent.

The triage step only WRITES here. n8n picks emails up (see outbox_server.py), sends them and reports back.
Keeping the sender separate means the AI step never needs mail credentials, and a failed send is visible.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

OUTBOX = Path(__file__).resolve().parents[2] / "outbox"


def enqueue(ticket_id: str, odoo_id: int, to: str, subject: str, body: str) -> bool:
    """Queue one requester email per ticket. Returns False if one already exists (safe to re-run)."""
    OUTBOX.mkdir(exist_ok=True)
    path = OUTBOX / f"{ticket_id}.json"
    if path.exists():
        return False
    item = {"id": ticket_id, "odoo_id": odoo_id, "to": to, "subject": subject, "body": body, "status": "pending",
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.write_text(json.dumps(item, ensure_ascii=False, indent=1))
    return True


def pending() -> list[dict]:
    items = [json.loads(p.read_text()) for p in sorted(OUTBOX.glob("*.json"))] if OUTBOX.exists() else []
    return [i for i in items if i["status"] == "pending"]


def mark_sent(ticket_id: str) -> dict | None:
    path = OUTBOX / f"{ticket_id}.json"
    if not path.exists():
        return None
    item = json.loads(path.read_text())
    item.update(status="sent", sent=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    path.write_text(json.dumps(item, ensure_ascii=False, indent=1))
    return item
