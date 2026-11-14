"""Master Data Kendaraan CRUD and document updates."""

import app as flask_app

KENDARAAN = [1, 'B 1234 XY', 'Budi', 'Toyota', 'Avanza', 'MPV', 'Putih', 2020,
             'RANGKA-1', 'MESIN-1', '31/12/2026', '01/01/2026', '31/12/2030',
             '01/01/2026', 'POLIS-1', 'Asuransi ABC', 'All Risk', '01/01/2026',
             '2026', '2500000', 'GPS-1', 'BPKB-1', 'Kantor', 'Bensin', 'catatan']

DOCUMENT_FORM = {
    'stnk_1_tahun': '31/12/2027',
    'realisasi_pajak': '01/01/2027',
    'stnk_5_tahun': '31/12/2031',
    'tgl_realisasi_kir': '01/01/2027',
    'no_asuransi': 'POLIS-9',
    'nama_asuransi': 'Asuransi XYZ',
    'jenis_asuransi': 'TLO',
    'tgl_berlaku_asuransi': '01/01/2027',
    'periode_asuransi': '2027',
    'biaya_premi_asuransi': '3000000',
}


def _sheet(sheets):
    return sheets[flask_app.SHEET_KENDARAAN]


class TestKendaraanList:
    def test_renders_seeded_rows(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        body = auth_client.get('/kendaraan').get_data(as_text=True)
        assert 'B 1234 XY' in body
        assert 'Toyota' in body

    def test_search_matches_pemilik(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        body = auth_client.get('/kendaraan?searudi').get_data(as_text=True)
        assert 'Toyota' in body

    def test_search_matches_plat(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        body = auth_client.get('/kendaraan?sear234').get_data(as_text=True)
        assert 'Toyota' in body

    def test_empty_sheet_renders(self, auth_client):
        assert auth_client.get('/kendaraan').status_code == 200


class TestKendaraanCreate:
    def test_get_form_renders(self, auth_client):
        assert auth_client.get('/kendaraan/tambah').status_code == 200

    def test_post_appends_row(self, auth_client, sheets):
        auth_client.post('/kendaraan/tambah', data={
            'no_kendaraan': 'B 9999 ZZ',
            'pemilik': 'Siti',
            'merk': 'Honda',
            'model_kendaraan': 'Brio',
            'jenis_type': 'Hatchback',
            'warna': 'Merah',
            'tahun_kendaraan': '2021',
        })
        rows = _sheet(sheets).rows
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == 'B 9999 ZZ'

    def test_success_flash(self, auth_client):
        response = auth_client.post('/kendaraan/tambah', data={
            'no_kendaraan': 'B 8888 YY', 'pemilik': 'Andi',
        }, follow_redirects=True)
        assert 'berhasil ditambahkan' in response.get_data(as_text=True)


class TestKendaraanEdit:
    def test_get_prefills_form(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        body = auth_client.get('/kendaraan/edit/1').get_data(as_text=True)
        assert 'B 1234 XY' in body

    def test_post_updates_in_place(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        auth_client.post('/kendaraan/edit/1', data={
            'no_kendaraan': 'B 1234 XY', 'pemilik': 'Budi Santoso',
            'merk': 'Toyota', 'model_kendaraan': 'Avanza',
        })
        assert _sheet(sheets).rows[0][2] == 'Budi Santoso'

    def test_unknown_no_flashes_error(self, auth_client):
        response = auth_client.get('/kendaraan/edit/999', follow_redirects=True)
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestKendaraanDelete:
    def test_post_deletes_row(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        auth_client.post('/kendaraan/delete/1')
        assert _sheet(sheets).rows == []


class TestUpdateDokumen:
    def test_get_prefills_document_fields(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        body = auth_client.get('/kendaraan/update-dokumen/1').get_data(as_text=True)
        assert 'POLIS-1' in body

    def test_post_updates_only_document_columns(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        auth_client.post('/kendaraan/update-dokumen/1', data=DOCUMENT_FORM)
        row = _sheet(sheets).rows[0]
        # Document block is columns K..T (index 10..19).
        assert row[10] == '31/12/2027'   # STNK 1 Tahun
        assert row[14] == 'POLIS-9'      # No Asuransi
        assert row[19] == '3000000'      # Biaya Premi Asuransi
        # Identity columns are untouched.
        assert row[1] == 'B 1234 XY'
        assert row[4] == 'Avanza'

    def test_post_does_not_clobber_neighbouring_columns(self, auth_client, sheets, seed):
        """Regression: writing L..U shifted every value one column right,
        so STNK 1 Tahun was never saved and GPS/APCT was overwritten."""
        seed(_sheet(sheets), KENDARAAN)
        auth_client.post('/kendaraan/update-dokumen/1', data=DOCUMENT_FORM)
        row = _sheet(sheets).rows[0]
        assert row[9] == 'MESIN-1'      # No. Mesin, left of the block
        assert row[20] == 'GPS-1'       # GPS/APCT, right of the block
        assert row[21] == 'BPKB-1'      # No. BPKB, right of the block

    def test_success_flash(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        response = auth_client.post(
            '/kendaraan/update-dokumen/1', data=DOCUMENT_FORM, follow_redirects=True
        )
        assert 'berhasil diperbarui' in response.get_data(as_text=True)

    def test_unknown_no_flashes_error(self, auth_client):
        response = auth_client.get('/kendaraan/update-dokumen/999', follow_redirects=True)
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestKendaraanDashboard:
    def test_renders_with_data(self, auth_client, sheets, seed):
        seed(_sheet(sheets), KENDARAAN)
        assert auth_client.get('/kendaraan/dashboard').status_code == 200

    def test_renders_without_data(self, auth_client):
        assert auth_client.get('/kendaraan/dashboard').status_code == 200
