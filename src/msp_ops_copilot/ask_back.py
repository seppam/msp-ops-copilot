"""Draft the confirmation email asking a requester for missing information.

Deterministic template (no LLM, no tokens): the wording is controlled by the ops team, the model only
decides WHICH items are missing. A human reviews the draft before anything is sent.
"""

ITEMS = {
    "langkah_reproduksi": "Langkah-langkah yang dilakukan hingga masalah muncul",
    "contoh_record": "Contoh nomor dokumen atau record yang terdampak (misalnya nomor invoice atau delivery order)",
    "pesan_error": "Pesan error yang muncul, atau screenshot layar",
    "waktu_mulai": "Kapan masalah ini mulai terjadi",
    "user_terdampak": "Siapa saja pengguna yang terdampak (satu orang atau banyak)",
}


def draft_ask_back(ticket: dict, missing_info: list[str]) -> dict:
    subject = f"[Tiket {ticket['id']}] Mohon informasi tambahan: {ticket['subject'] or 'laporan Anda'}"
    lines = "\n".join(f"{n}. {ITEMS[m]}" for n, m in enumerate(missing_info, 1))
    body = (
        "Yth. Bapak/Ibu,\n\n"
        f"Terima kasih atas laporan Anda ({ticket['subject'] or 'tanpa judul'}). "
        "Agar kami dapat segera menindaklanjuti, mohon lengkapi informasi berikut:\n\n"
        f"{lines}\n\n"
        "Cukup balas email ini. Setelah informasi lengkap, tim kami akan langsung menangani tiket Anda.\n\n"
        "Terima kasih,\nTim Application Support"
    )
    return {"subject": subject, "body": body}
