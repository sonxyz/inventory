"""Master Data ATK CRUD — ISSUE-ATK.md section 1."""

import app as flask_app


def _sheet(sheets):
    return sheets[flask_app.SHEET_MASTER_ATK]


class TestMasterList:
    def test_renders_seeded_barang(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'])
        body = auth_client.get('/atk/master').get_data(as_text=True)
        assert 'ATK-001' in body
        assert 'Kertas HVS A4' in body

    def test_search_filters_by_kode(self, auth_client, sheets, seed):
        seed(
            _sheet(sheets),
            [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'],
            [2, 'ATK-002', 'Pulpen Hitam', 3000, 'pcs'],
        )
        body = auth_client.get('/atk/master?search=ATK-002').get_data(as_text=True)
        assert 'Pulpen Hitam' in body
        assert 'Kertas HVS A4' not in body

    def test_search_matches_satuan(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'])
        body = auth_client.get('/atk/master?search=rim').get_data(as_text=True)
        assert 'Kertas HVS A4' in body

    def test_empty_sheet_renders_without_error(self, auth_client):
        assert auth_client.get('/atk/master').status_code == 200


class TestMasterCreate:
    def test_get_form_renders(self, auth_client):
        assert auth_client.get('/atk/master/tambah').status_code == 200

    def test_post_appends_row_with_auto_no(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas', 50000, 'rim'])
        auth_client.post('/atk/master/tambah', data={
            'kode': 'ATK-002',
            'nama_barang': 'Pulpen',
            'perkiraan_harga': '3000',
            'satuan': 'pcs',
        })
        rows = _sheet(sheets).rows
        assert len(rows) == 2
        assert rows[1] == [2, 'ATK-002', 'Pulpen', '3000', 'pcs']

    def test_first_row_gets_no_1(self, auth_client, sheets):
        auth_client.post('/atk/master/tambah', data={
            'kode': 'ATK-001', 'nama_barang': 'Kertas',
            'perkiraan_harga': '50000', 'satuan': 'rim',
        })
        assert _sheet(sheets).rows[0][0] == 1

    def test_post_redirects_to_list(self, auth_client):
        response = auth_client.post('/atk/master/tambah', data={
            'kode': 'ATK-009', 'nama_barang': 'Map', 'perkiraan_harga': '2000', 'satuan': 'pcs',
        })
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/atk/master')

    def test_success_flash_message(self, auth_client):
        response = auth_client.post('/atk/master/tambah', data={
            'kode': 'ATK-009', 'nama_barang': 'Map', 'perkiraan_harga': '2000', 'satuan': 'pcs',
        }, follow_redirects=True)
        assert 'berhasil ditambahkan' in response.get_data(as_text=True)


class TestMasterEdit:
    def test_get_form_prefills_existing_row(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'])
        body = auth_client.get('/atk/master/edit/1').get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'ATK-001' in body

    def test_post_updates_row_in_place(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas HVS A4', 50000, 'rim'])
        auth_client.post('/atk/master/edit/1', data={
            'kode': 'ATK-001', 'nama_barang': 'Kertas HVS F4',
            'perkiraan_harga': '55000', 'satuan': 'rim',
        })
        assert _sheet(sheets).rows[0] == [1, 'ATK-001', 'Kertas HVS F4', '55000', 'rim']

    def test_edit_does_not_add_a_row(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas', 50000, 'rim'])
        auth_client.post('/atk/master/edit/1', data={
            'kode': 'ATK-001', 'nama_barang': 'Kertas Baru',
            'perkiraan_harga': '1', 'satuan': 'rim',
        })
        assert len(_sheet(sheets).rows) == 1

    def test_unknown_no_redirects_with_error(self, auth_client):
        response = auth_client.get('/atk/master/edit/999', follow_redirects=True)
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestMasterDelete:
    def test_post_deletes_row(self, auth_client, sheets, seed):
        seed(
            _sheet(sheets),
            [1, 'ATK-001', 'Kertas', 50000, 'rim'],
            [2, 'ATK-002', 'Pulpen', 3000, 'pcs'],
        )
        auth_client.post('/atk/master/delete/1')
        rows = _sheet(sheets).rows
        assert len(rows) == 1
        assert rows[0][0] == 2

    def test_delete_unknown_no_keeps_data(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'ATK-001', 'Kertas', 50000, 'rim'])
        response = auth_client.post('/atk/master/delete/999', follow_redirects=True)
        assert len(_sheet(sheets).rows) == 1
        assert 'tidak ditemukan' in response.get_data(as_text=True)

    def test_get_is_not_allowed(self, auth_client):
        assert auth_client.get('/atk/master/delete/1').status_code == 405
