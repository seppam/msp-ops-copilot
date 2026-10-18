"""Formal email to the requester, from fixed templates (no LLM, no tokens).

The wording is controlled by the ops team. The model only decides WHICH items are missing.
One email per ticket: acknowledgement naming the PIC, plus the questions if something is missing.
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


def requester_email(ticket: dict, pic_name: str, missing_info: list[str]) -> dict:
    """Formal acknowledgement. No promise about timing or fix; tells the requester to wait for the PIC's email."""
    title = ticket["subject"] or "laporan Anda"
    body = (
        "Yth. Bapak/Ibu,\n\n"
        f"Laporan Anda ({title}) telah kami terima dan tercatat dengan nomor tiket {ticket['id']}. "
        f"Tiket ini telah ditugaskan kepada {pic_name}. Mohon menunggu email tindak lanjut dari PIC tersebut.\n"
    )
    if missing_info:
        lines = "\n".join(f"{n}. {ITEMS[m]}" for n, m in enumerate(missing_info, 1))
        body += (
            "\nAgar penanganan dapat segera dimulai, mohon lengkapi informasi berikut dengan membalas email ini. "
            "Jika informasi tersebut sudah Anda sampaikan, mohon abaikan permintaan ini:\n\n" + lines + "\n"
        )
    body += "\nTerima kasih,\nTim Application Support"
    return {"subject": f"[Tiket {ticket['id']}] Tiket Anda telah diterima, PIC: {pic_name}", "body": body}
