# ISSUE: Inventory DPP — Vehicle Management Web Application

## Overview
Bangun aplikasi web **Inventory DPP** untuk manajemen data kendaraan dan history service menggunakan Python Flask, TailwindCSS, dan Google Sheets sebagai database.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python Flask |
| Frontend | Jinja2 Templates + TailwindCSS (CDN) |
| Database | Google Sheets via `gspread` + `google-auth` |
| Auth | Service Account (`credentials.json`) |
| Environment | `.env` via `python-dotenv` |

---

## Google Sheets Schema

**Spreadsheet Name:** `database-inventory-dpp`

### Sheet 1: `Master Data Kendaraan`

| # | Field | Type | Keterangan |
|---|-------|------|------------|
| 1 | No | Auto-increment | Nomor urut otomatis |
| 2 | No. Kendaraan | String | Plat nomor kendaraan |
| 3 | Pemilik | String | Nama pemilik kendaraan |
| 4 | Merk | String | Merk kendaraan (Honda, Toyota, dll) |
| 5 | Model Kendaraan | String | Model kendaraan |
| 6 | Jenis/Type | String | Jenis atau tipe kendaraan |
| 7 | Warna | String | Warna kendaraan |
| 8 | Tahun Kendaraan | Number (Year) | Tahun pembuatan kendaraan (contoh: 2020) |
| 9 | No. Rangka | String | Nomor rangka |
| 10 | No. Mesin | String | Nomor mesin |
| 11 | STNK 1 Tahun | Date | Tanggal jatuh tempo STNK 1 tahun |
| 12 | Realisasi Pembayaran Pajak | Date | Tanggal realisasi pembayaran pajak |
| 13 | STNK 5 Tahun | Date | Tanggal jatuh tempo STNK 5 tahun |
| 14 | Tanggal Realisasi KIR | Date | Tanggal realisasi KIR |
| 15 | No Asuransi | String | Nomor polis asuransi |
| 16 | Nama Asuransi | String | Nama perusahaan asuransi |
| 17 | Jenis Asuransi | String | Jenis asuransi (All Risk, TLO, dll) |
| 18 | Tanggal Berlaku Asuransi | Date | Tanggal mulai berlaku asuransi |
| 19 | Periode Tahun Asuransi | String | Periode tahun asuransi |
| 20 | Biaya Premi Asuransi | Number (Currency) | Biaya premi asuransi per periode |
| 21 | GPS/APCT | String | Info GPS/APCT |
| 22 | No. BPKB | String | Nomor BPKB |
| 23 | Posisi BPKB | String | Lokasi penyimpanan BPKB |
| 24 | Bahan Bakar | String | Jenis bahan bakar (Bensin, Solar, dll) |
| 25 | Keterangan | String | Catatan tambahan |

### Sheet 2: `History Service Kendaraan Mobil`

| # | Field | Type | Keterangan |
|---|-------|------|------------|
| 1 | No | Auto-increment | Nomor urut otomatis |
| 2 | No. Kendaraan | String | Plat nomor kendaraan |
| 3 | Nama Pemilik | String | Nama pemilik |
| 4 | Tanggal Service | Date | Tanggal service dilakukan |
| 5 | Nama Bengkel | String | Nama bengkel tempat service |
| 6 | Jenis Service | String | Jenis service (Ganti Oli, Tune Up, dll) |
| 7 | Jumlah Part | Number | Jumlah part yang diganti |
| 8 | Satuan | String | Satuan part (pcs, liter, dll) |
| 9 | Pengajuan | Number (Currency) | Biaya yang diajukan |
| 10 | Realisasi | Number (Currency) | Biaya realisasi |
| 11 | Total | Number (Currency) | Total biaya |
| 12 | KM Awal | Number | Kilometer awal saat service |
| 13 | KM Akhir | Number | Kilometer akhir saat service |
| 14 | Selisih KM | Number (auto) | Selisih KM (KM Akhir - KM Awal) |
| 15 | KM Selanjutnya | Number | Target KM service selanjutnya |
| 16 | Keterangan | String | Catatan tambahan |

### Sheet 3: `History Service Kendaraan Motor`

> **Struktur field sama persis** dengan Sheet 2 (`History Service Kendaraan Mobil`), dipisah agar data motor dan mobil tidak tercampur.

---

## Features & Routes

### 1. Dashboard / Home
- **Route:** `GET /`
- Tampilkan ringkasan data:
  - Total kendaraan
  - Jumlah STNK yang akan jatuh tempo (30 hari ke depan)
  - Jumlah asuransi yang akan expired (30 hari ke depan)
  - Jumlah KIR yang perlu diperpanjang
- Navigasi ke semua fitur utama

### 2. Master Data Kendaraan
- **Route:** `GET /kendaraan`
- Tampilkan tabel semua data kendaraan dari sheet `Master Data Kendaraan`
- Fitur:
  - **Search/Filter:** Cari berdasarkan No. Kendaraan, Pemilik, Merk, Jenis/Type
  - **Pagination** (opsional, jika data banyak)
  - **Action buttons:** Edit, Delete per row

