# Kebijakan Prioritas dan SLA Application Support (DRAFT - ganti dengan SLA perusahaan sebenarnya)

## Cara menentukan prioritas
Prioritas ditentukan dari dampak bisnis dan urgensi, lalu dicocokkan dengan SLA. Keputusan akhir ada di Team Leader.
- Dampak Tinggi: banyak pengguna atau satu proses utama terhenti (penagihan, pengiriman, closing, pajak), tidak ada workaround, atau ada risiko kepatuhan dan keamanan data.
- Dampak Sedang: satu tim terganggu atau ada workaround yang merepotkan.
- Dampak Rendah: satu pengguna, satu record, atau masalah tampilan, ada workaround mudah.
- Urgensi Tinggi: ada tenggat hari ini (pengiriman hari ini, closing bulan, audit). Urgensi Sedang: tenggat dalam beberapa hari. Urgensi Rendah: tidak ada tenggat.

## Matriks
Dampak Tinggi dan urgensi Tinggi atau Sedang adalah P1. Dampak Tinggi dengan urgensi Rendah, atau dampak Sedang dengan urgensi Tinggi, adalah P2. Dampak Sedang dengan urgensi Sedang, atau dampak Rendah dengan urgensi Tinggi, adalah P3. Sisanya P4.
Jika beberapa pengguna melaporkan masalah yang sama, dampak dinaikkan satu tingkat.

## Target SLA
- P1: respons 30 menit, penyelesaian atau workaround 4 jam kerja.
- P2: respons 1 jam, penyelesaian 8 jam kerja.
- P3: respons 4 jam kerja, penyelesaian 3 hari kerja.
- P4: respons 1 hari kerja, penyelesaian 10 hari kerja.

## Tiket yang informasinya belum cukup
Jangan menetapkan prioritas hanya karena pelapor menulis kata mendesak. Minta informasi tambahan lebih dulu: langkah reproduksi, contoh record, pesan error, waktu mulai, dan pengguna yang terdampak.

## Permintaan di luar lingkup
Masalah jaringan diteruskan ke tim infrastruktur. Permintaan akun, pertanyaan cara pakai, dan permintaan data bukan insiden aplikasi. Permintaan menghapus data keuangan tidak boleh diproses tanpa persetujuan Team Leader.
