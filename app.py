from flask import Flask, render_template, request, redirect, url_for, flash, session
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# --- Config ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'inventory-dpp-secret-2024')

# --- Google Sheets Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'credentials.json')
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'database-inventory-dpp')
PORT = int(os.getenv('PORT', 5000))

# Sheet names (exact match)
SHEET_KENDARAAN = 'Master Data Kendaraan'
SHEET_SERVICE_MOBIL = 'History Service Kendaraan Mobil'
SHEET_SERVICE_MOTOR = 'History Service Kendaraan Motor'

# Sheet names — ATK Module
SHEET_MASTER_ATK = 'Master Data ATK'
SHEET_MASTER_DEPT = 'Master Departement'
SHEET_PENGAJUAN_ATK = 'Pengajuan ATK'
SHEET_MASTER_USERS = 'Master Users'

# Headers untuk setiap sheet
HEADERS_KENDARAAN = [
    'No', 'No. Kendaraan', 'Pemilik', 'Merk', 'Model Kendaraan', 'Jenis/Type',
    'Warna', 'Tahun Kendaraan', 'No. Rangka', 'No. Mesin', 'STNK 1 Tahun',
    'Realisasi Pembayaran Pajak', 'STNK 5 Tahun', 'Tanggal Realisasi KIR',
    'No Asuransi', 'Nama Asuransi', 'Jenis Asuransi', 'Tanggal Berlaku Asuransi',
    'Periode Tahun Asuransi', 'Biaya Premi Asuransi', 'GPS/APCT', 'No. BPKB',
    'Posisi BPKB', 'Bahan Bakar', 'Keterangan'
]

HEADERS_SERVICE = [
    'No', 'No. Kendaraan', 'Nama Pemilik', 'Tanggal Service', 'Nama Bengkel',
    'Jenis Service', 'Jumlah Part', 'Satuan', 'Pengajuan', 'Realisasi', 'Total',
    'KM Awal', 'KM Akhir', 'Selisih KM', 'KM Selanjutnya', 'Keterangan'
]

# Headers — ATK Module
HEADERS_MASTER_ATK = ['No', 'Kode', 'Nama Barang', 'Perkiraan Harga', 'Satuan']
HEADERS_MASTER_DEPT = ['No', 'Departement']
HEADERS_PENGAJUAN_ATK = [
    'No', 'Tanggal Pengajuan', 'Bulan', 'Tahun', 'Departement',
    'Kode Barang', 'Nama Barang', 'Jumlah', 'Satuan',
    'Harga Satuan', 'Total Harga', 'Keterangan'
]
HEADERS_MASTER_USERS = ['No', 'Username', 'Password', 'Role']

BULAN_LIST = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]


def get_sheets_client():
    """Inisialisasi Google Sheets client."""
    try:
        # Coba ambil dari GOOGLE_SHEETS_CREDENTIALS_JSON atau GOOGLE_SHEETS_CREDENTIALS
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
        if not creds_json:
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            
        # Jika isinya adalah teks JSON mentah (dimulai dengan '{')
        if creds_json and creds_json.strip().startswith('{'):
            info = json.loads(creds_json)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            # Fallback ke file path lokal
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception:
        return None


def get_spreadsheet():
    """Buka spreadsheet."""
    client = get_sheets_client()
    if not client:
        return None
    try:
        return client.open(SPREADSHEET_NAME)
    except Exception:
        return None


def get_sheet(sheet_name):
    """Ambil worksheet berdasarkan nama."""
    spreadsheet = get_spreadsheet()
    if not spreadsheet:
        return None
    try:
        return spreadsheet.worksheet(sheet_name)
    except Exception:
        return None


def get_all_data(sheet):
    """Ambil semua data dari sheet sebagai list of dict."""
    try:
        return sheet.get_all_records()
    except Exception:
        return []


def find_row_by_no(sheet, no):
    """Cari baris berdasarkan kolom 'No' (kolom pertama)."""
    try:
        cell = sheet.find(str(no), in_column=1)
        return cell.row if cell else None
    except Exception:
        return None


def get_next_no(sheet):
    """Generate auto-increment No dari data existing."""
    try:
        records = sheet.get_all_records()
        if not records:
            return 1
        nos = [int(r.get('No', 0)) for r in records if str(r.get('No', '')).isdigit()]
        return max(nos) + 1 if nos else 1
    except Exception:
        return 1


def safe_num(val):
    """Konversi nilai terformat (seperti currency rupiah, desimal) ke float secara aman."""
    if val is None or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
        
    try:
        s = str(val).strip().replace('Rp', '').replace('rp', '').replace('RP', '').replace(' ', '')
        
        # Deteksi format ribuan/desimal Indonesia vs US
        if ',' in s:
            if '.' in s:
                if s.find('.') < s.find(','):
                    # Format ID: 150.000,00 -> 150000.00
                    s = s.replace('.', '').replace(',', '.')
                else:
                    # Format US: 150,000.00 -> 150000.00
                    s = s.replace(',', '')
            else:
                # Hanya ada koma (misal: 150.000,00 -> 150000.00 atau 150,5)
                parts = s.split(',')
                if len(parts) == 2 and len(parts[1]) == 3:
                    s = s.replace(',', '')
                else:
                    s = s.replace(',', '.')
        else:
            # Hanya ada titik (misal: 150.000 atau 2.000.000)
            if '.' in s:
                parts = s.split('.')
                if len(parts) > 2:
                    s = s.replace('.', '')
                elif len(parts) == 2 and len(parts[1]) == 3:
                    s = s.replace('.', '')
                    
        return float(s or 0)
    except Exception:
        return 0.0


def format_currency(value):
    """Format angka ke format Rupiah."""
    try:
        num = safe_num(value)
        return f"Rp {num:,.0f}".replace(',', '.')
    except Exception:
        return str(value)


