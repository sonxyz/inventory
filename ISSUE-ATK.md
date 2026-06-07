# ISSUE-ATK: Modul Pengajuan ATK — Alat Tulis Kantor

## Overview
Tambahkan modul **Pengajuan ATK (Alat Tulis Kantor)** ke dalam aplikasi web **Inventory DPP** yang sudah berjalan. Modul ini mengelola master data ATK, master departemen, dan proses pengajuan kebutuhan ATK per departemen per bulan. Data disimpan di Google Sheets yang sama (`database-inventory-dpp`) dengan sheet tambahan.

> **Modul ini digabung dengan aplikasi Inventory DPP yang sudah ada** — menggunakan `app.py`, `base.html`, dan infrastruktur yang sama.

---

## Tech Stack

> Sama dengan aplikasi utama Inventory DPP — tidak ada dependensi tambahan.

| Layer | Technology |
|-------|------------|
| Backend | Python Flask (existing `app.py`) |
| Frontend | Jinja2 Templates + TailwindCSS (CDN) |
| Database | Google Sheets via `gspread` + `google-auth` |
| Spreadsheet | `database-inventory-dpp` (sama dengan modul Kendaraan) |

---

## Google Sheets Schema

**Spreadsheet Name:** `database-inventory-dpp` *(sudah ada)*

### Sheet: `Master Data ATK`  *(BARU)*

| # | Field | Type | Keterangan |
|---|-------|------|------------|
| 1 | No | Auto-increment | Nomor urut otomatis |
| 2 | Kode | String | Kode unik barang ATK (contoh: ATK-001) |
| 3 | Nama Barang | String | Nama barang ATK (contoh: Kertas HVS A4, Pulpen, dll) |
| 4 | Perkiraan Harga | Number (Currency) | Perkiraan harga satuan barang (Rupiah) |
| 5 | Satuan | String | Satuan barang (rim, pcs, pak, box, lusin, dll) |

### Sheet: `Master Departement`  *(BARU)*

| # | Field | Type | Keterangan |
|---|-------|------|------------|
| 1 | No | Auto-increment | Nomor urut otomatis |
| 2 | Departement | String | Nama departemen (contoh: HRD, Finance, IT, dll) |

### Sheet: `Pengajuan ATK`  *(BARU)*

> Sheet ini menyimpan semua data transaksi pengajuan ATK dari setiap departemen.

| # | Field | Type | Keterangan |
|---|-------|------|------------|
| 1 | No | Auto-increment | Nomor urut otomatis |
| 2 | Tanggal Pengajuan | Date (DD/MM/YYYY) | Tanggal pengajuan dibuat |
| 3 | Bulan | String | Bulan pengajuan (Januari, Februari, ... Desember) |
| 4 | Tahun | Number (Year) | Tahun pengajuan (contoh: 2026) |
| 5 | Departement | String | Nama departemen yang mengajukan (dari Master Departement) |
| 6 | Kode Barang | String | Kode barang ATK (dari Master Data ATK) |
| 7 | Nama Barang | String | Nama barang ATK (auto-fill dari Master Data ATK) |
| 8 | Jumlah | Number | Jumlah barang yang diajukan |
| 9 | Satuan | String | Satuan barang (auto-fill dari Master Data ATK) |
| 10 | Harga Satuan | Number (Currency) | Harga satuan (auto-fill dari Perkiraan Harga Master ATK, bisa di-override) |
| 11 | Total Harga | Number (Currency) | Total harga = Jumlah × Harga Satuan (auto-hitung) |
| 12 | Keterangan | String | Catatan tambahan |

---

## Features & Routes

### 1. Master Data ATK (CRUD)

#### Halaman List
- **Route:** `GET /atk/master`
- Tampilkan tabel semua data barang ATK dari sheet `Master Data ATK`
- Fitur:
  - **Search/Filter:** Cari berdasarkan Kode, Nama Barang
  - **Action buttons:** Edit, Delete per row

