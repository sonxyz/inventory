# ISSUE: Filter Rekap ATK per Departemen

## Deskripsi Masalah / Kebutuhan
Saat ini, halaman Rekap Pengajuan ATK (`/atk/rekap`) hanya menyediakan filter berdasarkan **Bulan** dan **Tahun**. Data rekap yang ditampilkan menggabungkan seluruh departemen yang ada. Pengguna membutuhkan kemampuan untuk menyaring rekapitulasi secara spesifik berdasarkan **Departemen** tertentu agar visualisasi "Rekap Per Departemen" dan "Rekap Per Barang" dapat difokuskan pada satu divisi saja.

## Rincian Perubahan

### 1. Backend Routing (`app.py` -> `atk_rekap`)
- Tangkap query parameter `departement` dari request GET.
- Ambil daftar master departemen dari Google Sheets (`Master Departement`) untuk dikirim ke dropdown pilihan filter di template HTML.
- Terapkan logika penyaringan data pengajuan ATK berdasarkan departemen terpilih jika parameter `departement` dikirimkan.

### 2. Frontend Layout (`templates/atk/rekap.html`)
- Tambahkan pilihan dropdown **Departement** pada Filter Bar di halaman rekap.
- Masukkan daftar departemen dari database secara dinamis.
- Sesuaikan penataan grid Tailwind agar Filter Bar terlihat rapi dengan 4 input (Departement, Bulan, Tahun, Tombol Aksi).
