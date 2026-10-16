"""Step 5: triage agent with structured output.

For each open ticket: ask the model for a JSON triage result, validate it
against a Pydantic schema (retry once with the error if it does not fit),
then optionally write it back to Odoo as an internal note.
Default is a dry run; pass --write to change anything in Odoo.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from msp_ops_copilot.llm import get_client
from msp_ops_copilot import odoo_client as odoo
from msp_ops_copilot.mcp_server import add_ticket_note, get_ticket, list_tickets
from msp_ops_copilot.rag import search

MAX_DISTANCE = 0.75  # sections farther than this are treated as 'not relevant'
AI_NOTE_MARKER = "AI triage (draft"  # first words of every note we write
AUDIT_LOG = Path(__file__).resolve().parents[2] / "logs" / "triage.jsonl"


class Category(str, Enum):
    network = "network"
    email = "email"
    hardware = "hardware"
    security = "security"
    storage = "storage"
    other = "other"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Triage(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=200, description="One sentence for the engineer.")
    draft_reply: str = Field(description="Short, polite reply to the customer.")
    next_action: str = Field(description="First concrete step for the engineer.")


SYSTEM = f"""You are a service desk triage assistant for a managed IT provider.
Reply with ONLY a JSON object matching this JSON Schema, no extra text:
{json.dumps(Triage.model_json_schema())}
Follow the company policy excerpts provided with each ticket. They override your own judgement.
If no excerpt applies, use your best judgement and keep priority conservative."""


def policy_for(ticket: dict) -> list[dict]:
    """Retrieve the company rules most relevant to this ticket (RAG)."""
    query = f"{ticket['subject']}. {ticket.get('description', '')}"
    hits = [h for h in search(query, k=4) if h["distance"] <= MAX_DISTANCE]
    # The classification rules are always needed, whatever the ticket says.
    if not any(h["source"] == "triage-policy.md" for h in hits):
        hits += [h for h in search("priority definitions and categories", k=2) if h["source"] == "triage-policy.md"]
    return hits


def triage_ticket(ticket: dict, retries: int = 1) -> tuple[Triage, list[dict]]:
    client, model = get_client()
    hits = policy_for(ticket)
    excerpts = "\n\n".join(f"[{h['source']} > {h['section']}]\n{h['text']}" for h in hits)
    messages = [
        {"role": "system", "content": f"{SYSTEM}\n\nCompany policy excerpts:\n{excerpts}"},
        {"role": "user", "content": json.dumps(ticket)},
    ]
    for attempt in range(retries + 1):
        raw = client.chat.completions.create(
            model=model, messages=messages, response_format={"type": "json_object"}, max_tokens=900
        ).choices[0].message.content
        try:
            return Triage.model_validate_json(raw), hits
        except ValidationError as exc:
            if attempt == retries:
                raise
            # Show the model exactly what was wrong so it can fix its own output.
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"Invalid: {exc.errors(include_url=False)}. Return corrected JSON only."},
            ]


def format_note(t: Triage, hits: list[dict]) -> str:
    # Sources come from the retrieval step, not from the model, so they cannot be invented.
    sources = ", ".join(sorted({f"{h['source']} > {h['section']}" for h in hits}))
    return (
        "AI triage (draft, needs human review)\n"
        f"Category: {t.category.value} | Priority: {t.priority.value}\n"
        f"Summary: {t.summary}\nNext action: {t.next_action}\n"
        f"Draft reply: {t.draft_reply}\nPolicy used: {sources}"
    )


def already_triaged(ticket_id: int) -> bool:
    """True if an AI note is already on the ticket, so re-runs do not pile up duplicates."""
    found = odoo.search_read(
        "mail.message",
        [("model", "=", "project.task"), ("res_id", "=", ticket_id), ("body", "ilike", AI_NOTE_MARKER)],
        ["id"],
        limit=1,
    )
    return bool(found)


def audit(ticket: dict, result: Triage, hits: list[dict], written: bool) -> None:
    """Append one JSON line per decision: who/what/when, for review and trend analysis."""
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": os.getenv("LLM_PROVIDER", "groq"),
        "ticket_id": ticket["id"],
        "result": result.model_dump(mode="json"),
        "sources": sorted({f"{h['source']} > {h['section']}" for h in hits}),
        "written_to_odoo": written,
    }
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="post notes to Odoo (default: dry run)")
    parser.add_argument("--force", action="store_true", help="also re-triage tickets that already have an AI note")
    args = parser.parse_args()
    for summary in list_tickets("open"):
        ticket = get_ticket(summary["id"])
        if not args.force and already_triaged(ticket["id"]):
            print(f"#{ticket['id']} {ticket['subject']}\n  skipped: already has an AI note (use --force to redo)")
            continue
        result, hits = triage_ticket(ticket)
        print(f"#{ticket['id']} {ticket['subject']}\n  -> {result.category.value}/{result.priority.value}: {result.summary}\n     next: {result.next_action}")
        print("     policy:", "; ".join(sorted({f"{h['source']} > {h['section']}" for h in hits})))
        if args.write:
            add_ticket_note(ticket["id"], format_note(result, hits))
            print("     (note written to Odoo)")
        audit(ticket, result, hits, written=args.write)


if __name__ == "__main__":
    main()