#### Tambah Data
- **Route:** `GET /atk/master/tambah` — Form tambah barang ATK baru
- **Route:** `POST /atk/master/tambah` — Simpan data barang ATK baru ke sheet
- Field input: Kode, Nama Barang, Perkiraan Harga, Satuan
- No di-generate otomatis (auto-increment)

#### Edit Data
- **Route:** `GET /atk/master/edit/<no>` — Form edit barang ATK
- **Route:** `POST /atk/master/edit/<no>` — Update data barang ATK di sheet

#### Hapus Data
- **Route:** `POST /atk/master/delete/<no>` — Hapus data barang ATK dari sheet

---

### 2. Master Departement (CRUD)

#### Halaman List
- **Route:** `GET /atk/departement`
- Tampilkan tabel semua departemen dari sheet `Master Departement`
- Fitur:
  - **Search/Filter:** Cari berdasarkan nama Departement
  - **Action buttons:** Edit, Delete per row

#### Tambah Data
- **Route:** `GET /atk/departement/tambah` — Form tambah departemen baru
- **Route:** `POST /atk/departement/tambah` — Simpan data departemen baru ke sheet
- Field input: Departement
- No di-generate otomatis (auto-increment)

#### Edit Data
- **Route:** `GET /atk/departement/edit/<no>` — Form edit departemen
- **Route:** `POST /atk/departement/edit/<no>` — Update data departemen di sheet

#### Hapus Data
- **Route:** `POST /atk/departement/delete/<no>` — Hapus data departemen dari sheet

---

### 3. Pengajuan ATK *(Fitur Utama)*

#### Form Pengajuan
- **Route:** `GET /atk/pengajuan/tambah` — Form pengajuan ATK baru
- **Route:** `POST /atk/pengajuan/tambah` — Simpan data pengajuan ke sheet
- **Behavior:**
  - Pilih **Departement** dari dropdown (data dari sheet `Master Departement`)
  - Pilih **Bulan** dari dropdown (Januari – Desember)
  - Pilih **Tahun** dari input number (default: tahun sekarang)
  - Tanggal Pengajuan otomatis terisi tanggal hari ini (bisa di-edit)
  - Pilih **Kode Barang** dari dropdown (data dari sheet `Master Data ATK`)
  - Saat Kode Barang dipilih → **auto-fill**: Nama Barang, Satuan, Harga Satuan (dari Master Data ATK)
  - Input **Jumlah** → **auto-hitung** Total Harga = Jumlah × Harga Satuan
  - Harga Satuan bisa di-override manual jika diperlukan
  - Input **Keterangan** (opsional)
  - **Bisa input multiple items** sekaligus dalam satu form (dynamic rows)
    - Tombol "Tambah Barang" untuk menambah baris baru
    - Tombol "Hapus" (×) per baris untuk menghapus item
    - Semua items di-submit sekaligus → masing-masing jadi 1 row di sheet

#### Edit Pengajuan
- **Route:** `GET /atk/pengajuan/edit/<no>` — Form edit pengajuan
- **Route:** `POST /atk/pengajuan/edit/<no>` — Update data pengajuan di sheet

#### Hapus Pengajuan
- **Route:** `POST /atk/pengajuan/delete/<no>` — Hapus data pengajuan dari sheet

---

### 4. Lihat Pengajuan ATK *(Filter Departement & Bulan)*

- **Route:** `GET /atk/pengajuan`
- Tampilkan tabel semua pengajuan ATK dari sheet `Pengajuan ATK`
- **Filter:**
  - **Departement** — dropdown filter (dari Master Departement, termasuk opsi "Semua")
  - **Bulan** — dropdown filter (Januari – Desember, termasuk opsi "Semua")
  - **Tahun** — dropdown/input filter (default: tahun sekarang, termasuk opsi "Semua")
  - Filter diterapkan secara kombinasi (AND logic)
