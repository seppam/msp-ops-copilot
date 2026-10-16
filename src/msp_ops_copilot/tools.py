"""Plain Python functions the model is allowed to call, plus their JSON schemas.

The model never runs these. It only *asks* for one by name with arguments;
our code runs it and sends the result back. That separation is what makes
tool calling safe and testable.
"""

import json
from pathlib import Path

TICKETS_FILE = Path(__file__).resolve().parents[2] / "data" / "tickets.json"


def _load() -> list[dict]:
    return json.loads(TICKETS_FILE.read_text())


def list_tickets(status: str = "open") -> list[dict]:
    return [
        {"id": t["id"], "customer": t["customer"], "subject": t["subject"]}
        for t in _load()
        if t["status"] == status
    ]


def get_ticket(ticket_id: int) -> dict:
    for t in _load():
        if t["id"] == ticket_id:
            return t
    return {"error": f"ticket {ticket_id} not found"}


REGISTRY = {"list_tickets": list_tickets, "get_ticket": get_ticket}

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_tickets",
            "description": "List tickets (id, customer, subject) filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["open", "closed"]}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket",
            "description": "Get the full details of one ticket by its id.",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        },
    },
]
