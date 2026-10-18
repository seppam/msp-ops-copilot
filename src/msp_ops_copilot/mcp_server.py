"""Step 4: a custom MCP server that exposes Odoo to any MCP client.

An MCP client (Claude Code, Claude Desktop, our own agent) starts this
process, asks it "what tools do you have?", and calls them. The tools below
are the *entire* surface the AI can touch: three reads and one narrowly
scoped write. There is deliberately no delete or free-form update tool.
"""

import html
import logging
import os
import re

from mcp.server.mcpserver import MCPServer

from msp_ops_copilot import odoo_client as odoo

mcp = MCPServer("msp-odoo")
# MCPServer configures logging on creation, so quiet the HTTP libraries after it.
for _name in ("httpx", "httpx2"):
    logging.getLogger(_name).setLevel(logging.WARNING)

STATE_LABELS = {
    "01_in_progress": "open",
    "02_changes_requested": "open",
    "03_approved": "open",
    "04_waiting_normal": "open",
    "1_done": "closed",
    "1_canceled": "closed",
}
CLOSED_STATES = [s for s, label in STATE_LABELS.items() if label == "closed"]
PROJECTS = [name.strip() for name in os.getenv("ODOO_TICKET_PROJECTS", "Service Desk,App Support").split(",")]
SERVICE_DESK = ("project_id.name", "in", PROJECTS)  # the only projects the AI may read or annotate


def _plain(html: str | bool) -> str:
    """Odoo stores descriptions as HTML; the model only needs the text."""
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def _ticket(task: dict) -> dict:
    ticket = {
        "id": task["id"],
        "subject": task["name"],
        "customer": task["partner_id"][1] if task["partner_id"] else None,
        "status": STATE_LABELS.get(task["state"], task["state"]),
    }
    if "description" in task:  # only present when fetched (get_ticket)
        ticket["description"] = _plain(task["description"])
    return ticket


@mcp.tool()
def list_tickets(status: str = "open", customer: str = "") -> list[dict]:
    """List service-desk tickets. status is 'open' or 'closed'; customer is an optional name filter."""
    if status not in ("open", "closed"):
        raise ValueError("status must be 'open' or 'closed'")
    domain = [SERVICE_DESK, ("state", "in" if status == "closed" else "not in", CLOSED_STATES)]
    if customer:
        domain.append(("partner_id.name", "ilike", customer))
    fields = ["name", "partner_id", "state"]
    return [_ticket(t) for t in odoo.search_read("project.task", domain, fields)]


@mcp.tool()
def get_ticket(ticket_id: int) -> dict:
    """Get one ticket with its full description."""
    domain = [SERVICE_DESK, ("id", "=", ticket_id)]
    found = odoo.search_read("project.task", domain, ["name", "partner_id", "state", "description"], limit=1)
    return _ticket(found[0]) if found else {"error": f"ticket {ticket_id} not found"}


@mcp.tool()
def list_leads(customer: str = "") -> list[dict]:
    """List sales opportunities from the CRM, optionally filtered by customer name."""
    domain = [("partner_id.name", "ilike", customer)] if customer else []
    leads = odoo.search_read("crm.lead", domain, ["name", "partner_id", "expected_revenue", "stage_id"])
    return [
        {
            "id": lead["id"],
            "title": lead["name"],
            "customer": lead["partner_id"][1] if lead["partner_id"] else None,
            "expected_revenue": lead["expected_revenue"],
            "stage": lead["stage_id"][1] if lead["stage_id"] else None,
        }
        for lead in leads
    ]


@mcp.tool()
def add_ticket_note(ticket_id: int, note: str) -> dict:
    """Add an internal plain-text note to a ticket. Cannot change status or delete anything."""
    if not get_ticket(ticket_id).get("subject"):
        return {"error": f"ticket {ticket_id} not found"}
    odoo.call(
        "project.task", "message_post",
        ids=[ticket_id], message_type="comment", subtype_xmlid="mail.mt_note",
        # Escape first so text from a model can never inject markup, then keep line breaks.
        body=html.escape(note).replace("\n", "<br/>"), body_is_html=True,
    )
    return {"ok": True, "ticket_id": ticket_id}


if __name__ == "__main__":
    mcp.run()  # stdio transport: the client launches this process directly
