# Inventory DPP — Vehicle Management System

Aplikasi web manajemen data kendaraan dan history service menggunakan Python Flask dan Google Sheets sebagai database.

---

## Prasyarat

- Python 3.10+
- Google Cloud Project dengan Service Account
- Google Sheets API & Google Drive API enabled
- File `credentials.json` dari Service Account

---

## Langkah Setup

### 1. Clone / Download Repository

```bash
cd d:\Project-app\inventory-dpp
```

### 2. Buat Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

```bash
copy .env.example .env
```

Edit file `.env` sesuai kebutuhan:
```
SECRET_KEY=ganti-dengan-secret-key-anda
SPREADSHEET_NAME=database-inventory-dpp
PORT=5000
```

### 5. Setup Google Sheets

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau gunakan yang sudah ada
3. Enable **Google Sheets API** dan **Google Drive API**
4. Buat **Service Account** dan download `credentials.json`
5. Letakkan `credentials.json` di root folder project
6. Buka Google Sheets `database-inventory-dpp`
7. **Share** spreadsheet ke email Service Account (lihat di `credentials.json` field `client_email`) dengan akses **Editor**

### 6. Struktur Google Sheets

Pastikan spreadsheet `database-inventory-dpp` memiliki 3 sheet dengan header berikut:

**Sheet: `Master Data Kendaraan`**
```
No | No. Kendaraan | Pemilik | Merk | Model Kendaraan | Jenis/Type | Warna | No. Rangka | No. Mesin | STNK 1 Tahun | Realisasi Pembayaran Pajak | STNK 5 Tahun | Tanggal Realisasi KIR | No Asuransi | Nama Asuransi | Jenis Asuransi | Tanggal Berlaku Asuransi | Periode Tahun Asuransi | GPS/APCT | No. BPKB | Posisi BPKB | Bahan Bakar | Keterangan
```

**Sheet: `History Service Kendaraan Mobil`**
```
No | No. Kendaraan | Nama Pemilik | Tanggal Service | Nama Bengkel | Jenis Service | Jumlah Part | Satuan | Pengajuan | Realisasi | Total | KM Awal | KM Akhir | Selisih KM | KM Selanjutnya | Keterangan
```

**Sheet: `History Service Kendaraan Motor`**
```
No | No. Kendaraan | Nama Pemilik | Tanggal Service | Nama Bengkel | Jenis Service | Jumlah Part | Satuan | Pengajuan | Realisasi | Total | KM Awal | KM Akhir | Selisih KM | KM Selanjutnya | Keterangan
```

### 7. Jalankan Aplikasi

```bash
python app.py
```

Akses di browser: **http://localhost:5000**

---

## Fitur

| Fitur | Deskripsi |
|-------|-----------|
| 📊 Dashboard | Ringkasan data, STNK/KIR/Asuransi yang akan jatuh tempo |
| 🚗 Master Data Kendaraan | CRUD lengkap data kendaraan |
| 📋 Update Dokumen | Form khusus update STNK, KIR, dan Asuransi |
| 🔧 History Service Mobil | CRUD history service kendaraan roda 4 |
| 🛵 History Service Motor | CRUD history service kendaraan roda 2 |
| 🔍 Search & Filter | Filter data di setiap tabel |

---

## Struktur Project

```
inventory-dpp/
├── app.py                          # Aplikasi Flask utama
├── requirements.txt                # Dependensi Python
├── .env.example                    # Template environment variables
├── credentials.json                # Service Account key (JANGAN di-commit!)
├── README.md                       # Dokumentasi ini
├── .gitignore                      # File yang diabaikan Git
├── templates/
│   ├── base.html                   # Layout dasar (navbar, footer)
│   ├── index.html                  # Dashboard
│   ├── kendaraan/
│   │   ├── list.html               # Daftar kendaraan
│   │   ├── form.html               # Form tambah/edit kendaraan
│   │   └── update_dokumen.html     # Form update STNK/KIR/Asuransi
│   └── service/
│       ├── list.html               # Daftar history service
│       └── form.html               # Form tambah/edit service
└── static/
    └── css/
        └── custom.css              # Custom CSS tambahan
```

---

## Troubleshooting

**Error: `SpreadsheetNotFound`**
- Pastikan nama spreadsheet persis `database-inventory-dpp`
- Pastikan sudah di-share ke email service account

**Error: `WorksheetNotFound`**
- Pastikan nama sheet persis sesuai (case-sensitive):
  - `Master Data Kendaraan`
  - `History Service Kendaraan Mobil`
  - `History Service Kendaraan Motor`

**Error: `credentials.json not found`**
- Pastikan file `credentials.json` ada di folder root project

---

## Keamanan

- ⚠️ **Jangan commit** `credentials.json` ke repository
- ⚠️ **Jangan commit** file `.env` ke repository
- Keduanya sudah terdaftar di `.gitignore`
