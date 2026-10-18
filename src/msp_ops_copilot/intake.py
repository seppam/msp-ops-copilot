"""The ticket submission template: render a ticket into Odoo's description, parse it back, check completeness.

The form makes the requester pick category/application/menu from lists and fill labelled fields.
A rendered ticket is plain "Label: value" lines, so the same text is readable by people, parseable by code
and visible to the model. Completeness is checked by deterministic rules first (free, instant);
the model is only needed for judgement.
"""

import html
import re

LABELS = {
    "id_uji": "ID uji",
    "tanggal": "Tanggal",
    "kategori": "Kategori",
    "aplikasi": "Aplikasi",
    "menu": "Menu",
    "label_ops": "Label ops",
    "deskripsi": "Deskripsi masalah",
    "langkah_reproduksi": "Langkah reproduksi",
    "contoh_record": "Contoh nomor dokumen",
    "pesan_error": "Pesan error atau screenshot",
    "waktu_mulai": "Waktu mulai",
    "user_terdampak": "User terdampak",
    "tenggat": "Tenggat bisnis",
}
# What a complete submission must contain, by category the requester picked.
REQUIRED = {
    "app": ["deskripsi", "langkah_reproduksi", "contoh_record", "pesan_error", "waktu_mulai", "user_terdampak"],
    "network": ["deskripsi", "waktu_mulai", "user_terdampak"],
    "other": ["deskripsi"],
}
EMPTY = {"", "-", "?", "n/a", "na", "tidak tahu", "belum tahu", "ga tau", "gak tau"}
# Fields whose absence maps to the model's missing_info vocabulary
VOCAB = {"langkah_reproduksi", "contoh_record", "pesan_error", "waktu_mulai", "user_terdampak"}


def render(fields: dict[str, str]) -> str:
    """Fields -> HTML for the Odoo task description (values escaped)."""
    return "<p>" + "<br/>".join(f"{LABELS[k]}: {html.escape(str(v))}" for k, v in fields.items() if k in LABELS) + "</p>"


def parse(description_html: str) -> dict[str, str]:
    text = re.sub(r"<br\s*/?>|</p>|<p>", "\n", description_html or "")
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    by_label = {label: key for key, label in LABELS.items()}
    out = {}
    for line in text.splitlines():
        label, _, value = line.partition(": ")
        if label.strip() in by_label:
            out[by_label[label.strip()]] = value.strip()
    return out


def missing_fields(fields: dict[str, str]) -> list[str]:
    """Required fields that are absent or filled with a non-answer, in the model's vocabulary."""
    required = REQUIRED.get(fields.get("kategori", "app"), REQUIRED["app"])
    return [k for k in required if k in VOCAB and fields.get(k, "").strip().lower() in EMPTY]
