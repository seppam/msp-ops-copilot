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


def by(steps, action):
    return next((s for s in steps if s["action"] == action), None)


def test_every_ticket_gets_a_pic_and_one_formal_email():
    for p, flags in [(pred(), []), (pred(handover="needs_human", resolution_path="escalate"), []), (pred(missing_info=["pesan_error"]), [])]:
        steps = actions.plan(T, p, flags)
        assert kinds(steps).count("assign_pic") == 1 and kinds(steps).count("send_requester_email") == 1


def test_the_system_never_contacts_the_team_leader_itself():
    cases = [(pred(priority="P1"), []), (pred(handover="project"), []), (pred(handover="route_comsec", resolution_path="route"), []),
             (pred(handover="needs_human", resolution_path="escalate"), ["delete_request"])]
    for p, flags in cases:
        assert "notify_team_leader" not in kinds(actions.plan(T, p, flags))


def test_tickets_are_assigned_straight_to_the_right_team():
    for handover, team in [("route_comsec", "comsec PIC"), ("route_network", "network PIC"), ("route_change_request", "business team PIC"), ("route_request", "ops PIC"), ("team", "ops PIC")]:
        assert by(actions.plan(T, pred(handover=handover, resolution_path="route"), []), "assign_pic")["target"].startswith(team)


def test_escalation_cases_stay_with_the_ops_pic_who_decides():
    for p, flags in [(pred(priority="P1"), []), (pred(handover="project"), []), (pred(handover="needs_human", resolution_path="escalate"), ["delete_request"])]:
        steps = actions.plan(T, p, flags)
        assert by(steps, "assign_pic")["target"] == actions.PIC  # no team of its own: ops handles it first
        assert by(steps, "flag_for_pic")["target"] == actions.PIC  # the ops PIC is always the one to escalate


def test_escalation_candidates_are_flagged_to_the_pic_who_decides():
    flag = by(actions.plan(T, pred(priority="P1"), []), "flag_for_pic")
    assert "escalate to the Team Leader" in flag["why"]


def test_missing_information_is_asked_automatically_in_the_same_email():
    steps = actions.plan(T, pred(missing_info=["pesan_error"]), [])
    email = by(steps, "send_requester_email")
    assert email["missing"] == ["pesan_error"] and email["auto"] and not email["needs_approval"]


def test_complete_ticket_gets_no_questions():
    assert by(actions.plan(T, pred(), []), "send_requester_email")["missing"] == []


def test_form_gaps_are_asked_even_if_the_model_missed_them():
    assert by(actions.plan(T, pred(), [], form_missing=["user_terdampak"]), "send_requester_email")["missing"] == ["user_terdampak"]


def test_vague_outage_report_starts_with_availability_then_network_checks():
    vague = pred(priority="unknown", handover="needs_info", resolution_path="ask_user",
                 missing_info=["langkah_reproduksi", "contoh_record", "pesan_error", "waktu_mulai", "user_terdampak"])
    assign = by(actions.plan(T, vague, []), "assign_pic")
    assert "ketersediaan sistem" in assign["checklist"][0] and "jaringan" in assign["checklist"][1] and "tim jaringan" in assign["checklist"][2]


def test_dangerous_cases_get_acknowledgement_only_and_no_questions():
    for p, flags in [(pred(handover="needs_human", resolution_path="escalate", missing_info=["pesan_error"]), []), (pred(missing_info=["pesan_error"]), ["delete_request"]), (pred(), ["possible_injection"])]:
        steps = actions.plan(T, p, flags)
        assert by(steps, "send_requester_email")["missing"] == []
        assert "No data change without the Team Leader" in by(steps, "flag_for_pic")["why"]
        assert "draft_workaround_for_pic" not in kinds(steps)


def test_confirmation_without_a_missing_item_is_left_to_the_pic():
    steps = actions.plan(T, pred(handover="review", resolution_path="ask_user"), [])
    assert not any(s.get("confirm_directly") for s in steps)  # review flag comes first; escalation candidate wins
    steps = actions.plan(T, pred(handover="team", resolution_path="ask_user"), [])
    flag = by(steps, "flag_for_pic")
    assert flag["confirm_directly"] and "directly" in flag["why"] and "draft_ask_back_email" not in kinds(steps)


def test_workaround_draft_only_when_documented_knowledge_exists():
    p = pred(resolution_path="workaround")
    assert "draft_workaround_for_pic" not in kinds(actions.plan(T, p, [], has_playbook=False))
    assert "draft_workaround_for_pic" in kinds(actions.plan(T, p, [], has_playbook=True))


def test_playbook_detection_uses_impact_matrix_sections_only():
    docs = [{"source": "impact-matrix.md", "text": "Ada workaround kirim PDF manual"}]
    assert actions.has_documented_workaround(docs)
    assert not actions.has_documented_workaround([{"source": "sla-priority.md", "text": "ada workaround mudah"}])
    assert not actions.has_documented_workaround([{"source": "impact-matrix.md", "text": "Dampak Tinggi"}])


def test_ai_failure_falls_back_to_the_manual_queue():
    steps = actions.plan_on_failure(T, "RateLimitError")
    assert kinds(steps) == ["assign_pic", "notify_ops_lead"] and "ops queue" in steps[0]["target"]


def test_template_suggestions_appear_only_after_a_pattern_repeats():
    from msp_ops_copilot.template_insights import insights
    t = lambda i: {"id": i, "app": "Inventory", "menu": "Deliveries"}
    p = lambda **kw: {**dict(missing_info=[], handover="team", resolution_path="fix_now"), **kw}
    two = insights([t("a"), t("b")], {"a": p(missing_info=["pesan_error"]), "b": p(missing_info=["pesan_error"])}, threshold=3)
    assert two == []
    three = insights([t("a"), t("b"), t("c")], {i: p(missing_info=["pesan_error"]) for i in "abc"}, threshold=3)
    assert any("'pesan_error' was missing in 3 tickets" in s for s in three)
    confirm = insights([t("a"), t("b"), t("c")], {i: p(resolution_path="ask_user") for i in "abc"}, threshold=3)
    assert any("confirm something directly in 3 tickets" in s for s in confirm)
