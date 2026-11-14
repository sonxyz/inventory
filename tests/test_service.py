"""History Service Mobil & Motor — one shared implementation, two sheets."""

import pytest

import app as flask_app

SERVICE = [1, 'B 1234 XY', 'Budi', '01/01/2026', 'Bengkel Jaya', 'Ganti Oli',
           4, 'liter', 500000, 450000, 450000, 10000, 10500, 500, 15000, 'rutin']


@pytest.fixture(params=['mobil', 'motor'])
def jenis(request):
    return request.param


def _sheet(sheets, jenis):
    name = (flask_app.SHEET_SERVICE_MOBIL if jenis == 'mobil'
            else flask_app.SHEET_SERVICE_MOTOR)
    return sheets[name]


class TestServiceList:
    def test_renders_seeded_rows(self, auth_client, sheets, seed, jenis):
        seed(_sheet(sheets, jenis), SERVICE)
        body = auth_client.get('/service/%s' % jenis).get_data(as_text=True)
        assert 'B 1234 XY' in body
        assert 'Bengkel Jaya' in body

    def test_search_filters(self, auth_client, sheets, seed, jenis):
        seed(_sheet(sheets, jenis), SERVICE)
        body = auth_client.get('/service/%s?searenkel' % jenis).get_data(as_text=True)
        assert 'Bengkel Jaya' in body

    def test_empty_sheet_renders(self, auth_client, jenis):
        assert auth_client.get('/service/%s' % jenis).status_code == 200

    def test_mobil_and_motor_use_separate_sheets(self, auth_client, sheets, seed):
        seed(_sheet(sheets, 'mobil'), SERVICE)
        mobil = auth_client.get('/service/mobil').get_data(as_text=True)
        motor = auth_client.get('/service/motor').get_data(as_text=True)
        assert 'Bengkel Jaya' in mobil
        assert 'Bengkel Jaya' not in motor


class TestServiceCreate:
    def test_get_form_renders(self, auth_client, jenis):
        assert auth_client.get('/service/%s/tambah' % jenis).status_code == 200

    def test_post_appends_row(self, auth_client, sheets, jenis):
        auth_client.post('/service/%s/tambah' % jenis, data={
            'no_kendaraan': 'B 1234 XY',
            'nama_pemilik': 'Budi',
            'tanggal_service': '01/01/2026',
            'nama_bengkel': 'Bengkel Jaya',
            'jenis_service': 'Ganti Oli',
            'jumlah_part': '4',
            'satuan': 'liter',
            'pengajuan': '500000',
            'realisasi': '450000',
            'km_awal': '10000',
            'km_akhir': '10500',
            'km_selanjutnya': '15000',
            'keterangan': 'rutin',
        })
        rows = _sheet(sheets, jenis).rows
        assert len(rows) == 1
        assert rows[0][0] == 1

    def test_selisih_km_is_km_akhir_minus_km_awal(self, auth_client, sheets, jenis):
        auth_client.post('/service/%s/tambah' % jenis, data={
            'no_kendaraan': 'B 1', 'nama_pemilik': 'A',
            'km_awal': '10000', 'km_akhir': '10500',
            'pengajuan': '500000', 'realisasi': '450000',
        })
        row = _sheet(sheets, jenis).rows[0]
        assert row[13] == 500      # Selisih KM

    def test_total_equals_realisasi(self, auth_client, sheets, jenis):
        auth_client.post('/service/%s/tambah' % jenis, data={
            'no_kendaraan': 'B 1', 'nama_pemilik': 'A',
            'km_awal': '1', 'km_akhir': '2',
            'pengajuan': '500000', 'realisasi': '450000',
        })
        row = _sheet(sheets, jenis).rows[0]
        assert row[10] == 450000.0   # Total

    def test_success_flash(self, auth_client, jenis):
        response = auth_client.post('/service/%s/tambah' % jenis, data={
            'no_kendaraan': 'B 1', 'nama_pemilik': 'A',
            'km_awal': '1', 'km_akhir': '2',
        }, follow_redirects=True)
        assert 'berhasil ditambahkan' in response.get_data(as_text=True)


class TestServiceEdit:
    def test_get_prefills_form(self, auth_client, sheets, seed, jenis):
        seed(_sheet(sheets, jenis), SERVICE)
        body = auth_client.get('/service/%s/edit/1' % jenis).get_data(as_text=True)
        assert 'Bengkel Jaya' in body

    def test_post_updates_in_place(self, auth_client, sheets, seed, jenis):
        seed(_sheet(sheets, jenis), SERVICE)
        auth_client.post('/service/%s/edit/1' % jenis, data={
            'no_kendaraan': 'B 1234 XY', 'nama_pemilik': 'Budi',
            'tanggal_service': '01/01/2026', 'nama_bengkel': 'Bengkel Baru',
            'jenis_service': 'Tune Up', 'km_awal': '10000', 'km_akhir': '11000',
            'pengajuan': '600000', 'realisasi': '550000',
        })
        rows = _sheet(sheets, jenis).rows
        assert len(rows) == 1
        assert rows[0][4] == 'Bengkel Baru'
        assert rows[0][13] == 1000

    def test_unknown_no_flashes_error(self, auth_client, jenis):
        response = auth_client.get(
            '/service/%s/edit/999' % jenis, follow_redirects=True
        )
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestServiceDelete:
    def test_post_deletes_row(self, auth_client, sheets, seed, jenis):
        seed(_sheet(sheets, jenis), SERVICE)
        auth_client.post('/service/%s/delete/1' % jenis)
        assert _sheet(sheets, jenis).rows == []