- **Tampilan Tabel:**
  - Kolom: No, Tanggal Pengajuan, Departement, Kode, Nama Barang, Jumlah, Satuan, Harga Satuan, Total Harga, Keterangan, Aksi
  - **Action buttons:** Edit, Delete per row
  - **Footer tabel:** Total keseluruhan harga dari data yang ter-filter
- **Search tambahan:** input text search untuk Nama Barang, Kode Barang

---

### 5. Rekap Pengajuan ATK *(Laporan Ringkasan)*

- **Route:** `GET /atk/rekap`
- Halaman rekap/laporan ringkasan pengajuan ATK
- **Filter:**
  - **Bulan** — dropdown (Januari – Desember, termasuk opsi "Semua")
  - **Tahun** — dropdown/input (default: tahun sekarang)
- **Tampilan Rekap:**

#### 5a. Rekap Per Departement
- Tabel ringkasan per departemen:
  - Kolom: No, Departement, Jumlah Item, Total Harga
  - Baris di-aggregate dari data `Pengajuan ATK` berdasarkan filter bulan/tahun
  - **Grand Total** di footer

#### 5b. Rekap Per Barang
- Tabel ringkasan per barang:
  - Kolom: No, Kode, Nama Barang, Total Jumlah, Satuan, Total Harga
  - Data di-aggregate berdasarkan kode barang dari filter bulan/tahun

#### 5c. Detail Per Departement (Expandable)
- Klik nama departemen → expand/collapse detail pengajuan departemen tersebut
- Detail menampilkan: Kode, Nama Barang, Jumlah, Satuan, Harga Satuan, Total Harga

#### 5d. Print / Cetak
- Tombol **"Cetak Rekap"** — buka halaman print-friendly (`window.print()`)
- Layout cetak: header laporan, tabel rekap, footer tanggal cetak

---

## Integrasi dengan Aplikasi Existing

### Navigasi (base.html)
Tambahkan menu baru di sidebar/navbar existing:

```
📋 ATK (Alat Tulis Kantor)
   ├── Master Data ATK          → /atk/master
   ├── Master Departement       → /atk/departement
   ├── Pengajuan ATK            → /atk/pengajuan
   ├── Buat Pengajuan           → /atk/pengajuan/tambah
   └── Rekap Pengajuan          → /atk/rekap
```

> Menu ATK bisa dijadikan sub-menu collapsible di bawah menu Kendaraan yang sudah ada.

### Sheet Constants (app.py)
Tambahkan di bagian sheet name constants:

```python
# Sheet names — ATK Module
SHEET_MASTER_ATK = 'Master Data ATK'
SHEET_MASTER_DEPT = 'Master Departement'
SHEET_PENGAJUAN_ATK = 'Pengajuan ATK'
```

### Headers Constants (app.py)
Tambahkan di bagian headers:

```python
HEADERS_MASTER_ATK = ['No', 'Kode', 'Nama Barang', 'Perkiraan Harga', 'Satuan']

HEADERS_MASTER_DEPT = ['No', 'Departement']

HEADERS_PENGAJUAN_ATK = [
    'No', 'Tanggal Pengajuan', 'Bulan', 'Tahun', 'Departement',
    'Kode Barang', 'Nama Barang', 'Jumlah', 'Satuan',
    'Harga Satuan', 'Total Harga', 'Keterangan'
]
```

---

## Project Structure (Tambahan)

```
inventory-dpp/
├── app.py                          # Tambah routes ATK di sini
├── templates/
│   ├── base.html                   # Update navbar: tambah menu ATK
│   ├── index.html                  # (opsional) tambah stats ATK di dashboard
│   ├── kendaraan/                  # (existing, tidak diubah)
│   ├── service/                    # (existing, tidak diubah)
│   └── atk/                        # ======= FOLDER BARU =======
│       ├── master_list.html        # Tabel master data ATK
│       ├── master_form.html        # Form tambah/edit barang ATK
│       ├── dept_list.html          # Tabel master departement
│       ├── dept_form.html          # Form tambah/edit departement
│       ├── pengajuan_list.html     # Tabel pengajuan ATK (+ filter dept/bulan)
│       ├── pengajuan_form.html     # Form pengajuan ATK (multi-item)
│       └── rekap.html              # Halaman rekap pengajuan ATK
```

