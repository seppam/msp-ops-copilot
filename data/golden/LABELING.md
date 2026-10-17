# Panduan Review Label (golden set)

File: `tickets.csv` (buka dengan Numbers, Excel, atau editor teks). Kolom kiri adalah isi tiket. Kolom kanan adalah **label usulan dari AI yang belum tentu benar**. Tugas Anda: koreksi label sesuai praktik tim Anda, lalu isi `reviewed` dengan `y`.

| Kolom | Arti | Nilai |
|---|---|---|
| label_by_ops | jenis masalah yang ditetapkan tim ops saat menerima tiket (kolom kiri, bisa keliru) | bug, data |
| type | jenis masalah sebenarnya menurut Anda | bug, data, change_impact, request, other |
| priority | prioritas menurut dampak, urgensi, SLA | P1, P2, P3, P4, unknown (info belum cukup) |
| handover | siapa yang menangani | team, review, project, needs_info, needs_human, route_comsec, route_network, route_change_request, route_request |
| missing_info | info yang kurang, dipisah titik koma | langkah_reproduksi, contoh_record, pesan_error, waktu_mulai, user_terdampak |
| duplicate_of | id tiket yang sama dengan tiket ini | mis. T03 |
| related_change | perubahan di change-log.csv yang diduga penyebab | mis. CHG-02 |
| labeler_note | catatan alasan | bebas |

Arti `handover`: team = ditangani tim support sendiri; review = perlu review Team Leader atas usulan perbaikan; project = diserahkan ke tim proyek; needs_info = minta info tambahan dulu; needs_human = tidak boleh diproses otomatis; route_comsec = tindak lanjut ke tim keamanan dan hak akses; route_network = ke tim jaringan; route_change_request = harus diajukan tim bisnis sebagai change request; route_request = permintaan layanan atau pertanyaan cara pakai.

Yang paling penting dikoreksi:
1. Prioritas: apakah sesuai cara Team Leader Anda mengelompokkan masalah?
2. Tiket yang menurut Anda ambigu. Tulis alasannya di `labeler_note`. Tiket ambigu lebih berguna daripada yang jelas.
3. `data/kb_app/*.md` adalah draft aturan. Koreksi angka SLA dan dampak menu agar sesuai pengalaman Anda. Jangan memakai data rahasia perusahaan Anda. Pakai versi karangan atau yang sudah disamarkan.