- **Route:** `GET /kendaraan/tambah` — Form tambah kendaraan baru
- **Route:** `POST /kendaraan/tambah` — Simpan data kendaraan baru ke sheet
- **Route:** `GET /kendaraan/edit/<no>` — Form edit kendaraan
- **Route:** `POST /kendaraan/edit/<no>` — Update data kendaraan di sheet
- **Route:** `POST /kendaraan/delete/<no>` — Hapus data kendaraan dari sheet

### 3. Update STNK, KIR & Asuransi
- **Route:** `GET /kendaraan/update-dokumen/<no>` — Form khusus update field:
  - STNK 1 Tahun
  - Realisasi Pembayaran Pajak
  - STNK 5 Tahun
  - Tanggal Realisasi KIR
  - No Asuransi, Nama Asuransi, Jenis Asuransi
  - Tanggal Berlaku Asuransi, Periode Tahun Asuransi
  - Biaya Premi Asuransi
- **Route:** `POST /kendaraan/update-dokumen/<no>` — Simpan perubahan dokumen

### 4. History Service Kendaraan Mobil
- **Route:** `GET /service/mobil`
- Tampilkan tabel history service mobil
- Fitur search/filter berdasarkan No. Kendaraan, Nama Pemilik, Tanggal Service
- **Route:** `GET /service/mobil/tambah` — Form tambah history service mobil
- **Route:** `POST /service/mobil/tambah` — Simpan data service baru
- **Route:** `GET /service/mobil/edit/<no>` — Form edit service
- **Route:** `POST /service/mobil/edit/<no>` — Update data service
- **Route:** `POST /service/mobil/delete/<no>` — Hapus data service

### 5. History Service Kendaraan Motor
- **Route:** `GET /service/motor`
- Tampilkan tabel history service motor (struktur sama dengan mobil)
- Fitur search/filter berdasarkan No. Kendaraan, Nama Pemilik, Tanggal Service
- **Route:** `GET /service/motor/tambah` — Form tambah history service motor
- **Route:** `POST /service/motor/tambah` — Simpan data service baru
- **Route:** `GET /service/motor/edit/<no>` — Form edit service
- **Route:** `POST /service/motor/edit/<no>` — Update data service
- **Route:** `POST /service/motor/delete/<no>` — Hapus data service

### 6. Tracking History Service Per Kendaraan *(Ditambahkan)*
- **Route:** `GET /kendaraan/tracking/<no_kendaraan>`
- Halaman tracking per kendaraan berdasarkan No. Kendaraan (plat nomor)
- Menggabungkan data service dari sheet Mobil & Motor secara otomatis
- **Fitur:**
  - **4 Stats Cards:** Total service, total biaya realisasi, KM terakhir, KM service berikutnya
  - **KM Progress Bar:** Visual progress menuju target KM service berikutnya (warna berubah: hijau → orange → merah saat mendekati target)
  - **Jenis Service Chart:** Bar chart horizontal top-6 jenis service terbanyak
  - **Timeline:** Riwayat service chronological (newest first) dengan tombol edit/hapus per item
  - **Tabel KM:** Riwayat perubahan kilometer (KM awal, akhir, selisih, target berikutnya)
- **Akses:** Tombol ikon jam (🕐) pada kolom Aksi di halaman Master Data Kendaraan

---

## Project Structure

```
inventory-dpp/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── credentials.json                # Google Service Account key (JANGAN di-commit)
├── README.md                       # Setup & usage instructions
├── .gitignore                      # Ignore credentials, venv, .env
│
├── templates/
│   ├── base.html                   # Base layout (navbar, TailwindCSS CDN, footer)
│   ├── index.html                  # Dashboard / Home
│   ├── kendaraan/
│   │   ├── list.html               # Tabel master data kendaraan
│   │   ├── form.html               # Form tambah/edit kendaraan (reusable)
│   │   └── update_dokumen.html     # Form update STNK/KIR/Asuransi
│   └── service/
│       ├── list.html               # Tabel history service (reusable mobil & motor)
│       └── form.html               # Form tambah/edit service (reusable)
│
└── static/                         # (opsional) custom CSS/JS jika diperlukan
    └── css/
        └── custom.css
```

---

## Implementation Details

### 1. `app.py` — Main Application

