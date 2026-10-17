# Kebijakan SLA dan Urutan Pengerjaan Application Support (DRAFT)

## SLA
Semua tiket memakai target yang sama, sekitar 3 jam. Jam SLA mulai berjalan setelah petugas ops yang ditugaskan menerima email penugasan, bukan saat pelapor mengirim tiket. Karena itu tiket yang ditugaskan ke tim yang salah atau tidak lengkap akan membuang waktu SLA.

## Prioritas menentukan urutan pengerjaan
Prioritas tidak mengubah target SLA. Prioritas dipakai Team Leader untuk mengelompokkan masalah dan menentukan mana yang dikerjakan lebih dulu. Keputusan akhir ada di Team Leader.
- Dampak Tinggi: banyak pengguna atau satu proses utama terhenti (penagihan, pengiriman, closing, pajak), tidak ada workaround, atau ada risiko kepatuhan dan keamanan data.
- Dampak Sedang: satu tim terganggu atau ada workaround yang merepotkan.
- Dampak Rendah: satu pengguna, satu record, atau tampilan, ada workaround mudah.
- Urgensi Tinggi: ada tenggat hari ini (pengiriman hari ini, closing bulan, audit). Urgensi Sedang: tenggat dalam beberapa hari. Urgensi Rendah: tidak ada tenggat.

## Matriks urutan
Dampak Tinggi dengan urgensi Tinggi atau Sedang adalah P1. Dampak Tinggi dengan urgensi Rendah, atau dampak Sedang dengan urgensi Tinggi, adalah P2. Dampak Sedang dengan urgensi Sedang, atau dampak Rendah dengan urgensi Tinggi, adalah P3. Sisanya P4.
Jika beberapa pengguna melaporkan masalah yang sama, dampak dinaikkan satu tingkat.

## Tindak lanjut ke tim lain
Hak akses atau akun: tindak lanjut ke comsec. Jaringan: ke tim jaringan. Bug yang sudah dianalisis dan berdampak besar: Team Leader memutuskan serah terima ke tim proyek. Perubahan tampilan atau standar sistem: pelapor diarahkan ke tim bisnis untuk mengajukan change request.

## Tiket yang informasinya belum cukup
Jangan menetapkan prioritas hanya karena pelapor menulis kata mendesak. Minta informasi tambahan sesuai template tiket sebelum menugaskan.

## Permintaan di luar lingkup
Permintaan menghapus data keuangan tidak boleh diproses tanpa persetujuan Team Leader.