def parse_date(date_str):
    """Parse tanggal dari format DD/MM/YYYY ke datetime object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), '%d/%m/%Y')
    except Exception:
        return None


def is_expiring_soon(date_str, days=30):
    """Cek apakah tanggal akan jatuh tempo dalam X hari ke depan."""
    d = parse_date(date_str)
    if not d:
        return False
    today = datetime.today()
    return today <= d <= today + timedelta(days=days)


def filter_records(records, search, fields):
    """Filter records berdasarkan keyword search di field tertentu."""
    if not search:
        return records
    search_lower = search.lower()
    result = []
    for r in records:
        for f in fields:
            if search_lower in str(r.get(f, '')).lower():
                result.append(r)
                break
    return result


def init_users_sheet():
    """Menginisialisasi sheet Master Users jika belum ada, dan membuat default admin."""
    try:
        sheet = get_sheet(SHEET_MASTER_USERS)
        if not sheet:
            spreadsheet = get_spreadsheet()
            if spreadsheet:
                sheet = spreadsheet.add_worksheet(title=SHEET_MASTER_USERS, rows="100", cols="4")
                sheet.append_row(HEADERS_MASTER_USERS, value_input_option='USER_ENTERED')
        
        # Cek jika sheet kosong (hanya header)
        records = get_all_data(sheet)
        if not records:
            default_pwd = generate_password_hash('admin123')
            row = [1, 'admin', default_pwd, 'admin']
            sheet.append_row(row, value_input_option='USER_ENTERED')
    except Exception as e:
        print(f"Error initializing users sheet: {e}")


def get_user_by_username(username):
    """Mencari user berdasarkan username (case-insensitive)."""
    try:
        init_users_sheet()
        sheet = get_sheet(SHEET_MASTER_USERS)
        if not sheet:
            return None
        records = get_all_data(sheet)
        for r in records:
            if str(r.get('Username', '')).strip().lower() == username.strip().lower():
                return r
        return None
    except Exception:
        return None


def login_required(roles=None):
    """Decorator untuk membatasi akses route berdasarkan role pengguna."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash('Silakan login terlebih dahulu untuk mengakses halaman ini.', 'warning')
                return redirect(url_for('login', next=request.url))
            if roles and session.get('role') not in roles:
                flash('Anda tidak memiliki hak akses ke modul ini.', 'error')
                return redirect(url_for('portal'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.before_request
def check_route_access():
    if request.endpoint is None:
        return
        
    # Endpoint bebas akses (tidak butuh login)
    public_endpoints = ['login', 'static']
    if request.endpoint in public_endpoints:
        return
        
    # Verifikasi apakah pengguna sudah login
    if 'user' not in session:
        flash('Silakan login terlebih dahulu untuk mengakses halaman ini.', 'warning')
        return redirect(url_for('login', next=request.url))
        
    # Verifikasi hak akses berdasarkan role pengguna
    role = session.get('role')
    
    # Admin memiliki akses ke semua halaman
    if role == 'admin':
        return
        
    # Halaman manajemen pengguna hanya untuk Admin
    if request.path.startswith('/admin'):
        flash('Halaman ini hanya dapat diakses oleh Admin.', 'error')
        return redirect(url_for('portal'))
        
    # Pembatasan akses Modul Kendaraan & Service
    if request.path.startswith('/kendaraan') or request.path.startswith('/service'):
        if role != 'kendaraan':
            flash('Anda tidak memiliki hak akses ke modul Kendaraan & Service.', 'error')
            return redirect(url_for('portal'))
            
    # Pembatasan akses Modul ATK
    if request.path.startswith('/atk'):
        if role != 'atk':
            flash('Anda tidak memiliki hak akses ke modul ATK.', 'error')
            return redirect(url_for('portal'))



# ============================================================
# Jinja2 filters
# ============================================================
@app.template_filter('rupiah')
def rupiah_filter(value):
    return format_currency(value)


@app.template_filter('expiring')
def expiring_filter(value, days=30):
    return is_expiring_soon(value, days)


@app.template_filter('clean_num')
def clean_num_filter(value):
    num = safe_num(value)
    if num.is_integer():
        return int(num)
    return num



# ============================================================
# AUTHENTICATION
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('portal'))
        
    next_url = request.args.get('next', '')
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = get_user_by_username(username)
        if user:
            pwd_hash = user.get('Password', '')
            if check_password_hash(pwd_hash, password):
                session['user'] = user.get('Username')
                session['role'] = user.get('Role')
                flash(f'Selamat datang kembali, {user.get("Username")}!', 'success')
                
                if username.lower() == 'admin' and password == 'admin123':
                    flash('PERINGATAN KEAMANAN: Harap segera ubah password default admin Anda!', 'error')
                
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('portal'))
                
        flash('Username atau password salah.', 'error')
        
    return render_template('login.html', next_url=next_url)


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))


# ============================================================
# USER MANAGEMENT (ADMIN ONLY)
# ============================================================
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required(roles=['admin'])
def admin_users():
    try:
        sheet = get_sheet(SHEET_MASTER_USERS)
        if not sheet:
            flash('Gagal mengakses sheet Master Users.', 'error')
            return redirect(url_for('portal'))
            
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', '').strip()
            
            if not username or not password or not role:
                flash('Semua field wajib diisi.', 'error')
            else:
                existing = get_user_by_username(username)
                if existing:
                    flash(f'Username {username} sudah terdaftar.', 'error')
                else:
                    no = get_next_no(sheet)
                    pwd_hash = generate_password_hash(password)
                    row = [no, username, pwd_hash, role]
                    sheet.append_row(row, value_input_option='USER_ENTERED')
                    flash(f'User {username} berhasil ditambahkan.', 'success')
            return redirect(url_for('admin_users'))
            
        records = get_all_data(sheet)
        return render_template('admin_users.html', users=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('portal'))


@app.route('/admin/users/delete/<int:no>', methods=['POST'])
@login_required(roles=['admin'])
def admin_user_delete(no):
    try:
        sheet = get_sheet(SHEET_MASTER_USERS)
        if not sheet:
            flash('Gagal mengakses sheet.', 'error')
            return redirect(url_for('admin_users'))
            
        records = get_all_data(sheet)
        target = next((r for r in records if str(r.get('No', '')) == str(no)), None)
        if target and target.get('Username') == session.get('user'):
            flash('Anda tidak dapat menghapus akun Anda sendiri.', 'error')
            return redirect(url_for('admin_users'))
            
        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash('User tidak ditemukan.', 'error')
            return redirect(url_for('admin_users'))
            
        sheet.delete_rows(row_num)
        flash('User berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus user: {str(e)}', 'error')
    return redirect(url_for('admin_users'))