---

## Implementation Details

### 1. Routes ATK di `app.py`

Semua route ATK dikelompokkan di bawah prefix `/atk/`:

```python
# ============================================================
# ATK MODULE — Master Data ATK
# ============================================================

BULAN_LIST = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

@app.route('/atk/master')
def atk_master_list():
    """List semua barang ATK."""
    search = request.args.get('search', '').strip()
    try:
        sheet = get_sheet(SHEET_MASTER_ATK)
        if not sheet:
            flash('Tidak dapat terhubung ke sheet Master Data ATK.', 'error')
            return render_template('atk/master_list.html', records=[], search=search)
        records = get_all_data(sheet)
        if search:
            records = filter_records(records, search, ['Kode', 'Nama Barang'])
        return render_template('atk/master_list.html', records=records, search=search)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/master_list.html', records=[], search=search)


@app.route('/atk/master/tambah', methods=['GET', 'POST'])
def atk_master_tambah():
    """Form tambah barang ATK baru."""
    if request.method == 'POST':
        try:
            sheet = get_sheet(SHEET_MASTER_ATK)
            if not sheet:
                flash('Tidak dapat terhubung ke Google Sheets.', 'error')
                return redirect(url_for('atk_master_tambah'))
            no = get_next_no(sheet)
            row = [
                no,
                request.form.get('kode', ''),
                request.form.get('nama_barang', ''),
                request.form.get('perkiraan_harga', ''),
                request.form.get('satuan', ''),
            ]
            sheet.append_row(row, value_input_option='USER_ENTERED')
            flash(f'Barang ATK berhasil ditambahkan (No: {no}).', 'success')
            return redirect(url_for('atk_master_list'))
        except Exception as e:
            flash(f'Gagal menambah data: {str(e)}', 'error')
            return redirect(url_for('atk_master_tambah'))
    return render_template('atk/master_form.html', mode='tambah', data={})


@app.route('/atk/master/edit/<int:no>', methods=['GET', 'POST'])
def atk_master_edit(no):
    """Form edit barang ATK."""
    # Pattern sama dengan kendaraan_edit — load, update, redirect
    pass


@app.route('/atk/master/delete/<int:no>', methods=['POST'])
def atk_master_delete(no):
    """Hapus barang ATK."""
    # Pattern sama dengan kendaraan_delete
    pass


# ============================================================
# ATK MODULE — Master Departement
# ============================================================

@app.route('/atk/departement')
def atk_dept_list():
    """List semua departemen."""
    pass  # Pattern sama dengan atk_master_list


@app.route('/atk/departement/tambah', methods=['GET', 'POST'])
def atk_dept_tambah():
    """Form tambah departemen baru."""
    pass


@app.route('/atk/departement/edit/<int:no>', methods=['GET', 'POST'])
def atk_dept_edit(no):
    """Form edit departemen."""
    pass


@app.route('/atk/departement/delete/<int:no>', methods=['POST'])
def atk_dept_delete(no):
    """Hapus departemen."""
    pass


# ============================================================
# ATK MODULE — Pengajuan ATK
# ============================================================

@app.route('/atk/pengajuan')
def atk_pengajuan_list():
    """List pengajuan ATK dengan filter departement, bulan, tahun."""
    dept_filter = request.args.get('departement', '').strip()
    bulan_filter = request.args.get('bulan', '').strip()
    tahun_filter = request.args.get('tahun', '').strip()
    search = request.args.get('search', '').strip()

    try:
        sheet = get_sheet(SHEET_PENGAJUAN_ATK)
        records = get_all_data(sheet) if sheet else []

        # Apply filters
        if dept_filter:
            records = [r for r in records if r.get('Departement', '') == dept_filter]
        if bulan_filter:
            records = [r for r in records if r.get('Bulan', '') == bulan_filter]
        if tahun_filter:
            records = [r for r in records if str(r.get('Tahun', '')) == tahun_filter]
        if search:
            records = filter_records(records, search, ['Kode Barang', 'Nama Barang'])

        # Load dropdown data
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        dept_list = get_all_data(sheet_dept) if sheet_dept else []

        # Hitung total harga
        total_harga = sum(safe_num(r.get('Total Harga', 0)) for r in records)

        return render_template('atk/pengajuan_list.html',
                               records=records, search=search,
                               dept_filter=dept_filter, bulan_filter=bulan_filter,
                               tahun_filter=tahun_filter, dept_list=dept_list,
                               bulan_list=BULAN_LIST, total_harga=total_harga)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/pengajuan_list.html', records=[], ...)


@app.route('/atk/pengajuan/tambah', methods=['GET', 'POST'])
def atk_pengajuan_tambah():
    """Form pengajuan ATK (multi-item)."""
    if request.method == 'POST':
        # Loop setiap item yang disubmit (dynamic rows)
        # Setiap item → 1 row di sheet Pengajuan ATK
        pass

    # Load data untuk dropdown
    sheet_dept = get_sheet(SHEET_MASTER_DEPT)
    sheet_atk = get_sheet(SHEET_MASTER_ATK)
    dept_list = get_all_data(sheet_dept) if sheet_dept else []
    atk_list = get_all_data(sheet_atk) if sheet_atk else []

    return render_template('atk/pengajuan_form.html', mode='tambah',
                           dept_list=dept_list, atk_list=atk_list,
                           bulan_list=BULAN_LIST)


@app.route('/atk/pengajuan/edit/<int:no>', methods=['GET', 'POST'])
def atk_pengajuan_edit(no):
    """Edit pengajuan ATK per item."""
    pass


@app.route('/atk/pengajuan/delete/<int:no>', methods=['POST'])
def atk_pengajuan_delete(no):
    """Hapus pengajuan ATK."""
    pass


# ============================================================
# ATK MODULE — Rekap Pengajuan ATK
# ============================================================

@app.route('/atk/rekap')
def atk_rekap():
    """Halaman rekap pengajuan ATK."""
    bulan_filter = request.args.get('bulan', '').strip()
    tahun_filter = request.args.get('tahun', str(datetime.today().year)).strip()

    try:
        sheet = get_sheet(SHEET_PENGAJUAN_ATK)
        records = get_all_data(sheet) if sheet else []

        # Filter
        if bulan_filter:
            records = [r for r in records if r.get('Bulan', '') == bulan_filter]
        if tahun_filter:
            records = [r for r in records if str(r.get('Tahun', '')) == tahun_filter]

        # Rekap per departement
        dept_rekap = {}
        for r in records:
            dept = r.get('Departement', 'Tidak Diketahui')
            if dept not in dept_rekap:
                dept_rekap[dept] = {'jumlah_item': 0, 'total_harga': 0, 'items': []}
            dept_rekap[dept]['jumlah_item'] += 1
            dept_rekap[dept]['total_harga'] += safe_num(r.get('Total Harga', 0))
            dept_rekap[dept]['items'].append(r)

        # Rekap per barang
        barang_rekap = {}
        for r in records:
            kode = r.get('Kode Barang', '')
            if kode not in barang_rekap:
                barang_rekap[kode] = {
                    'nama': r.get('Nama Barang', ''),
                    'satuan': r.get('Satuan', ''),
                    'total_jumlah': 0,
                    'total_harga': 0
                }
            barang_rekap[kode]['total_jumlah'] += safe_num(r.get('Jumlah', 0))
            barang_rekap[kode]['total_harga'] += safe_num(r.get('Total Harga', 0))

        grand_total = sum(safe_num(r.get('Total Harga', 0)) for r in records)

        return render_template('atk/rekap.html',
                               dept_rekap=dept_rekap, barang_rekap=barang_rekap,
                               grand_total=grand_total,
                               bulan_filter=bulan_filter, tahun_filter=tahun_filter,
                               bulan_list=BULAN_LIST)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/rekap.html', dept_rekap={}, barang_rekap={},
                               grand_total=0, ...)
```