```python
# Struktur utama app.py

# --- Imports ---
from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os

# --- Config ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')

# --- Google Sheets Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open('database-inventory-dpp')

# Akses setiap sheet
sheet_kendaraan = spreadsheet.worksheet('Master Data Kendaraan')
sheet_service_mobil = spreadsheet.worksheet('History Service Kendaraan Mobil')
sheet_service_motor = spreadsheet.worksheet('History Service Kendaraan Motor')

# --- Helper Functions ---
def get_all_data(sheet):
    """Ambil semua data dari sheet sebagai list of dict"""
    return sheet.get_all_records()

def find_row_by_no(sheet, no):
    """Cari baris berdasarkan kolom 'No'"""
    cell = sheet.find(str(no), in_column=1)
    return cell.row if cell else None

def get_next_no(sheet):
    """Generate auto-increment No"""
    records = sheet.get_all_records()
    if not records:
        return 1
    return max(r.get('No', 0) for r in records) + 1

# --- Routes ---
# Implementasi setiap route sesuai Features & Routes di atas

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### 2. `templates/base.html` — Base Layout

- Gunakan TailwindCSS via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Sidebar navigation atau top navbar dengan menu:
  - Dashboard
  - Master Data Kendaraan
  - Service Mobil
  - Service Motor
- Flash messages area untuk notifikasi sukses/error
- Responsive layout (mobile-friendly)
- Warna tema: Biru/putih profesional (corporate style)

### 3. Template Guidelines

- **Semua template extend `base.html`**
- Gunakan Jinja2 template inheritance: `{% extends 'base.html' %}` dan `{% block content %}`
- Form menggunakan method POST dengan CSRF-safe (Flask flash)
- Tabel menggunakan TailwindCSS utility classes
- Search/filter menggunakan query parameter: `?search=keyword`
- Implementasi search di backend (filter data dari `get_all_records()`)

### 4. `requirements.txt`

```
Flask==3.1.1
gspread==6.1.4
google-auth==2.38.0
google-auth-oauthlib==1.2.1
python-dotenv==1.1.0
```

### 5. `.env.example`

```
SECRET_KEY=your-secret-key-here
GOOGLE_SHEETS_CREDENTIALS=credentials.json
SPREADSHEET_NAME=database-inventory-dpp
```

### 6. `.gitignore`

```
credentials.json
.env
__pycache__/
venv/
*.pyc
```

---

## UI/UX Guidelines

### Design System (TailwindCSS)
- **Primary Color:** Blue (`bg-blue-600`, `text-blue-600`)
- **Background:** Light gray (`bg-gray-50` atau `bg-gray-100`)
- **Cards:** White (`bg-white`) dengan shadow (`shadow-md`)
- **Table:** Striped rows, hover effect, responsive overflow
- **Buttons:**
  - Primary: `bg-blue-600 hover:bg-blue-700 text-white`
  - Danger: `bg-red-600 hover:bg-red-700 text-white`
  - Edit: `bg-yellow-500 hover:bg-yellow-600 text-white`
- **Forms:** Rounded input, focus ring, label di atas input
- **Flash Messages:** Alert-style notification (success=green, error=red)

### Responsive
- Tabel harus scrollable horizontal di mobile (`overflow-x-auto`)
- Navbar collapse di mobile (hamburger menu)
- Form width responsive (`max-w-2xl mx-auto`)

---

## Setup Instructions (untuk README.md)

```markdown
## Prasyarat
- Python 3.10+
- Google Cloud Project dengan Service Account
- Google Sheets API & Google Drive API enabled
- credentials.json dari Service Account

## Langkah Setup

1. Clone repository
2. Buat virtual environment:
   python -m venv venv
   venv\Scripts\activate   (Windows)
3. Install dependencies:
   pip install -r requirements.txt
4. Copy .env.example ke .env:
   copy .env.example .env
5. Letakkan credentials.json di root folder
6. Share spreadsheet "database-inventory-dpp" ke email service account
7. Jalankan aplikasi:
   python app.py
8. Akses di browser: http://localhost:5000
```

---

## Acceptance Criteria

- [ ] Aplikasi berjalan tanpa error di `http://localhost:5000`
- [ ] Dashboard menampilkan ringkasan data kendaraan
- [ ] CRUD Master Data Kendaraan berfungsi (Create, Read, Update, Delete)
- [ ] Form update STNK, KIR, dan Asuransi terpisah dan berfungsi
- [ ] History Service Mobil — CRUD lengkap
- [ ] History Service Motor — CRUD lengkap (sheet terpisah)
- [ ] **Tracking History Service** per kendaraan — timeline, stats KM, biaya, progress bar
- [ ] Search/filter berfungsi di setiap tabel
- [ ] Flash messages muncul setelah setiap operasi (sukses/gagal)
- [ ] UI responsive dan menggunakan TailwindCSS
- [ ] `requirements.txt`, `.env.example`, `README.md` tersedia
- [ ] Tidak ada credentials yang ter-commit ke repository

---

## Notes untuk Developer

> **Target model:** Sonnet 4.6 — pastikan instruksi eksplisit dan terstruktur.

1. **Jangan gunakan ORM** — langsung pakai `gspread` API
2. **Error handling wajib** — wrap semua operasi Google Sheets dengan try-except
3. **Auto-increment No** — hitung dari data existing, bukan pakai counter terpisah
4. **Selisih KM** di service dihitung otomatis: `KM Akhir - KM Awal`
5. **Sheet names harus exact match** dengan yang ada di Google Sheets
6. **Format currency** — tampilkan Pengajuan, Realisasi, Total, dan Biaya Premi Asuransi dengan format Rupiah
7. **Date fields** — gunakan format `DD/MM/YYYY` untuk konsistensi dengan Google Sheets
8. **Template reuse** — `service/list.html` dan `service/form.html` bisa dipakai untuk mobil & motor dengan parameter berbeda
9. **Credentials path** — baca dari `.env` atau default ke `credentials.json`
10. **Port** — default 5000, bisa diubah via environment variable