# ============================================================
# PORTAL PAGE
# ============================================================
@app.route('/')
@login_required()
def portal():
    return render_template('portal.html')


# ============================================================
# KENDARAAN DASHBOARD
# ============================================================
@app.route('/kendaraan/dashboard')
def kendaraan_dashboard():
    try:
        sheet_k = get_sheet(SHEET_KENDARAAN)
        sheet_sm = get_sheet(SHEET_SERVICE_MOBIL)
        sheet_mo = get_sheet(SHEET_SERVICE_MOTOR)

        kendaraan = get_all_data(sheet_k) if sheet_k else []
        service_mobil = get_all_data(sheet_sm) if sheet_sm else []
        service_motor = get_all_data(sheet_mo) if sheet_mo else []

        total_kendaraan = len(kendaraan)

        # Hitung STNK jatuh tempo (30 hari ke depan)
        stnk_expiring = sum(
            1 for k in kendaraan
            if is_expiring_soon(k.get('STNK 1 Tahun', '')) or
               is_expiring_soon(k.get('STNK 5 Tahun', ''))
        )

        # Hitung Asuransi expiring
        asuransi_expiring = sum(
            1 for k in kendaraan
            if is_expiring_soon(k.get('Tanggal Berlaku Asuransi', ''))
        )

        # Hitung KIR (yang sudah lebih dari setahun dari realisasi KIR)
        kir_expiring = sum(
            1 for k in kendaraan
            if k.get('Tanggal Realisasi KIR', '')
        )

        # Statistik service
        total_service_mobil = len(service_mobil)
        total_service_motor = len(service_motor)

        # 5 kendaraan terbaru
        recent_kendaraan = kendaraan[-5:][::-1] if kendaraan else []

        # Kendaraan dengan STNK akan jatuh tempo
        stnk_list = [
            k for k in kendaraan
            if is_expiring_soon(k.get('STNK 1 Tahun', ''), 60) or
               is_expiring_soon(k.get('STNK 5 Tahun', ''), 60)
        ][:5]

        return render_template(
            'index.html',
            total_kendaraan=total_kendaraan,
            stnk_expiring=stnk_expiring,
            asuransi_expiring=asuransi_expiring,
            kir_expiring=kir_expiring,
            total_service_mobil=total_service_mobil,
            total_service_motor=total_service_motor,
            recent_kendaraan=recent_kendaraan,
            stnk_list=stnk_list,
            sheet_connected=(sheet_k is not None)
        )
    except Exception as e:
        flash(f'Error memuat dashboard: {str(e)}', 'error')
        return render_template('index.html',
                               total_kendaraan=0, stnk_expiring=0,
                               asuransi_expiring=0, kir_expiring=0,
                               total_service_mobil=0, total_service_motor=0,
                               recent_kendaraan=[], stnk_list=[],
                               sheet_connected=False)


# ============================================================
# MASTER DATA KENDARAAN
# ============================================================
@app.route('/kendaraan')
def kendaraan_list():
    search = request.args.get('search', '').strip()
    try:
        sheet = get_sheet(SHEET_KENDARAAN)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets. Periksa credentials.json.', 'error')
            return render_template('kendaraan/list.html', kendaraan=[], search=search)

        records = get_all_data(sheet)
        if search:
            records = filter_records(
                records, search,
                ['No. Kendaraan', 'Pemilik', 'Merk', 'Model Kendaraan', 'Jenis/Type']
            )

        return render_template('kendaraan/list.html', kendaraan=records, search=search)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('kendaraan/list.html', kendaraan=[], search=search)


@app.route('/kendaraan/tambah', methods=['GET', 'POST'])
def kendaraan_tambah():
    if request.method == 'POST':
        try:
            sheet = get_sheet(SHEET_KENDARAAN)
            if not sheet:
                flash('Tidak dapat terhubung ke Google Sheets.', 'error')
                return redirect(url_for('kendaraan_tambah'))

            no = get_next_no(sheet)
            row = [
                no,
                request.form.get('no_kendaraan', ''),
                request.form.get('pemilik', ''),
                request.form.get('merk', ''),
                request.form.get('model_kendaraan', ''),
                request.form.get('jenis_type', ''),
                request.form.get('warna', ''),
                request.form.get('tahun_kendaraan', ''),
                request.form.get('no_rangka', ''),
                request.form.get('no_mesin', ''),
                request.form.get('stnk_1_tahun', ''),
                request.form.get('realisasi_pajak', ''),
                request.form.get('stnk_5_tahun', ''),
                request.form.get('tgl_realisasi_kir', ''),
                request.form.get('no_asuransi', ''),
                request.form.get('nama_asuransi', ''),
                request.form.get('jenis_asuransi', ''),
                request.form.get('tgl_berlaku_asuransi', ''),
                request.form.get('periode_asuransi', ''),
                request.form.get('biaya_premi_asuransi', ''),
                request.form.get('gps_apct', ''),
                request.form.get('no_bpkb', ''),
                request.form.get('posisi_bpkb', ''),
                request.form.get('bahan_bakar', ''),
                request.form.get('keterangan', '')
            ]
            sheet.append_row(row, value_input_option='USER_ENTERED')
            flash(f'Data kendaraan berhasil ditambahkan (No: {no}).', 'success')
            return redirect(url_for('kendaraan_list'))
        except Exception as e:
            flash(f'Gagal menambah data: {str(e)}', 'error')
            return redirect(url_for('kendaraan_tambah'))

    return render_template('kendaraan/form.html', mode='tambah', data={})


