"""Decide what should happen after triage. Pure function: nothing is sent or changed here.

Rules (phase 1):
  * Every ticket is assigned straight to the right team's PIC (person in charge): ops by default, comsec,
    network or the business team when the triage says so. Anything that needs ESCALATION (P1, review, project
    handover, dangerous cases) always goes through the OPS PIC, who decides whether to involve the Team Leader
    or the project team. The system never contacts the Team Leader or the project team itself.
  * The requester gets ONE formal email: the ticket is in the system, here is the PIC, wait for the PIC's follow-up.
    If information is missing it is asked in the same email, automatically. Complete tickets get no questions.
  * Dangerous cases (needs_human, escalate, delete request, injection): acknowledgement only, no questions,
    and the PIC is told not to change any data without the Team Leader's approval.
  * Drafts (e.g. workaround message) are produced only when documented knowledge exists. Otherwise the PIC
    handles it directly, which also saves LLM calls.
  * If the AI fails, the ticket still goes to the manual ops queue and the ops lead is alerted.
"""

import re

PIC = "ops PIC (on duty)"
TEAM_PICS = {  # who receives the ticket for each routing outcome (placeholders for an on-duty rotation)
    "route_comsec": "comsec PIC (on duty)",
    "route_network": "network PIC (on duty)",
    "route_change_request": "business team PIC (change requests)",
    "route_request": PIC,
}
# For vague reports ("everything is broken") the PIC starts here, without waiting for the requester.
FIRST_CHECKS = [
    "Cek ketersediaan sistem: aplikasi dan database berjalan, tidak ada error massal",
    "Cek jaringan: apakah aplikasi bisa dijangkau dari lokasi pelapor dan dari lokasi lain",
    "Jika hanya lokasi pelapor yang gagal: eskalasi ke tim jaringan",
]


def step(action: str, target: str, why: str, checklist: list[str] | None = None, **extra) -> dict:
    out = {"action": action, "target": target, "why": why, "auto": True, "needs_approval": False, **extra}
    if checklist:
        out["checklist"] = checklist
    return out


def has_documented_workaround(rules: list[dict]) -> bool:
    """First, simple rule for 'the system has an advance evaluation': a retrieved impact-matrix section names a workaround."""
    return any(r["source"] == "impact-matrix.md" and re.search(r"workaround|alternatif", r["text"], re.I) for r in rules)


def plan(ticket: dict, pred, flags: list[str], form_missing: list[str] | None = None, pic: str = PIC, has_playbook: bool = False) -> list[dict]:
    missing = sorted(set(form_missing or []) | set(pred.missing_info))
    risky = pred.handover == "needs_human" or pred.resolution_path == "escalate" or any(f in ("delete_request", "possible_injection") for f in flags)
    vague = (pred.priority == "unknown" or len(missing) >= 3) and not risky
    ask = [] if risky else missing
    escalation = risky or pred.priority == "P1" or pred.handover in ("project", "review")
    target = pic if risky else TEAM_PICS.get(pred.handover, pic)
    steps = [
        step("assign_pic", target, "Assigned directly to the team the triage points to" if target != pic else "First check by the ops team; escalating is the PIC's decision",
             checklist=FIRST_CHECKS if vague else None),
        step("send_requester_email", "requester",
             "Formal acknowledgement naming the PIC; wait for the PIC's follow-up" + (f"; asks for: {', '.join(ask)}" if ask else ""),
             missing=ask),
    ]
    if risky:
        steps.append(step("flag_for_pic", pic, "Needs a human decision (" + (", ".join(flags) or pred.handover) + "). No data change without the Team Leader's approval; the PIC escalates if confirmed"))
    elif escalation:
        steps.append(step("flag_for_pic", pic, f"Escalation candidate ({pred.priority} / {pred.handover}): check first, then escalate to the Team Leader"))
    elif (pred.handover == "needs_info" or pred.resolution_path == "ask_user") and not missing:
        steps.append(step("flag_for_pic", pic, "Confirm directly with the requester (no template question for this yet)", confirm_directly=True))
    if not risky and pred.resolution_path == "workaround" and has_playbook:
        steps.append(step("draft_workaround_for_pic", pic, "Documented workaround found: draft for the PIC to review and send. Not sent automatically"))
    return steps


def plan_on_failure(ticket: dict, error: str) -> list[dict]:
    """AI unavailable or its answer was unusable: do the manual process and tell someone."""
    return [
        step("assign_pic", "ops queue (default)", "Normal manual intake, no AI recommendation"),
        step("notify_ops_lead", "ops lead", f"AI step failed: {error}"),
    ]
