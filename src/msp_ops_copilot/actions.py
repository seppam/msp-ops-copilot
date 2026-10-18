"""Decide what should happen after triage: which steps automation may take and which need a human.

Pure function: (ticket, recommendation, guard flags) -> a plan. Nothing is sent or changed here, so the plan
can be reviewed, tested and later executed by n8n. Principles:
  * Anything touching business data, routing or customers' expectations needs a human to approve.
  * Information-only notices (acknowledgement, alert to the Team Leader) may be automatic.
  * Needs_human / escalate / injection / delete requests: no automation except telling the right person.
  * If the AI fails, the ticket falls back to the normal ops queue. Automation never blocks a ticket.
"""

ROUTE_TEAMS = {"route_comsec": "comsec", "route_network": "network team", "route_change_request": "business team (change request)", "route_request": "ops team (service request)"}


def step(action: str, target: str, why: str, auto: bool) -> dict:
    return {"action": action, "target": target, "why": why, "auto": auto, "needs_approval": not auto}


def plan(ticket: dict, pred, flags: list[str], form_missing: list[str] | None = None) -> list[dict]:
    steps = [step("send_acknowledgement", "requester", "Confirm receipt, no promises about timing or fix", auto=True)]
    missing = sorted(set(form_missing or []) | set(pred.missing_info))
    risky = pred.handover == "needs_human" or pred.resolution_path == "escalate" or any(f in ("delete_request", "possible_injection") for f in flags)
    if risky:
        steps.append(step("notify_team_leader", "team leader", "Needs a human decision: " + (", ".join(flags) or pred.handover), auto=True))
        steps.append(step("hold_ticket", "ops queue", "No automatic follow-up until the Team Leader decides", auto=True))
        return steps
    if pred.priority == "P1" or pred.handover in ("project", "review"):
        steps.append(step("notify_team_leader", "team leader", f"{pred.priority} / {pred.handover}: leader decides order or handover", auto=True))
    if pred.handover == "needs_info" or pred.resolution_path == "ask_user" or missing:
        steps.append(step("draft_ask_back_email", "requester", "Missing: " + (", ".join(missing) or "confirmation needed"), auto=False))
        steps.append(step("hold_assignment", "ops queue", "Wait for the requester's answer before assigning", auto=True))
        return steps
    if pred.handover in ROUTE_TEAMS:
        steps.append(step("assign_to", ROUTE_TEAMS[pred.handover], "Hand over with context pack", auto=False))
    else:
        steps.append(step("assign_to", "ops engineer", "Support team handles it", auto=False))
        if pred.resolution_path == "workaround":
            steps.append(step("draft_workaround_message", "requester", "Alternative business flow while the bug waits", auto=False))
    return steps


def plan_on_failure(ticket: dict, error: str) -> list[dict]:
    """AI unavailable or its answer was unusable: do the manual process and tell someone."""
    return [
        step("assign_to", "ops queue (default)", "Normal manual intake, no AI recommendation", auto=True),
        step("notify_ops_lead", "ops lead", f"AI step failed: {error}", auto=True),
    ]
