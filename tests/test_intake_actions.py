from msp_ops_copilot import actions, intake
from msp_ops_copilot.triage2 import Triage2


def pred(**kw):
    base = dict(type="bug", priority="P3", handover="team", resolution_path="workaround", reason="x")
    return Triage2(**{**base, **kw})


T = {"id": "T99", "subject": "x", "description": "y"}


def kinds(steps):
    return [s["action"] for s in steps]


def test_render_then_parse_round_trips_and_escapes():
    fields = {"id_uji": "T01", "kategori": "app", "deskripsi": "Nominal <b>salah</b> & dobel", "pesan_error": "-"}
    html_text = intake.render(fields)
    assert "<b>salah" not in html_text
    assert intake.parse(html_text) == fields


def test_empty_answers_count_as_missing():
    form = {"kategori": "app", "deskripsi": "x", "langkah_reproduksi": "klik Validate", "contoh_record": "tidak tahu",
            "pesan_error": "-", "waktu_mulai": "kemarin", "user_terdampak": ""}
    assert intake.missing_fields(form) == ["contoh_record", "pesan_error", "user_terdampak"]


def test_requirements_depend_on_the_category():
    assert intake.missing_fields({"kategori": "other", "deskripsi": "minta akun"}) == []
    assert intake.missing_fields({"kategori": "network", "deskripsi": "wifi"}) == ["waktu_mulai", "user_terdampak"]


def test_every_ticket_gets_an_acknowledgement_first():
    assert kinds(actions.plan(T, pred(), []))[0] == "send_acknowledgement"


def test_dangerous_cases_only_notify_the_team_leader():
    for p, flags in [(pred(handover="needs_human", resolution_path="escalate"), []), (pred(), ["delete_request"]), (pred(), ["possible_injection"])]:
        steps = actions.plan(T, p, flags)
        assert kinds(steps) == ["send_acknowledgement", "notify_team_leader", "hold_ticket"]
        assert all(s["auto"] for s in steps)  # information only: nothing that changes data or promises anything


def test_missing_information_asks_and_assigns_in_parallel():
    steps = actions.plan(T, pred(missing_info=["pesan_error"]), [])
    assert {"draft_ask_back_email", "assign_to"} <= set(kinds(steps)) and "hold_assignment" not in kinds(steps)
    assert next(s for s in steps if s["action"] == "draft_ask_back_email")["needs_approval"]
    assert "checklist" not in next(s for s in steps if s["action"] == "assign_to")  # one gap: no first-check list needed


def test_vague_outage_report_starts_with_availability_then_network_checks():
    vague = pred(priority="unknown", handover="needs_info", resolution_path="ask_user",
                 missing_info=["langkah_reproduksi", "contoh_record", "pesan_error", "waktu_mulai", "user_terdampak"])
    assign = next(s for s in actions.plan(T, vague, []) if s["action"] == "assign_to")
    assert assign["target"] == "ops engineer" and assign["needs_approval"]
    assert "ketersediaan sistem" in assign["checklist"][0] and "jaringan" in assign["checklist"][1] and "tim jaringan" in assign["checklist"][2]


def test_form_gaps_trigger_ask_back_even_if_the_model_missed_them():
    assert "draft_ask_back_email" in kinds(actions.plan(T, pred(), [], form_missing=["user_terdampak"]))


def test_p1_alerts_the_leader_immediately():
    assert "notify_team_leader" in kinds(actions.plan(T, pred(priority="P1"), []))


def test_routing_to_comsec_needs_approval():
    steps = actions.plan(T, pred(handover="route_comsec", resolution_path="route"), [])
    assign = next(s for s in steps if s["action"] == "assign_to")
    assert assign["target"] == "comsec" and assign["needs_approval"]


def test_ai_failure_falls_back_to_the_manual_queue():
    steps = actions.plan_on_failure(T, "RateLimitError")
    assert kinds(steps) == ["assign_to", "notify_ops_lead"] and "ops queue" in steps[0]["target"]