@app.route('/kendaraan/edit/<int:no>', methods=['GET', 'POST'])
def kendaraan_edit(no):
    try:
        sheet = get_sheet(SHEET_KENDARAAN)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('kendaraan_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data kendaraan No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('kendaraan_list'))

        if request.method == 'POST':
            row = [
                no,
                request.form.get('no_kendaraan', ''),
                request.form.get('pemilik', ''),
                request.form.get('merk', ''),
                request.form.get('model_kendaraan', ''),
                request.form.get('jenis_type', ''),
                request.form.get('warna', ''),
                request.form.get('tahun_kendaraan', ''),
                request.form.get('no_rangka', ''),
                request.form.get('no_mesin', ''),
                request.form.get('stnk_1_tahun', ''),
                request.form.get('realisasi_pajak', ''),
                request.form.get('stnk_5_tahun', ''),
                request.form.get('tgl_realisasi_kir', ''),
                request.form.get('no_asuransi', ''),
                request.form.get('nama_asuransi', ''),
                request.form.get('jenis_asuransi', ''),
                request.form.get('tgl_berlaku_asuransi', ''),
                request.form.get('periode_asuransi', ''),
                request.form.get('biaya_premi_asuransi', ''),
                request.form.get('gps_apct', ''),
                request.form.get('no_bpkb', ''),
                request.form.get('posisi_bpkb', ''),
                request.form.get('bahan_bakar', ''),
                request.form.get('keterangan', '')
            ]
            sheet.update(f'A{row_num}:Y{row_num}', [row], value_input_option='USER_ENTERED')
            flash(f'Data kendaraan No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for('kendaraan_list'))

        # GET - load existing data
        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})
        return render_template('kendaraan/form.html', mode='edit', data=data, no=no)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('kendaraan_list'))


@app.route('/kendaraan/delete/<int:no>', methods=['POST'])
def kendaraan_delete(no):
    try:
        sheet = get_sheet(SHEET_KENDARAAN)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('kendaraan_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('kendaraan_list'))

        sheet.delete_rows(row_num)
        flash(f'Data kendaraan No. {no} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus data: {str(e)}', 'error')

    return redirect(url_for('kendaraan_list'))


@app.route('/kendaraan/update-dokumen/<int:no>', methods=['GET', 'POST'])
def kendaraan_update_dokumen(no):
    try:
        sheet = get_sheet(SHEET_KENDARAAN)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('kendaraan_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data kendaraan No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('kendaraan_list'))

        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})

        if request.method == 'POST':
            # Update hanya field dokumen (kolom L sampai T = index 12-20)
            # STNK 1 Tahun=L(12), Realisasi Pajak=M(13), STNK 5 Tahun=N(14),
            # Tgl KIR=O(15), No Asuransi=P(16), Nama Asuransi=Q(17),
            # Jenis Asuransi=R(18), Tgl Berlaku Asuransi=S(19), Periode Asuransi=T(20),
            # Biaya Premi Asuransi=U(21)
            updates = [
                [request.form.get('stnk_1_tahun', ''),
                 request.form.get('realisasi_pajak', ''),
                 request.form.get('stnk_5_tahun', ''),
                 request.form.get('tgl_realisasi_kir', ''),
                 request.form.get('no_asuransi', ''),
                 request.form.get('nama_asuransi', ''),
                 request.form.get('jenis_asuransi', ''),
                 request.form.get('tgl_berlaku_asuransi', ''),
                 request.form.get('periode_asuransi', ''),
                 request.form.get('biaya_premi_asuransi', '')]
            ]
            sheet.update(f'L{row_num}:U{row_num}', updates, value_input_option='USER_ENTERED')
            flash(f'Dokumen kendaraan No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for('kendaraan_list'))

        return render_template('kendaraan/update_dokumen.html', data=data, no=no)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('kendaraan_list'))


# ============================================================
# SERVICE KENDARAAN (MOBIL & MOTOR)
# ============================================================
def service_list_view(jenis):
    """View untuk list history service (reusable untuk mobil & motor)."""
    sheet_name = SHEET_SERVICE_MOBIL if jenis == 'mobil' else SHEET_SERVICE_MOTOR
    search = request.args.get('search', '').strip()
    try:
        sheet = get_sheet(sheet_name)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return render_template('service/list.html', records=[], search=search, jenis=jenis)

        records = get_all_data(sheet)
        if search:
            records = filter_records(
                records, search,
                ['No. Kendaraan', 'Nama Pemilik', 'Tanggal Service', 'Nama Bengkel', 'Jenis Service']
            )
        return render_template('service/list.html', records=records, search=search, jenis=jenis)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('service/list.html', records=[], search=search, jenis=jenis)


def service_tambah_view(jenis):
    """View untuk form tambah history service."""
    sheet_name = SHEET_SERVICE_MOBIL if jenis == 'mobil' else SHEET_SERVICE_MOTOR
    if request.method == 'POST':
        try:
            sheet = get_sheet(sheet_name)
            if not sheet:
                flash('Tidak dapat terhubung ke Google Sheets.', 'error')
                return redirect(url_for(f'service_{jenis}_tambah'))

            no = get_next_no(sheet)
            # Auto-hitung selisih KM
            try:
                km_awal = int(request.form.get('km_awal', 0) or 0)
                km_akhir = int(request.form.get('km_akhir', 0) or 0)
                selisih_km = km_akhir - km_awal
            except ValueError:
                km_awal = 0
                km_akhir = 0
                selisih_km = 0

            # Auto-hitung total
            try:
                pengajuan = float(str(request.form.get('pengajuan', 0)).replace('.', '').replace(',', '') or 0)
                realisasi = float(str(request.form.get('realisasi', 0)).replace('.', '').replace(',', '') or 0)
                total = realisasi  # Total = Realisasi
            except ValueError:
                pengajuan = 0
                realisasi = 0
                total = 0

            row = [
                no,
                request.form.get('no_kendaraan', ''),
                request.form.get('nama_pemilik', ''),
                request.form.get('tanggal_service', ''),
                request.form.get('nama_bengkel', ''),
                request.form.get('jenis_service', ''),
                request.form.get('jumlah_part', ''),
                request.form.get('satuan', ''),
                pengajuan,
                realisasi,
                total,
                km_awal,
                km_akhir,
                selisih_km,
                request.form.get('km_selanjutnya', ''),
                request.form.get('keterangan', '')
            ]
            sheet.append_row(row, value_input_option='USER_ENTERED')
            flash(f'History service berhasil ditambahkan (No: {no}).', 'success')
            return redirect(url_for(f'service_{jenis}_list'))
        except Exception as e:
            flash(f'Gagal menambah data: {str(e)}', 'error')
            return redirect(url_for(f'service_{jenis}_tambah'))

    # Load daftar kendaraan untuk dropdown
    try:
        sheet_k = get_sheet(SHEET_KENDARAAN)
        kendaraan_list = get_all_data(sheet_k) if sheet_k else []
    except Exception:
        kendaraan_list = []

    return render_template('service/form.html', mode='tambah', data={}, jenis=jenis,
                           kendaraan_list=kendaraan_list)


