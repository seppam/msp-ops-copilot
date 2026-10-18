import json
import threading
from http.client import HTTPConnection
from http.server import HTTPServer

from msp_ops_copilot import outbox, outbox_server


def test_one_email_per_ticket_and_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(outbox, "OUTBOX", tmp_path / "ob")
    assert outbox.enqueue("T01", 5, "a@example.test", "subj", "body") is True
    assert outbox.enqueue("T01", 5, "a@example.test", "other", "other") is False  # re-running never duplicates
    assert [i["id"] for i in outbox.pending()] == ["T01"]
    assert outbox.mark_sent("T01")["status"] == "sent" and outbox.pending() == []
    assert outbox.mark_sent("nope") is None


def test_server_lists_pending_and_records_the_send_in_odoo(tmp_path, monkeypatch):
    monkeypatch.setattr(outbox, "OUTBOX", tmp_path / "ob")
    notes = []
    monkeypatch.setattr(outbox_server, "add_ticket_note", lambda odoo_id, text: notes.append((odoo_id, text)))
    outbox.enqueue("T02", 9, "b@example.test", "Hello", "body")
    server = HTTPServer(("127.0.0.1", 0), outbox_server.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    conn = HTTPConnection("127.0.0.1", server.server_port)
    conn.request("GET", "/pending"); assert json.loads(conn.getresponse().read())[0]["to"] == "b@example.test"
    conn.request("POST", "/sent/T02"); assert json.loads(conn.getresponse().read())["ok"]
    conn.request("POST", "/sent/missing"); assert conn.getresponse().status == 404
    server.shutdown()
    assert notes == [(9, "Email sent to requester (b@example.test): Hello")]
