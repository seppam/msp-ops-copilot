"""Load the demo customers, service-desk tickets and sales leads into Odoo.

Safe to run twice: it looks up each record by name before creating it.
"""

import json

from msp_ops_copilot.odoo_client import create, search_read
from msp_ops_copilot.tools import TICKETS_FILE

PROJECT = "Service Desk"

LEADS = [
    ("Acme Logistics", "Managed backup renewal", 12000),
    ("Borneo Coffee", "Email security upgrade", 4500),
    ("Cahaya Dental", "Server storage expansion", 8000),
]


def get_or_create(model: str, name: str, extra: dict | None = None) -> int:
    found = search_read(model, [("name", "=", name)], ["id"], limit=1)
    if found:
        return found[0]["id"]
    return create(model, {"name": name, **(extra or {})})


def main() -> None:
    tickets = json.loads(TICKETS_FILE.read_text())
    project_id = get_or_create("project.project", PROJECT)
    partners = {}
    for t in tickets:
        partners.setdefault(t["customer"], get_or_create("res.partner", t["customer"], {"is_company": True}))

    for t in tickets:
        name = t["subject"]
        if search_read("project.task", [("name", "=", name)], ["id"], limit=1):
            continue
        create("project.task", {
            "name": name,
            "description": f"<p>{t['body']}</p>",
            "project_id": project_id,
            "partner_id": partners[t["customer"]],
            "state": "1_done" if t["status"] == "closed" else "01_in_progress",
        })
    for customer, title, revenue in LEADS:
        get_or_create("crm.lead", title, {"partner_id": partners[customer], "expected_revenue": revenue, "type": "opportunity"})

    tasks = search_read("project.task", [("project_id", "=", project_id)], ["name", "state", "partner_id"])
    print(f"{len(partners)} customers, {len(tasks)} tasks in '{PROJECT}', {len(LEADS)} leads")
    for task in tasks:
        print(f"  #{task['id']} [{task['state']}] {task['partner_id'][1]}: {task['name']}")


if __name__ == "__main__":
    main()
