"""Triage v2 on live Odoo tickets (project "App Support"): recommend, plan actions, optionally annotate.

Dry run by default. With --write it adds ONE internal note per ticket (recommendation + planned steps) and
skips tickets that already have an AI note. It never sends email, assigns, or changes ticket data:
the plan is for the ops team to approve (see docs/WORKFLOW.md).
"""

import argparse

from msp_ops_copilot import actions, intake, triage2
from msp_ops_copilot import odoo_client as odoo
from msp_ops_copilot.mcp_server import add_ticket_note
from msp_ops_copilot.triage import AI_NOTE_MARKER, already_triaged

PROJECT = "App Support"


def clean(value: str) -> str:
    return "" if value.strip() == "-" else value.strip()


def load_tickets() -> list[dict]:
    tasks = odoo.search_read("project.task", [("project_id.name", "=", PROJECT)], ["name", "description"], limit=200)
    tickets = []
    for task in tasks:
        f = intake.parse(task["description"])
        tickets.append({
            "odoo_id": task["id"], "id": f.get("id_uji", f"#{task['id']}"), "submitted_at": f.get("tanggal", ""),
            "category": f.get("kategori", ""), "app": clean(f.get("aplikasi", "")), "menu": clean(f.get("menu", "")),
            "label_by_ops": f.get("label_ops", ""), "subject": "" if task["name"] == "(tanpa judul)" else task["name"],
            "description": clean(f.get("deskripsi", "")), "screenshot_note": clean(f.get("pesan_error", "")), "form": f,
        })
    return sorted(tickets, key=lambda t: (t["submitted_at"], t["id"]))


def note_text(pred, steps: list[dict], flags: list[str]) -> str:
    lines = [f"{AI_NOTE_MARKER}, needs human review)",
             f"Type: {pred.type} | Priority: {pred.priority} | Handover: {pred.handover} | Path: {pred.resolution_path}",
             f"Missing: {', '.join(pred.missing_info) or '-'}"]
    if pred.duplicate_of or pred.related_change:
        lines.append(f"Possible duplicate of: {pred.duplicate_of or '-'} | Related change: {pred.related_change or '-'}")
    if flags:
        lines.append(f"Safety flags: {', '.join(flags)}")
    lines.append(f"Reason: {pred.reason}")
    lines.append("Planned steps (nothing has been sent or assigned):")
    lines += [f"- {s['action']} -> {s['target']} [{'automatic' if s['auto'] else 'needs approval'}]" for s in steps]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", help="comma-separated test ids, e.g. T01,T29")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--write", action="store_true", help="add an internal note to each ticket (default: dry run)")
    args = ap.parse_args()
    everything = load_tickets()
    chosen = [t for t in everything if not args.ids or t["id"] in args.ids.split(",")][: args.limit]
    stats = triage2.new_stats()
    for t in chosen:
        if args.write and already_triaged(t["odoo_id"]):
            print(f"{t['id']} skipped: already has an AI note")
            continue
        earlier = [e for e in everything if (e["submitted_at"], e["id"]) < (t["submitted_at"], t["id"])]
        seen = len(stats["guard_flags"])
        try:
            pred = triage2.triage(t, earlier, stats)
            flags = [f.split(":", 1)[1] for f in stats["guard_flags"][seen:]]
            steps = actions.plan(t, pred, flags)  # legacy free-text tickets have no structured form fields to check
            text = note_text(pred, steps, flags)
        except Exception as exc:  # fail open: the ticket stays in the normal manual queue
            steps = actions.plan_on_failure(t, exc.__class__.__name__)
            text = f"{AI_NOTE_MARKER}, FAILED)\nAI step failed ({exc.__class__.__name__}). Ticket stays in the manual queue.\n" + "\n".join(f"- {s['action']} -> {s['target']}" for s in steps)
        print(f"--- {t['id']} {t['subject'] or '(tanpa judul)'}\n{text}")
        if args.write:
            add_ticket_note(t["odoo_id"], text)
    print(f"\ntokens: {stats['prompt_tokens']} in / {stats['completion_tokens']} out, calls {stats['calls']}, 429 retries {stats['retries']}")


if __name__ == "__main__":
    main()
