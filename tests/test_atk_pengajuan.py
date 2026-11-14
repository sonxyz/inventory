"""Pengajuan ATK: multi-item create, list filters, edit, delete."""

import app as flask_app


def _pengajuan(sheets):
    return sheets[flask_app.SHEET_PENGAJUAN_ATK]


def _dept(sheets):
    return sheets[flask_app.SHEET_MASTER_DEPT]


def _atk(sheets):
    return sheets[flask_app.SHEET_MASTER_ATK]


ROW_HRD = [1, '01/01/2026', 'Januari', 2026, 'HRD', 'ATK-001', 'Kertas HVS A4',
           2, 'rim', 50000, 100000, '']
ROW_IT = [2, '02/01/2026', 'Januari', 2026, 'IT', 'ATK-002', 'Pulpen Hitam',
          10, 'pcs', 3000, 30000, 'urgent']


def _item_form(**overrides):
    data = {
        'tanggal_pengajuan': '01/01/2026',
        'bulan': 'Januari',
        'tahun': '2026',
        'departement': 'HRD',
        'kode_barang[]': ['ATK-001'],
        'nama_barang[]': ['Kertas HVS A4'],
        'jumlah[]': ['2'],
        'satuan[]': ['rim'],
        'harga_satuan[]': ['50000'],
        'keterangan_item[]': [''],
    }
    data.update(overrides)
    return data


class TestPengajuanList:
    def test_renders_rows(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get('/atk/pengajuan').get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'Pulpen Hitam' in body

    def test_departement_filter(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get('/atk/pengajuan?departement=HRD').get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'Pulpen Hitam' not in body

    def test_bulan_filter(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get('/atk/pengajuan?bulan=Januari').get_data(as_text=True)
        assert 'Kertas HVS A4' in body

    def test_tahun_filter_excludes_other_years(self, auth_client, sheets, seed):
        old = [3, '01/01/2025', 'Januari', 2025, 'HRD', 'ATK-009', 'Spidol',
               1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), ROW_HRD, old)
        body = auth_client.get('/atk/pengajuan?tahun=2025').get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas HVS A4' not in body

    def test_search_matches_kode_and_nama(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get('/atk/pengajuan?search=pulpen').get_data(as_text=True)
        assert 'Pulpen Hitam' in body
        assert 'Kertas HVS A4' not in body

    def test_footer_total_reflects_filtered_rows(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get('/atk/pengajuan?departement=HRD').get_data(as_text=True)
        assert 'Rp 100.000' in body
        assert 'Rp 130.000' not in body

    def test_filters_combine_as_and(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        body = auth_client.get(
            '/atk/pengajuan?departement=HRD&bulan=Januari&tahun=2026'
        ).get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'Pulpen Hitam' not in body

    def test_empty_result_renders(self, auth_client):
        response = auth_client.get('/atk/pengajuan?departement=Nobody')
        assert response.status_code == 200


class TestPengajuanCreate:
    def test_form_is_publicly_reachable(self, client):
        assert client.get('/atk/pengajuan/tambah').status_code == 200

    def test_form_lists_departements_and_barang(self, client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'])
        seed(_atk(sheets), [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'])
        body = client.get('/atk/pengajuan/tambah').get_data(as_text=True)
        assert 'HRD' in body
        assert 'Kertas HVS A4' in body

    def test_multi_item_creates_one_row_per_item(self, auth_client, sheets):
        auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'kode_barang[]': ['ATK-001', 'ATK-002'],
            'nama_barang[]': ['Kertas', 'Pulpen'],
            'jumlah[]': ['2', '10'],
            'satuan[]': ['rim', 'pcs'],
            'harga_satuan[]': ['50000', '3000'],
            'keterangan_item[]': ['', 'urgent'],
        }))
        rows = _pengajuan(sheets).rows
        assert len(rows) == 2
        assert [r[5] for r in rows] == ['ATK-001', 'ATK-002']

    def test_total_harga_is_jumlah_times_harga(self, auth_client, sheets):
        auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'jumlah[]': ['3'], 'harga_satuan[]': ['50000'],
        }))
        row = _pengajuan(sheets).rows[0]
        assert row[7] == 3.0
        assert row[9] == 50000.0
        assert row[10] == 150000.0

    def test_auto_increment_continues_per_item(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD)
        auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'kode_barang[]': ['ATK-002', 'ATK-003'],
            'nama_barang[]': ['Pulpen', 'Map'],
            'jumlah[]': ['1', '1'],
            'satuan[]': ['pcs', 'pcs'],
            'harga_satuan[]': ['3000', '2000'],
            'keterangan_item[]': ['', ''],
        }))
        assert [r[0] for r in _pengajuan(sheets).rows] == [1, 2, 3]

    def test_incomplete_rows_are_skipped(self, auth_client, sheets):
        auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'kode_barang[]': ['ATK-001', '', 'ATK-003'],
            'nama_barang[]': ['Kertas', 'Tanpa Kode', 'Map'],
            'jumlah[]': ['1', '5', '1'],
            'satuan[]': ['rim', 'pcs', 'pcs'],
            'harga_satuan[]': ['50000', '999', '2000'],
            'keterangan_item[]': ['', '', ''],
        }))
        assert len(_pengajuan(sheets).rows) == 2

    def test_all_rows_invalid_flashes_error(self, auth_client, sheets):
        response = auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'kode_barang[]': [''], 'nama_barang[]': [''],
            'jumlah[]': ['0'], 'satuan[]': [''], 'harga_satuan[]': ['0'],
        }), follow_redirects=True)
        assert 'Tidak ada item yang valid' in response.get_data(as_text=True)

    def test_success_flash_reports_item_count(self, auth_client, sheets):
        response = auth_client.post('/atk/pengajuan/tambah', data=_item_form(**{
            'kode_barang[]': ['ATK-001', 'ATK-002'],
            'nama_barang[]': ['Kertas', 'Pulpen'],
            'jumlah[]': ['1', '2'],
            'satuan[]': ['rim', 'pcs'],
            'harga_satuan[]': ['50000', '3000'],
            'keterangan_item[]': ['', ''],
        }), follow_redirects=True)
        assert '2 item pengajuan ATK berhasil disimpan' in response.get_data(as_text=True)


class TestPengajuanEdit:
    def test_get_prefills_form(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD)
        body = auth_client.get('/atk/pengajuan/edit/1').get_data(as_text=True)
        assert 'Kertas HVS A4' in body

    def test_post_recomputes_total(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD)
        auth_client.post('/atk/pengajuan/edit/1', data={
            'tanggal_pengajuan': '01/01/2026',
            'bulan': 'Januari',
            'tahun': '2026',
            'departement': 'HRD',
            'kode_barang': 'ATK-001',
            'nama_barang': 'Kertas HVS A4',
            'jumlah': '5',
            'satuan': 'rim',
            'harga_satuan': '50000',
            'keterangan': 'revisi',
        })
        row = _pengajuan(sheets).rows[0]
        assert row[7] == 5.0
        assert row[10] == 250000.0
        assert row[11] == 'revisi'

    def test_unknown_no_flashes_error(self, auth_client):
        response = auth_client.get('/atk/pengajuan/edit/999', follow_redirects=True)
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestPengajuanDelete:
    def test_post_removes_row(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), ROW_HRD, ROW_IT)
        auth_client.post('/atk/pengajuan/delete/1')
        rows = _pengajuan(sheets).rows
        assert len(rows) == 1
        assert rows[0][0] == 2
