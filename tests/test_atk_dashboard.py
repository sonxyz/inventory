"""ATK dashboard and graceful degradation when Google Sheets is unreachable."""

import app as flask_app


def _pengajuan(sheets):
    return sheets[flask_app.SHEET_PENGAJUAN_ATK]


def _atk(sheets):
    return sheets[flask_app.SHEET_MASTER_ATK]


def _dept(sheets):
    return sheets[flask_app.SHEET_MASTER_DEPT]


class TestAtkDashboard:
    def test_renders_with_data(self, auth_client, sheets, seed):
        seed(_atk(sheets), [1, 'ATK-001', 'Kertas', 50000, 'rim'])
        seed(_dept(sheets), [1, 'HRD'])
        seed(_pengajuan(sheets), [1, '01/01/2026', 'Januari', 2026, 'HRD',
                                  'ATK-001', 'Kertas', 2, 'rim', 50000, 100000, ''])
        body = auth_client.get('/atk/dashboard').get_data(as_text=True)
        assert 'Rp 100.000' in body

    def test_renders_with_no_data(self, auth_client):
        assert auth_client.get('/atk/dashboard').status_code == 200

    def test_recent_pengajuan_lists_latest_first(self, auth_client, sheets, seed):
        seed(
            _pengajuan(sheets),
            [1, '01/01/2026', 'Januari', 2026, 'HRD', 'ATK-001', 'Kertas',
             1, 'rim', 50000, 50000, ''],
            [2, '02/01/2026', 'Januari', 2026, 'HRD', 'ATK-002', 'Pulpen',
             1, 'pcs', 3000, 3000, ''],
        )
        body = auth_client.get('/atk/dashboard').get_data(as_text=True)
        assert body.index('Pulpen') < body.index('Kertas')


class TestSheetsUnavailable:
    """Every page must degrade gracefully instead of raising."""

    def test_master_list_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/atk/master')
        assert response.status_code == 200

    def test_departement_list_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/atk/departement')
        assert response.status_code == 200

    def test_pengajuan_list_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/atk/pengajuan')
        assert response.status_code == 200

    def test_rekap_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/atk/rekap')
        assert response.status_code == 200

    def test_dashboard_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/atk/dashboard')
        assert response.status_code == 200

    def test_kendaraan_list_without_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.get('/kendaraan')
        assert response.status_code == 200

    def test_pengajuan_create_without_sheet_flashes_error(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: None)
        response = auth_client.post('/atk/pengajuan/tambah', data={
            'tanggal_pengajuan': '01/01/2026',
            'bulan': 'Januari',
            'tahun': '2026',
            'departement': 'HRD',
            'kode_barang[]': ['ATK-001'],
            'nama_barang[]': ['Kertas'],
            'jumlah[]': ['1'],
            'satuan[]': ['rim'],
            'harga_satuan[]': ['50000'],
            'keterangan_item[]': [''],
        }, follow_redirects=True)
        assert 'Tidak dapat terhubung' in response.get_data(as_text=True)


class TestAtkDashboardStats:
    def test_counts_barang_and_departements(self, auth_client, sheets, seed):
        seed(
            _atk(sheets),
            [1, 'ATK-001', 'Kertas', 50000, 'rim'],
            [2, 'ATK-002', 'Pulpen', 3000, 'pcs'],
        )
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        body = auth_client.get('/atk/dashboard').get_data(as_text=True)
        assert 'Total Barang' in body
        assert 'Departemen' in body
