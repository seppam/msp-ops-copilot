import json

import pytest
from pydantic import ValidationError

from msp_ops_copilot import triage
from tests.conftest import text_reply

TICKET = {"id": 7, "subject": "VPN down", "description": "Cannot connect", "customer": "Acme", "status": "open"}
GOOD = {"category": "network", "priority": "high", "summary": "VPN down", "draft_reply": "Hi", "next_action": "Check logs"}


@pytest.fixture(autouse=True)
def no_retrieval(monkeypatch):
    monkeypatch.setattr(triage, "policy_for", lambda ticket: [{"source": "p.md", "section": "S", "text": "t", "distance": 0.1}])


def test_schema_rejects_priority_outside_the_list():
    with pytest.raises(ValidationError):
        triage.Triage(**{**GOOD, "priority": "urgent!!"})


def test_valid_reply_is_parsed(fake_llm):
    fake_llm([text_reply(json.dumps(GOOD))], triage)
    result, hits = triage.triage_ticket(TICKET)
    assert result.priority is triage.Priority.high and hits[0]["source"] == "p.md"


def test_invalid_reply_is_retried_once_with_the_error_shown(fake_llm):
    llm = fake_llm([text_reply(json.dumps({**GOOD, "priority": "urgent!!"})), text_reply(json.dumps(GOOD))], triage)
    result, _ = triage.triage_ticket(TICKET)
    assert result.priority is triage.Priority.high
    assert len(llm.calls) == 2
    assert "Invalid" in llm.calls[1]["messages"][-1]["content"]


def test_gives_up_after_the_retry_cap(fake_llm):
    bad = text_reply("not json at all")
    llm = fake_llm([bad, bad, bad], triage)
    with pytest.raises(ValidationError):
        triage.triage_ticket(TICKET)
    assert len(llm.calls) == 2  # first try + one retry, never a loop


def test_note_lists_sources_from_retrieval_not_from_the_model():
    note = triage.format_note(triage.Triage(**GOOD), [{"source": "runbook-vpn.md", "section": "Auth"}])
    assert "Policy used: runbook-vpn.md > Auth" in note and note.startswith(triage.AI_NOTE_MARKER)


def test_already_triaged_looks_for_the_marker(monkeypatch):
    seen = {}

    def fake_search_read(model, domain, fields, limit=50):
        seen["domain"] = domain
        return [{"id": 1}]

    monkeypatch.setattr(triage.odoo, "search_read", fake_search_read)
    assert triage.already_triaged(7) is True
    assert ("res_id", "=", 7) in seen["domain"]