### 2. Auto-fill dengan JavaScript (pengajuan_form.html)

```javascript
// Data master ATK di-embed sebagai JSON di template
const masterATK = {{ atk_list | tojson }};

function onKodeBarangChange(selectEl, rowIndex) {
    const kode = selectEl.value;
    const item = masterATK.find(a => a['Kode'] === kode);
    if (item) {
        document.getElementById(`nama_barang_${rowIndex}`).value = item['Nama Barang'];
        document.getElementById(`satuan_${rowIndex}`).value = item['Satuan'];
        document.getElementById(`harga_satuan_${rowIndex}`).value = item['Perkiraan Harga'];
        hitungTotal(rowIndex);
    }
}

function hitungTotal(rowIndex) {
    const jumlah = parseFloat(document.getElementById(`jumlah_${rowIndex}`).value) || 0;
    const harga = parseFloat(document.getElementById(`harga_satuan_${rowIndex}`).value) || 0;
    document.getElementById(`total_harga_${rowIndex}`).value = jumlah * harga;
}
```

### 3. Dynamic Rows (Multi-item Form)

```javascript
let rowCount = 1;

function tambahBaris() {
    rowCount++;
    const container = document.getElementById('items-container');
    const newRow = document.createElement('div');
    newRow.id = `row_${rowCount}`;
    newRow.innerHTML = `
        <!-- Clone struktur baris pertama dengan index baru -->
        <!-- Kode Barang dropdown, Nama Barang, Jumlah, Satuan, Harga, Total, Keterangan -->
        <button type="button" onclick="hapusBaris(${rowCount})">×</button>
    `;
    container.appendChild(newRow);
}

function hapusBaris(index) {
    const row = document.getElementById(`row_${index}`);
    if (row) row.remove();
}
```