def service_edit_view(jenis, no):
    """View untuk edit history service."""
    sheet_name = SHEET_SERVICE_MOBIL if jenis == 'mobil' else SHEET_SERVICE_MOTOR
    try:
        sheet = get_sheet(sheet_name)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for(f'service_{jenis}_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for(f'service_{jenis}_list'))

        if request.method == 'POST':
            try:
                km_awal = int(request.form.get('km_awal', 0) or 0)
                km_akhir = int(request.form.get('km_akhir', 0) or 0)
                selisih_km = km_akhir - km_awal
            except ValueError:
                km_awal = 0
                km_akhir = 0
                selisih_km = 0

            try:
                pengajuan = float(str(request.form.get('pengajuan', 0)).replace('.', '').replace(',', '') or 0)
                realisasi = float(str(request.form.get('realisasi', 0)).replace('.', '').replace(',', '') or 0)
                total = realisasi
            except ValueError:
                pengajuan = 0
                realisasi = 0
                total = 0

            row = [
                no,
                request.form.get('no_kendaraan', ''),
                request.form.get('nama_pemilik', ''),
                request.form.get('tanggal_service', ''),
                request.form.get('nama_bengkel', ''),
                request.form.get('jenis_service', ''),
                request.form.get('jumlah_part', ''),
                request.form.get('satuan', ''),
                pengajuan,
                realisasi,
                total,
                km_awal,
                km_akhir,
                selisih_km,
                request.form.get('km_selanjutnya', ''),
                request.form.get('keterangan', '')
            ]
            sheet.update(f'A{row_num}:P{row_num}', [row], value_input_option='USER_ENTERED')
            flash(f'Data service No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for(f'service_{jenis}_list'))

        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})

        try:
            sheet_k = get_sheet(SHEET_KENDARAAN)
            kendaraan_list = get_all_data(sheet_k) if sheet_k else []
        except Exception:
            kendaraan_list = []

        return render_template('service/form.html', mode='edit', data=data, no=no, jenis=jenis,
                               kendaraan_list=kendaraan_list)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for(f'service_{jenis}_list'))


