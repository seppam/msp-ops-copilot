import json

from msp_ops_copilot import agent_basic, mcp_server
from tests.conftest import text_reply, tool_reply


def test_unknown_tool_is_reported_back_to_the_model_not_a_crash(fake_llm):
    llm = fake_llm([tool_reply("delete_ticket", '{"ticket_id": 1}'), text_reply("Sorry, I cannot do that.")], agent_basic)
    answer = agent_basic.run("delete ticket 1")
    assert answer == "Sorry, I cannot do that."
    tool_message = llm.calls[1]["messages"][-1]
    assert tool_message["role"] == "tool" and "unknown tool" in json.loads(tool_message["content"])["error"]


def test_bad_arguments_are_reported_back(fake_llm):
    llm = fake_llm([tool_reply("get_ticket", "{not json"), text_reply("ok")], agent_basic)
    agent_basic.run("x")
    assert "error" in json.loads(llm.calls[1]["messages"][-1]["content"])


def test_loop_stops_at_max_steps(fake_llm):
    fake_llm([tool_reply("list_tickets") for _ in range(agent_basic.MAX_STEPS)], agent_basic)
    assert "too many" in agent_basic.run("loop forever")


def test_note_text_is_escaped_before_it_reaches_odoo(monkeypatch):
    sent = {}
    monkeypatch.setattr(mcp_server, "get_ticket", lambda tid: {"subject": "exists"})
    monkeypatch.setattr(mcp_server.odoo, "call", lambda model, method, **kw: sent.update(kw))
    mcp_server.add_ticket_note(2, "<script>alert(1)</script>\nsecond line")
    assert "<script>" not in sent["body"] and "&lt;script&gt;" in sent["body"] and "<br/>" in sent["body"]


def test_note_on_a_missing_ticket_writes_nothing(monkeypatch):
    called = []
    monkeypatch.setattr(mcp_server, "get_ticket", lambda tid: {"error": "not found"})
    monkeypatch.setattr(mcp_server.odoo, "call", lambda *a, **k: called.append(1))
    assert "error" in mcp_server.add_ticket_note(99, "x") and not called


def test_list_tickets_rejects_unknown_status():
    import pytest
    with pytest.raises(ValueError):
        mcp_server.list_tickets("deleted")


def test_no_destructive_tool_is_registered():
    names = {t for t in dir(mcp_server) if not t.startswith("_")}
    assert not {"delete_ticket", "update_ticket", "unlink"} & names
