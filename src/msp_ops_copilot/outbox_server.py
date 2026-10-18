"""Local HTTP bridge for n8n: GET /pending lists queued emails, POST /sent/<id> confirms one was sent.

On confirmation it adds a note to the Odoo ticket, so the ticket itself records that the requester was emailed.
Bound to localhost only. Start it only while testing: uv run python -m msp_ops_copilot.outbox_server
"""

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from msp_ops_copilot import outbox
from msp_ops_copilot.mcp_server import add_ticket_note

PORT = 8787


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/pending":
            return self._send(200, outbox.pending())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        match = re.fullmatch(r"/sent/([A-Za-z0-9_-]+)", self.path)
        item = outbox.mark_sent(match.group(1)) if match else None
        if not item:
            return self._send(404, {"error": "unknown outbox item"})
        add_ticket_note(item["odoo_id"], f"Email sent to requester ({item['to']}): {item['subject']}")
        self._send(200, {"ok": True, "id": item["id"]})

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


if __name__ == "__main__":
    print(f"outbox server on http://127.0.0.1:{PORT} (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