def service_delete_view(jenis, no):
    """View untuk hapus history service."""
    sheet_name = SHEET_SERVICE_MOBIL if jenis == 'mobil' else SHEET_SERVICE_MOTOR
    try:
        sheet = get_sheet(sheet_name)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for(f'service_{jenis}_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for(f'service_{jenis}_list'))

        sheet.delete_rows(row_num)
        flash(f'Data service No. {no} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus data: {str(e)}', 'error')

    return redirect(url_for(f'service_{jenis}_list'))


# ---- Routes Service Mobil ----
@app.route('/service/mobil')
def service_mobil_list():
    return service_list_view('mobil')


@app.route('/service/mobil/tambah', methods=['GET', 'POST'])
def service_mobil_tambah():
    return service_tambah_view('mobil')


@app.route('/service/mobil/edit/<int:no>', methods=['GET', 'POST'])
def service_mobil_edit(no):
    return service_edit_view('mobil', no)


@app.route('/service/mobil/delete/<int:no>', methods=['POST'])
def service_mobil_delete(no):
    return service_delete_view('mobil', no)


# ---- Routes Service Motor ----
@app.route('/service/motor')
def service_motor_list():
    return service_list_view('motor')


@app.route('/service/motor/tambah', methods=['GET', 'POST'])
def service_motor_tambah():
    return service_tambah_view('motor')


@app.route('/service/motor/edit/<int:no>', methods=['GET', 'POST'])
def service_motor_edit(no):
    return service_edit_view('motor', no)


@app.route('/service/motor/delete/<int:no>', methods=['POST'])
def service_motor_delete(no):
    return service_delete_view('motor', no)


# ============================================================
# TRACKING HISTORY SERVICE PER KENDARAAN
# ============================================================
@app.route('/kendaraan/tracking/<no_kendaraan>')
def kendaraan_tracking(no_kendaraan):
    """Halaman tracking history service lengkap per kendaraan."""
    try:
        # Load data kendaraan
        sheet_k = get_sheet(SHEET_KENDARAAN)
        kendaraan_records = get_all_data(sheet_k) if sheet_k else []
        kendaraan = next(
            (k for k in kendaraan_records
             if str(k.get('No. Kendaraan', '')).strip().upper() == no_kendaraan.strip().upper()),
            None
        )

        # Load history service mobil & motor, filter by no_kendaraan
        sheet_sm = get_sheet(SHEET_SERVICE_MOBIL)
        sheet_mo = get_sheet(SHEET_SERVICE_MOTOR)
        all_mobil = get_all_data(sheet_sm) if sheet_sm else []
        all_motor = get_all_data(sheet_mo) if sheet_mo else []

        service_mobil = [
            r for r in all_mobil
            if str(r.get('No. Kendaraan', '')).strip().upper() == no_kendaraan.strip().upper()
        ]
        service_motor = [
            r for r in all_motor
            if str(r.get('No. Kendaraan', '')).strip().upper() == no_kendaraan.strip().upper()
        ]

        # Gabungkan semua service dengan label jenis
        for r in service_mobil:
            r['_jenis'] = 'mobil'
        for r in service_motor:
            r['_jenis'] = 'motor'

        all_service = service_mobil + service_motor

        # Sort berdasarkan tanggal service (ascending)
        def sort_key(r):
            d = parse_date(r.get('Tanggal Service', ''))
            return d if d else datetime.min

        all_service_sorted = sorted(all_service, key=sort_key)

        # ---- Statistik ----
        total_service = len(all_service_sorted)

        # Total biaya
        total_pengajuan = sum(safe_num(r.get('Pengajuan', 0)) for r in all_service_sorted)
        total_realisasi = sum(safe_num(r.get('Realisasi', 0)) for r in all_service_sorted)
        total_biaya = sum(safe_num(r.get('Total', 0)) for r in all_service_sorted)

        # KM tracking — ambil urutan KM dari semua service
        km_records = [
            {
                'tanggal': r.get('Tanggal Service', ''),
                'km_awal': safe_num(r.get('KM Awal', 0)),
                'km_akhir': safe_num(r.get('KM Akhir', 0)),
                'selisih': safe_num(r.get('Selisih KM', 0)),
                'km_selanjutnya': safe_num(r.get('KM Selanjutnya', 0)),
                'jenis_service': r.get('Jenis Service', ''),
                'bengkel': r.get('Nama Bengkel', ''),
                '_jenis': r.get('_jenis', ''),
            }
            for r in all_service_sorted
            if safe_num(r.get('KM Akhir', 0)) > 0
        ]

        # KM terakhir & next service
        last_km = 0
        next_service_km = 0
        if km_records:
            last_km = int(km_records[-1]['km_akhir'])
            next_service_km = int(km_records[-1]['km_selanjutnya'])

        # Jenis service terbanyak
        jenis_count = {}
        for r in all_service_sorted:
            js = r.get('Jenis Service', 'Lainnya') or 'Lainnya'
            jenis_count[js] = jenis_count.get(js, 0) + 1
        jenis_sorted = sorted(jenis_count.items(), key=lambda x: x[1], reverse=True)

        # Service terakhir
        last_service = all_service_sorted[-1] if all_service_sorted else None

        return render_template(
            'kendaraan/tracking.html',
            kendaraan=kendaraan,
            no_kendaraan=no_kendaraan,
            all_service=all_service_sorted,
            service_mobil=service_mobil,
            service_motor=service_motor,
            total_service=total_service,
            total_pengajuan=total_pengajuan,
            total_realisasi=total_realisasi,
            total_biaya=total_biaya,
            km_records=km_records,
            last_km=last_km,
            next_service_km=next_service_km,
            jenis_sorted=jenis_sorted,
            last_service=last_service,
        )
    except Exception as e:
        flash(f'Error memuat tracking: {str(e)}', 'error')
        return redirect(url_for('kendaraan_list'))


# ============================================================
# ATK MODULE — Dashboard
# ============================================================
@app.route('/atk/dashboard')
def atk_dashboard():
    """Halaman Dashboard ATK dengan ringkasan statistik."""
    try:
        sheet_atk = get_sheet(SHEET_MASTER_ATK)
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        sheet_pengajuan = get_sheet(SHEET_PENGAJUAN_ATK)

        master_atk = get_all_data(sheet_atk) if sheet_atk else []
        departments = get_all_data(sheet_dept) if sheet_dept else []
        pengajuan = get_all_data(sheet_pengajuan) if sheet_pengajuan else []

        total_barang = len(master_atk)
        total_dept = len(departments)
        total_pengajuan = len(pengajuan)
        grand_total = sum(safe_num(r.get('Total Harga', 0)) for r in pengajuan)

        # 5 pengajuan terbaru
        recent_pengajuan = pengajuan[-5:][::-1] if pengajuan else []

        return render_template(
            'atk/dashboard.html',
            total_barang=total_barang,
            total_dept=total_dept,
            total_pengajuan=total_pengajuan,
            grand_total=grand_total,
            recent_pengajuan=recent_pengajuan,
            sheet_connected=(sheet_atk is not None)
        )
    except Exception as e:
        flash(f'Error memuat dashboard ATK: {str(e)}', 'error')
        return render_template('atk/dashboard.html',
                               total_barang=0, total_dept=0,
                               total_pengajuan=0, grand_total=0,
                               recent_pengajuan=[],
                               sheet_connected=False)


# ============================================================
# ATK MODULE — Master Data ATK
# ============================================================

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
            records = filter_records(records, search, ['Kode', 'Nama Barang', 'Satuan'])
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
                request.form.get('kode', '').strip(),
                request.form.get('nama_barang', '').strip(),
                request.form.get('perkiraan_harga', '').strip(),
                request.form.get('satuan', '').strip(),
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
    try:
        sheet = get_sheet(SHEET_MASTER_ATK)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_master_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data ATK No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_master_list'))

        if request.method == 'POST':
            row = [
                no,
                request.form.get('kode', '').strip(),
                request.form.get('nama_barang', '').strip(),
                request.form.get('perkiraan_harga', '').strip(),
                request.form.get('satuan', '').strip(),
            ]
            sheet.update(f'A{row_num}:E{row_num}', [row], value_input_option='USER_ENTERED')
            flash(f'Data ATK No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for('atk_master_list'))

        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})
        return render_template('atk/master_form.html', mode='edit', data=data, no=no)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('atk_master_list'))


@app.route('/atk/master/delete/<int:no>', methods=['POST'])
def atk_master_delete(no):
    """Hapus barang ATK."""
    try:
        sheet = get_sheet(SHEET_MASTER_ATK)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_master_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_master_list'))

        sheet.delete_rows(row_num)
        flash(f'Barang ATK No. {no} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus data: {str(e)}', 'error')

    return redirect(url_for('atk_master_list'))


# ============================================================
# ATK MODULE — Master Departement
# ============================================================

@app.route('/atk/departement')
def atk_dept_list():
    """List semua departemen."""
    search = request.args.get('search', '').strip()
    try:
        sheet = get_sheet(SHEET_MASTER_DEPT)
        if not sheet:
            flash('Tidak dapat terhubung ke sheet Master Departement.', 'error')
            return render_template('atk/dept_list.html', records=[], search=search)
        records = get_all_data(sheet)
        if search:
            records = filter_records(records, search, ['Departement'])
        return render_template('atk/dept_list.html', records=records, search=search)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/dept_list.html', records=[], search=search)


