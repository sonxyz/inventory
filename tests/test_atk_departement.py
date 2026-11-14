"""Master Departement CRUD — ISSUE-ATK.md section 2."""

import app as flask_app


def _sheet(sheets):
    return sheets[flask_app.SHEET_MASTER_DEPT]


class TestDeptList:
    def test_renders_seeded_departements(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'], [2, 'Finance'])
        body = auth_client.get('/atk/departement').get_data(as_text=True)
        assert 'HRD' in body
        assert 'Finance' in body

    def test_search_filters_by_name(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'], [2, 'Finance'])
        body = auth_client.get('/atk/departement?search=Finance').get_data(as_text=True)
        assert 'Finance' in body
        assert 'HRD' not in body


class TestDeptCreate:
    def test_get_form_renders(self, auth_client):
        assert auth_client.get('/atk/departement/tambah').status_code == 200

    def test_post_appends_with_auto_no(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'])
        auth_client.post('/atk/departement/tambah', data={'departement': 'IT'})
        assert _sheet(sheets).rows == [[1, 'HRD'], [2, 'IT']]


class TestDeptEdit:
    def test_post_updates_in_place(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'])
        auth_client.post('/atk/departement/edit/1', data={'departement': 'Human Resource'})
        assert _sheet(sheets).rows[0] == [1, 'Human Resource']

    def test_get_form_prefills(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'])
        body = auth_client.get('/atk/departement/edit/1').get_data(as_text=True)
        assert 'HRD' in body

    def test_unknown_no_redirects_with_error(self, auth_client):
        response = auth_client.get('/atk/departement/edit/999', follow_redirects=True)
        assert 'tidak ditemukan' in response.get_data(as_text=True)


class TestDeptDelete:
    def test_post_deletes_row(self, auth_client, sheets, seed):
        seed(_sheet(sheets), [1, 'HRD'], [2, 'IT'])
        auth_client.post('/atk/departement/delete/1')
        assert _sheet(sheets).rows == [[2, 'IT']]
