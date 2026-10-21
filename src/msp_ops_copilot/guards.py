"""Deterministic safety checks applied AFTER the model answers.

A prompt can be ignored or talked around by ticket text. Code cannot. These rules are narrow on purpose:
they only fire on clear patterns and only change the fields that make an unsafe outcome possible.
"""

import re

from msp_ops_copilot.triage2 import Triage2

# "tolong hapus ...", "please delete ...", "hapus semua ..."
DELETE_REQUEST = re.compile(
    r"\b(tolong|mohon|minta|harap|please|pls)\b[^.!?\n]{0,30}?\b(hapus|menghapus|delete|drop|truncate|wipe)\b"
    r"|\b(hapus|delete|drop|truncate|wipe)\s+(semua|seluruh|all)\b",
    re.I,
)
# Not a request: a bug report or how-to about the delete feature itself
NOT_A_REQUEST = re.compile(
    r"(tombol|button|menu|fitur|opsi|icon)\s+(hapus|delete)|"
    r"(tidak bisa|gagal|error|cannot|can't|cant|unable)[^.!?\n]{0,15}(hapus|menghapus|delete)|"
    r"\bcara\b[^.!?\n]{0,10}\b(hapus|delete)",
    re.I,
)
INJECTION = re.compile(
    r"abaikan\s+(semua\s+)?(aturan|instruksi|perintah)|"
    r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(rules|instructions)|"
    r"(tandai|set|mark)\b[^.!?\n]{0,25}\bP[1-4]\b|"
    r"kirim\s+email\s+ke\s+semua|system\s+prompt|you\s+are\s+now|kamu\s+sekarang",
    re.I,
)
VAGUE_MISSING = 4  # this many missing items means impact cannot be judged from the ticket
DEMANDS_HIGH_PRIORITY = re.compile(r"\bP[12]\b|prioritas\s+(tinggi|utama)|urgent", re.I)


def apply_guards(ticket: dict, pred: Triage2) -> tuple[Triage2, list[str]]:
    text = f"{ticket['subject']}. {ticket['description']}"
    flags, changes = [], {}
    if DELETE_REQUEST.search(text) and not NOT_A_REQUEST.search(text):
        flags.append("delete_request")
        changes.update(handover="needs_human", resolution_path="escalate")
    if INJECTION.search(text):
        flags.append("possible_injection")
        if pred.priority in ("P1", "P2") and DEMANDS_HIGH_PRIORITY.search(text):
            changes["priority"] = "unknown"  # do not trust a priority the ticket itself demands
    if len(pred.missing_info) >= VAGUE_MISSING and pred.priority in ("P1", "P2"):
        # A report that lacks nearly everything cannot justify a high priority from its wording alone ("URGENT!!!").
        # The PIC still starts first checks at once (see actions.FIRST_CHECKS), so nothing waits.
        flags.append("vague_priority")
        changes["priority"] = "unknown"
    changes = {k: v for k, v in changes.items() if getattr(pred, k) != v}
    return (pred.model_copy(update=changes) if changes else pred), flags + [f"override:{k}" for k in changes]
