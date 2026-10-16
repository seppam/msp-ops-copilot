# Matriks Dampak Menu Aplikasi (DRAFT - perlu dikoreksi tim)

## Sales > Orders > Quotations
Proses: pembuatan dan pengiriman penawaran ke customer. Pengguna: tim Sales. Jika tidak bisa dipakai sama sekali: penawaran tertunda dan order bisa hilang, dampak Tinggi. Jika hanya satu record atau tampilan email: dampak Rendah sampai Sedang, ada workaround kirim PDF manual.

## Sales > Orders > Orders
Proses: konfirmasi sales order yang memicu pengiriman dan penagihan. Pengguna: Sales dan Admin Sales. Jika konfirmasi gagal untuk semua user: pesanan customer tertahan, dampak Tinggi. Jika hanya satu user: dampak Rendah karena user lain dapat membantu.

## Sales > To Invoice
Proses: daftar order yang siap ditagih. Pengguna: Finance. Jika tidak akurat: penagihan terlambat dan arus kas tertunda, dampak Sedang.

## Inventory > Operations > Deliveries
Proses: validasi pengiriman barang ke customer. Pengguna: Gudang. Jika validasi gagal untuk semua pengiriman: barang tidak bisa keluar dan customer menerima terlambat, dampak Tinggi. Satu record: dampak Sedang.

## Inventory > Operations > Receipts
Proses: penerimaan barang dari vendor. Pengguna: Gudang. Jika gagal: stok tidak masuk sehingga penjualan dan produksi terhambat, dampak Sedang sampai Tinggi.

## Inventory > Operations > Transfers
Proses: perpindahan stok antar gudang. Pengguna: Gudang. Dampak Sedang. Ada workaround manual lewat penyesuaian stok dengan persetujuan supervisor.

## Inventory > Reporting > Stock
Proses: laporan stok untuk keputusan pembelian dan ketersediaan barang. Pengguna: Purchasing, Sales, Gudang. Jika angka salah: salah beli atau menolak order yang sebenarnya bisa dipenuhi, dampak Sedang sampai Tinggi.

## Accounting > Customers > Invoices
Proses: penerbitan faktur ke customer termasuk pajak PPN. Pengguna: Finance dan customer penerima faktur. Jika perhitungan pajak atau nominal salah: faktur keliru sampai ke customer dan berisiko masalah pajak (kepatuhan), dampak Tinggi.

## Accounting > Customers > Payments
Proses: pencatatan pembayaran customer. Pengguna: Finance. Dampak Sedang. Ada workaround lewat input manual jurnal.

## Accounting > Vendors > Bills
Proses: pencatatan tagihan vendor. Pengguna: Finance dan Purchasing. Nominal salah: salah bayar vendor, dampak Sedang.

## Accounting > Accounting > Journal Entries
Proses: posting jurnal dan closing bulanan. Pengguna: Finance. Pada periode closing (akhir dan awal bulan) kegagalan posting menghentikan laporan keuangan, dampak Tinggi. Di luar periode closing: dampak Sedang.

## Accounting > Reporting
Proses: laporan Aged Receivable, Trial Balance. Pengguna: Finance dan manajemen. Angka tidak cocok: keputusan dan audit terganggu, dampak Sedang sampai Tinggi.

## Purchase > Orders > Requests for Quotation
Proses: pengadaan barang dan persetujuan pembelian. Pengguna: Purchasing dan Manager. Jika email ke vendor atau approval gagal untuk semua: pengadaan terhenti, dampak Tinggi.

## Contacts
Proses: data master customer dan vendor. Pengguna: semua tim. Data ganda memecah saldo piutang dan riwayat transaksi, dampak Sedang.

## Employees dan hak akses
Proses: data karyawan, termasuk data sensitif (gaji, identitas). Akses yang bocor ke pengguna non-HR adalah masalah keamanan dan privasi data, dampak Tinggi dan harus dieskalasi ke Team Leader.
