from msp_ops_copilot import actions, intake, triage_odoo
from msp_ops_copilot.triage2 import Triage2


def test_note_carries_the_marker_so_reruns_skip_it():
    pred = Triage2(type="bug", priority="P3", handover="team", resolution_path="workaround", reason="alasan")
    steps = actions.plan({"id": "T1"}, pred, [])
    text = triage_odoo.note_text(pred, steps, ["delete_request"])
    assert text.startswith(triage_odoo.AI_NOTE_MARKER) and "nothing has been sent or assigned" in text
    assert "Safety flags: delete_request" in text


def test_load_tickets_parses_the_template_and_hides_placeholders(monkeypatch):
    html_text = intake.render({"id_uji": "T30", "tanggal": "2026-10-15", "kategori": "app", "aplikasi": "Accounting",
                               "menu": "-", "label_ops": "bug", "deskripsi": "-", "pesan_error": "Access Denied"})
    monkeypatch.setattr(triage_odoo.odoo, "search_read", lambda *a, **k: [{"id": 36, "name": "(tanpa judul)", "description": html_text}])
    t = triage_odoo.load_tickets()[0]
    assert t["id"] == "T30" and t["subject"] == "" and t["description"] == "" and t["menu"] == ""
    assert t["screenshot_note"] == "Access Denied" and t["odoo_id"] == 36
