"""Load the golden tickets into Odoo as tasks of project "App Support", rendered with the intake template.

Idempotent (looks up each by its test id). The old "Service Desk" project is left untouched.
Labels are NOT written to Odoo: the AI must not see the answers.
"""

import csv

from msp_ops_copilot import intake
from msp_ops_copilot import odoo_client as odoo
from msp_ops_copilot.rag import ROOT

PROJECT = "App Support"


def main() -> None:
    found = odoo.search_read("project.project", [("name", "=", PROJECT)], ["id"], limit=1)
    project_id = found[0]["id"] if found else odoo.create("project.project", {"name": PROJECT})
    created = updated = 0
    for t in csv.DictReader(open(ROOT / "data" / "golden" / "tickets.csv", encoding="utf-8-sig")):
        marker = f"ID uji: {t['id']}<"  # '<' ends the value, so T01 never matches T010
        existing = odoo.search_read("project.task", [("project_id", "=", project_id), ("description", "ilike", marker)], ["id", "description"], limit=1)
        fields = {
            "id_uji": t["id"], "tanggal": t["submitted_at"], "email": f"pelapor.{t['id'].lower()}@example.test",  # fake: reserved test domain
            "kategori": t["category"], "aplikasi": t["app"] or "-",
            "menu": t["menu"] or "-", "label_ops": t["label_by_ops"], "deskripsi": t["description"] or "-",
            "pesan_error": t["screenshot_note"] or "-",
        }
        if existing:
            if "Email pelapor" not in existing[0]["description"]:  # older seed: add the fake email field
                odoo.call("project.task", "write", ids=[existing[0]["id"]], vals={"description": intake.render(fields)})
                updated += 1
            continue
        odoo.create("project.task", {"name": t["subject"] or "(tanpa judul)", "description": intake.render(fields), "project_id": project_id})
        created += 1
    total = len(odoo.search_read("project.task", [("project_id", "=", project_id)], ["id"], limit=200))
    print(f"created {created}, updated {updated}; '{PROJECT}' now has {total} tasks")


if __name__ == "__main__":
    main()
