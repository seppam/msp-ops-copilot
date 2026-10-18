# Kebijakan Penghapusan Data (DRAFT)

## Tidak ada penghapusan permanen
Permintaan menghapus data tidak boleh diproses sebagai penghapusan permanen di database. Penghapusan dari antarmuka memakai soft delete: baris diberi tanda pada kolom isDeleted sehingga tidak tampil di UI, tetapi datanya tetap ada untuk audit.

## Data keuangan
Penghapusan atau penyembunyian data keuangan (invoice, jurnal, pembayaran) memerlukan persetujuan Team Leader. Untuk dokumen yang sudah diposting, koreksi dilakukan dengan dokumen pembalik, bukan dengan menghapus.

## Cara menangani permintaan
Catat alasan pelapor, minta persetujuan Team Leader, dan jangan menjalankan perubahan data apa pun sebelum disetujui.