### 4. Template Guidelines (ATK)

- **Semua template extend `base.html`** yang sudah ada
- Gunakan TailwindCSS classes yang konsisten dengan modul Kendaraan
- Form `pengajuan_form.html` perlu JavaScript untuk:
  - Auto-fill saat pilih kode barang
  - Auto-hitung total harga
  - Dynamic rows (tambah/hapus item)
- Tabel `pengajuan_list.html` dan `rekap.html` harus responsive
- Filter menggunakan query parameter: `?departement=HRD&bulan=Januari&tahun=2026`
- Format currency Rupiah konsisten: `Rp 150.000`

---

## UI/UX Guidelines

### Konsistensi dengan Modul Existing
- Gunakan design system yang sama (warna, button, card, dll)
- **Primary Color:** Blue (`bg-blue-600`) — sama dengan modul Kendaraan
- **Secondary/Accent untuk ATK:** Emerald/Green indicators untuk membedakan menu ATK
- Ikon menu: 📋 atau 📝 untuk ATK

### Form Pengajuan (Multi-item)
- Layout: Card-based form
- Setiap item row menggunakan grid layout (Kode | Nama | Jumlah | Satuan | Harga | Total | Aksi)
- Tombol "Tambah Barang" — warna hijau (`bg-green-600`)
- Tombol hapus baris — warna merah kecil (`text-red-500`)
- Grand total dan jumlah item ditampilkan di footer form
- Animasi smooth saat tambah/hapus baris

### Halaman Rekap
- Card ringkasan di atas: Total Departemen, Total Item, Grand Total Harga
- Tabel rekap per departemen dengan expandable detail (accordion)
- Tabel rekap per barang di bawahnya
- Tombol cetak di pojok kanan atas