@app.route('/atk/departement/tambah', methods=['GET', 'POST'])
def atk_dept_tambah():
    """Form tambah departemen baru."""
    if request.method == 'POST':
        try:
            sheet = get_sheet(SHEET_MASTER_DEPT)
            if not sheet:
                flash('Tidak dapat terhubung ke Google Sheets.', 'error')
                return redirect(url_for('atk_dept_tambah'))
            no = get_next_no(sheet)
            row = [
                no,
                request.form.get('departement', '').strip(),
            ]
            sheet.append_row(row, value_input_option='USER_ENTERED')
            flash(f'Departemen berhasil ditambahkan (No: {no}).', 'success')
            return redirect(url_for('atk_dept_list'))
        except Exception as e:
            flash(f'Gagal menambah data: {str(e)}', 'error')
            return redirect(url_for('atk_dept_tambah'))
    return render_template('atk/dept_form.html', mode='tambah', data={})


@app.route('/atk/departement/edit/<int:no>', methods=['GET', 'POST'])
def atk_dept_edit(no):
    """Form edit departemen."""
    try:
        sheet = get_sheet(SHEET_MASTER_DEPT)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_dept_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data Departemen No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_dept_list'))

        if request.method == 'POST':
            row = [
                no,
                request.form.get('departement', '').strip(),
            ]
            sheet.update(f'A{row_num}:B{row_num}', [row], value_input_option='USER_ENTERED')
            flash(f'Departemen No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for('atk_dept_list'))

        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})
        return render_template('atk/dept_form.html', mode='edit', data=data, no=no)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('atk_dept_list'))


@app.route('/atk/departement/delete/<int:no>', methods=['POST'])
def atk_dept_delete(no):
    """Hapus departemen."""
    try:
        sheet = get_sheet(SHEET_MASTER_DEPT)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_dept_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_dept_list'))

        sheet.delete_rows(row_num)
        flash(f'Departemen No. {no} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus data: {str(e)}', 'error')

    return redirect(url_for('atk_dept_list'))


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
            records = [r for r in records if str(r.get('Departement', '')) == dept_filter]
        if bulan_filter:
            records = [r for r in records if str(r.get('Bulan', '')) == bulan_filter]
        if tahun_filter:
            records = [r for r in records if str(r.get('Tahun', '')) == str(tahun_filter)]
        if search:
            records = filter_records(records, search, ['Kode Barang', 'Nama Barang', 'Keterangan'])

        # Load dropdown data
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        dept_list = get_all_data(sheet_dept) if sheet_dept else []

        # Hitung total harga
        total_harga = sum(safe_num(r.get('Total Harga', 0)) for r in records)

        # Get unique tahun for filter dropdown
        all_records = get_all_data(sheet) if sheet else []
        tahun_set = sorted(set(str(r.get('Tahun', '')) for r in all_records if r.get('Tahun', '')), reverse=True)

        return render_template('atk/pengajuan_list.html',
                               records=records, search=search,
                               dept_filter=dept_filter, bulan_filter=bulan_filter,
                               tahun_filter=tahun_filter, dept_list=dept_list,
                               bulan_list=BULAN_LIST, total_harga=total_harga,
                               tahun_set=tahun_set)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/pengajuan_list.html',
                               records=[], search='',
                               dept_filter='', bulan_filter='',
                               tahun_filter='', dept_list=[],
                               bulan_list=BULAN_LIST, total_harga=0,
                               tahun_set=[])


@app.route('/atk/pengajuan/tambah', methods=['GET', 'POST'])
def atk_pengajuan_tambah():
    """Form pengajuan ATK (multi-item)."""
    if request.method == 'POST':
        try:
            sheet = get_sheet(SHEET_PENGAJUAN_ATK)
            if not sheet:
                flash('Tidak dapat terhubung ke Google Sheets.', 'error')
                return redirect(url_for('atk_pengajuan_tambah'))

            departement = request.form.get('departement', '').strip()
            bulan = request.form.get('bulan', '').strip()
            tahun = request.form.get('tahun', '').strip()
            tanggal = request.form.get('tanggal_pengajuan', '').strip()

            # Multi-item — ambil data dari field array
            kode_list = request.form.getlist('kode_barang[]')
            nama_list = request.form.getlist('nama_barang[]')
            jumlah_list = request.form.getlist('jumlah[]')
            satuan_list = request.form.getlist('satuan[]')
            harga_list = request.form.getlist('harga_satuan[]')
            ket_list = request.form.getlist('keterangan_item[]')

            count = 0
            for i in range(len(kode_list)):
                kode = kode_list[i].strip() if i < len(kode_list) else ''
                nama = nama_list[i].strip() if i < len(nama_list) else ''
                jumlah_str = jumlah_list[i].strip() if i < len(jumlah_list) else '0'
                satuan = satuan_list[i].strip() if i < len(satuan_list) else ''
                harga_str = harga_list[i].strip() if i < len(harga_list) else '0'
                ket = ket_list[i].strip() if i < len(ket_list) else ''

                if not kode or not nama:
                    continue  # Skip empty rows

                try:
                    jumlah = float(jumlah_str) if jumlah_str else 0
                    harga = float(harga_str) if harga_str else 0
                    total = jumlah * harga
                except ValueError:
                    jumlah = 0
                    harga = 0
                    total = 0

                no = get_next_no(sheet)
                row = [
                    no, tanggal, bulan, tahun, departement,
                    kode, nama, jumlah, satuan, harga, total, ket
                ]
                sheet.append_row(row, value_input_option='USER_ENTERED')
                count += 1

            if count > 0:
                flash(f'{count} item pengajuan ATK berhasil disimpan.', 'success')
            else:
                flash('Tidak ada item yang valid untuk disimpan.', 'error')
            return redirect(url_for('atk_pengajuan_list'))
        except Exception as e:
            flash(f'Gagal menyimpan pengajuan: {str(e)}', 'error')
            return redirect(url_for('atk_pengajuan_tambah'))

    # GET — load data untuk dropdown
    try:
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        sheet_atk = get_sheet(SHEET_MASTER_ATK)
        dept_list = get_all_data(sheet_dept) if sheet_dept else []
        atk_list = get_all_data(sheet_atk) if sheet_atk else []
    except Exception:
        dept_list = []
        atk_list = []

    today = datetime.today().strftime('%d/%m/%Y')
    current_year = datetime.today().year

    return render_template('atk/pengajuan_form.html', mode='tambah',
                           dept_list=dept_list, atk_list=atk_list,
                           bulan_list=BULAN_LIST, today=today,
                           current_year=current_year, data={})


