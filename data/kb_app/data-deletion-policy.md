# Kebijakan Penghapusan Data (DRAFT)

## Soft delete adalah standar
Permintaan menghapus data diproses sebagai soft delete: baris diberi tanda pada kolom isDeleted sehingga tidak tampil di UI, tetapi datanya tetap ada untuk audit. Dukungan aplikasi tidak menjalankan penghapusan permanen sendiri.

## Penghapusan permanen
Penghapusan permanen di database bisa dilakukan hanya dalam kasus khusus, dengan alasan yang kuat dan persetujuan berjenjang dari beberapa tingkat manajemen. Pelapor tidak boleh meminta penghapusan permanen lewat tiket biasa. Permintaan seperti itu harus dieskalasi ke Team Leader.

## Data keuangan
Penghapusan atau penyembunyian data keuangan (invoice, jurnal, pembayaran) memerlukan persetujuan Team Leader. Untuk dokumen yang sudah diposting, koreksi dilakukan dengan dokumen pembalik, bukan dengan menghapus.

## Cara menangani permintaan
Catat alasan pelapor, minta persetujuan Team Leader, dan jangan menjalankan perubahan data apa pun sebelum disetujui.