### Responsive
- Tabel harus scrollable horizontal di mobile (`overflow-x-auto`)
- Form multi-item di mobile: stack vertikal per item
- Filter dropdowns stack vertikal di mobile

---

## Acceptance Criteria

- [ ] Sheet `Master Data ATK` tersedia di Google Sheets dan CRUD berfungsi
- [ ] Sheet `Master Departement` tersedia di Google Sheets dan CRUD berfungsi
- [ ] Sheet `Pengajuan ATK` tersedia di Google Sheets
- [ ] Form pengajuan ATK berfungsi dengan auto-fill dari Master Data ATK
- [ ] Form pengajuan mendukung multi-item (dynamic rows) dalam satu submit
- [ ] Auto-hitung Total Harga = Jumlah × Harga Satuan berfungsi
- [ ] Halaman Lihat Pengajuan ATK — filter Departement, Bulan, Tahun berfungsi
- [ ] Halaman Lihat Pengajuan menampilkan total harga dari data yang ter-filter
- [ ] Edit & Delete pengajuan ATK berfungsi
- [ ] Halaman Rekap menampilkan ringkasan per Departement dan per Barang
- [ ] Rekap mendukung filter Bulan dan Tahun
- [ ] Detail per departemen expandable (accordion) di halaman Rekap
- [ ] Tombol Cetak Rekap berfungsi (print-friendly layout)
- [ ] Menu ATK ter-integrasi di navbar/sidebar `base.html`
- [ ] Flash messages muncul setelah setiap operasi (sukses/gagal)
- [ ] UI responsive dan konsisten dengan modul Kendaraan existing
- [ ] Semua route ATK accessible dan tidak conflict dengan route existing

---

## Notes untuk Developer

> **Target model:** Sonnet 4.x — pastikan instruksi eksplisit dan terstruktur.

1. **Integrasikan ke `app.py` existing** — jangan buat file app terpisah
2. **Gunakan helper functions yang sudah ada:** `get_sheet()`, `get_all_data()`, `find_row_by_no()`, `get_next_no()`, `filter_records()`, `format_currency()`, `safe_num()`
3. **Sheet names harus exact match** — `Master Data ATK`, `Master Departement`, `Pengajuan ATK`
4. **Sheets harus dibuat manual terlebih dahulu** di Google Sheets dengan header row sesuai schema
5. **Jangan ubah route/logic Kendaraan & Service** — hanya tambahkan modul ATK
6. **Format currency** — gunakan Jinja2 filter `|rupiah` yang sudah ada
7. **Date format** — gunakan `DD/MM/YYYY` konsisten dengan modul existing
8. **Auto-fill di form** — gunakan JavaScript client-side, embed data master sebagai JSON dari Jinja2
9. **Multi-item form** — setiap item dikirim sebagai array field: `kode_barang[]`, `jumlah[]`, dll. Di backend loop `request.form.getlist('kode_barang[]')`
10. **Rekap aggregation** — hitung di backend (Python), jangan andalkan Google Sheets formula
11. **Error handling** — wrap semua operasi Google Sheets dengan try-except (pattern sama dengan existing)
12. **Update `base.html`** — tambahkan menu group ATK, bisa collapsible submenu

---

## Urutan Implementasi (Suggested)

1. **Buat 3 sheets baru** di Google Sheets (`Master Data ATK`, `Master Departement`, `Pengajuan ATK`) dengan header row
2. **Tambah constants** di `app.py` (sheet names, headers, BULAN_LIST)
3. **Implementasi CRUD Master Departement** (lebih sederhana, 2 field saja)
4. **Implementasi CRUD Master Data ATK** (5 field)
5. **Update `base.html`** — tambah navigasi menu ATK
6. **Implementasi Form Pengajuan ATK** — multi-item, auto-fill, auto-hitung
7. **Implementasi Lihat Pengajuan ATK** — tabel + filter
8. **Implementasi Rekap Pengajuan ATK** — aggregation + expandable + print
9. **Testing end-to-end** — semua CRUD, filter, rekap