@app.route('/atk/pengajuan/edit/<int:no>', methods=['GET', 'POST'])
def atk_pengajuan_edit(no):
    """Edit pengajuan ATK per item."""
    try:
        sheet = get_sheet(SHEET_PENGAJUAN_ATK)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_pengajuan_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data pengajuan No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_pengajuan_list'))

        if request.method == 'POST':
            try:
                jumlah = float(request.form.get('jumlah', 0) or 0)
                harga = float(request.form.get('harga_satuan', 0) or 0)
                total = jumlah * harga
            except ValueError:
                jumlah = 0
                harga = 0
                total = 0

            row = [
                no,
                request.form.get('tanggal_pengajuan', '').strip(),
                request.form.get('bulan', '').strip(),
                request.form.get('tahun', '').strip(),
                request.form.get('departement', '').strip(),
                request.form.get('kode_barang', '').strip(),
                request.form.get('nama_barang', '').strip(),
                jumlah,
                request.form.get('satuan', '').strip(),
                harga,
                total,
                request.form.get('keterangan', '').strip(),
            ]
            sheet.update(f'A{row_num}:L{row_num}', [row], value_input_option='USER_ENTERED')
            flash(f'Pengajuan ATK No. {no} berhasil diperbarui.', 'success')
            return redirect(url_for('atk_pengajuan_list'))

        records = get_all_data(sheet)
        data = next((r for r in records if str(r.get('No', '')) == str(no)), {})

        # Load dropdown data
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        sheet_atk = get_sheet(SHEET_MASTER_ATK)
        dept_list = get_all_data(sheet_dept) if sheet_dept else []
        atk_list = get_all_data(sheet_atk) if sheet_atk else []
        current_year = datetime.today().year

        return render_template('atk/pengajuan_edit.html', data=data, no=no,
                               dept_list=dept_list, atk_list=atk_list,
                               bulan_list=BULAN_LIST, current_year=current_year)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('atk_pengajuan_list'))


@app.route('/atk/pengajuan/delete/<int:no>', methods=['POST'])
def atk_pengajuan_delete(no):
    """Hapus pengajuan ATK."""
    try:
        sheet = get_sheet(SHEET_PENGAJUAN_ATK)
        if not sheet:
            flash('Tidak dapat terhubung ke Google Sheets.', 'error')
            return redirect(url_for('atk_pengajuan_list'))

        row_num = find_row_by_no(sheet, no)
        if not row_num:
            flash(f'Data No. {no} tidak ditemukan.', 'error')
            return redirect(url_for('atk_pengajuan_list'))

        sheet.delete_rows(row_num)
        flash(f'Pengajuan ATK No. {no} berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Gagal menghapus data: {str(e)}', 'error')

    return redirect(url_for('atk_pengajuan_list'))


# ============================================================
# ATK MODULE — Rekap Pengajuan ATK
# ============================================================

@app.route('/atk/rekap')
def atk_rekap():
    """Halaman rekap pengajuan ATK."""
    bulan_filter = request.args.get('bulan', '').strip()
    tahun_filter = request.args.get('tahun', str(datetime.today().year)).strip()
    dept_filter = request.args.get('departement', '').strip()

    try:
        sheet = get_sheet(SHEET_PENGAJUAN_ATK)
        records = get_all_data(sheet) if sheet else []

        # Load departments list for filter dropdown
        sheet_dept = get_sheet(SHEET_MASTER_DEPT)
        dept_list = get_all_data(sheet_dept) if sheet_dept else []

        # Filter
        if bulan_filter:
            records = [r for r in records if str(r.get('Bulan', '')) == bulan_filter]
        if tahun_filter:
            records = [r for r in records if str(r.get('Tahun', '')) == str(tahun_filter)]
        if dept_filter:
            records = [r for r in records if str(r.get('Departement', '')) == dept_filter]

        # Rekap per departement
        dept_rekap = {}
        for r in records:
            dept = r.get('Departement', 'Tidak Diketahui') or 'Tidak Diketahui'
            if dept not in dept_rekap:
                dept_rekap[dept] = {'jumlah_item': 0, 'total_harga': 0, 'items': []}
            dept_rekap[dept]['jumlah_item'] += 1
            dept_rekap[dept]['total_harga'] += safe_num(r.get('Total Harga', 0))
            dept_rekap[dept]['items'].append(r)

        # Rekap per barang
        barang_rekap = {}
        for r in records:
            kode = r.get('Kode Barang', '') or '-'
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
        total_items = len(records)
        total_dept = len(dept_rekap)

        # Get unique tahun for filter
        all_records = get_all_data(sheet) if sheet else []
        tahun_set = sorted(set(str(r.get('Tahun', '')) for r in all_records if r.get('Tahun', '')), reverse=True)

        return render_template('atk/rekap.html',
                               dept_rekap=dept_rekap, barang_rekap=barang_rekap,
                               grand_total=grand_total, total_items=total_items,
                               total_dept=total_dept,
                               bulan_filter=bulan_filter, tahun_filter=tahun_filter,
                               dept_filter=dept_filter, dept_list=dept_list,
                               bulan_list=BULAN_LIST, tahun_set=tahun_set)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('atk/rekap.html',
                               dept_rekap={}, barang_rekap={},
                               grand_total=0, total_items=0, total_dept=0,
                               bulan_filter='', tahun_filter=str(datetime.today().year),
                               dept_filter='', dept_list=[],
                               bulan_list=BULAN_LIST, tahun_set=[])


# ============================================================
# Run App
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
