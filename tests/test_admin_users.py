"""Admin user management and the landing portal."""

import app as flask_app


def _users(sheets):
    return sheets[flask_app.SHEET_MASTER_USERS]


class TestPortal:
    def test_requires_login(self, client):
        response = client.get('/')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_renders_for_logged_in_user(self, auth_client):
        assert auth_client.get('/').status_code == 200


class TestAdminUsers:
    def test_lists_users(self, auth_client, sheets, seed):
        seed(_users(sheets), [1, 'admin', 'hash', 'admin'], [2, 'budi', 'hash', 'atk'])
        body = auth_client.get('/admin/users').get_data(as_text=True)
        assert 'budi' in body
        assert 'admin' in body

    def test_create_appends_hashed_password(self, auth_client, sheets, seed):
        seed(_users(sheets), [1, 'admin', 'hash', 'admin'])
        auth_client.post('/admin/users', data={
            'username': 'siti', 'password': 'rahasia123', 'role': 'atk',
        })
        rows = _users(sheets).rows
        assert len(rows) == 2
        assert rows[1][1] == 'siti'
        assert rows[1][2] != 'rahasia123'      # stored hashed, never plaintext
        assert rows[1][3] == 'atk'

    def test_duplicate_username_is_rejected(self, auth_client, sheets, seed):
        seed(_users(sheets), [1, 'siti', 'hash', 'atk'])
        response = auth_client.post('/admin/users', data={
            'username': 'siti', 'password': 'x', 'role': 'atk',
        }, follow_redirects=True)
        assert 'sudah terdaftar' in response.get_data(as_text=True)
        assert len(_users(sheets).rows) == 1

    def test_missing_fields_are_rejected(self, auth_client, sheets):
        response = auth_client.post('/admin/users', data={
            'username': 'x', 'password': '', 'role': '',
        }, follow_redirects=True)
        assert 'wajib diisi' in response.get_data(as_text=True)
        assert _users(sheets).rows == []

    def test_cannot_delete_own_account(self, auth_client, sheets, seed):
        seed(_users(sheets), [1, 'tester', 'hash', 'admin'])
        response = auth_client.post(
            '/admin/users/delete/1', follow_redirects=True
        )
        assert 'tidak dapat menghapus akun Anda sendiri' in response.get_data(as_text=True)
        assert len(_users(sheets).rows) == 1

    def test_can_delete_other_account(self, auth_client, sheets, seed):
        seed(_users(sheets), [1, 'tester', 'hash', 'admin'], [2, 'other', 'hash', 'atk'])
        auth_client.post('/admin/users/delete/2')
        assert [r[1] for r in _users(sheets).rows] == ['tester']


class TestLoginAgainstStoredUsers:
    def test_created_user_can_log_in(self, auth_client, client, sheets, seed):
        auth_client.post('/admin/users', data={
            'username': 'siti', 'password': 'rahasia123', 'role': 'atk',
        })
        client.get('/logout')
        response = client.post(
            '/login',
            data={'username': 'siti', 'password': 'rahasia123'},
            follow_redirects=False,
        )
        assert response.status_code == 302
        with client.session_transaction() as session:
            assert session['role'] == 'atk'

    def test_unknown_user_is_rejected(self, client):
        response = client.post(
            '/login', data={'username': 'ghost', 'password': 'x'},
            follow_redirects=True,
        )
        assert 'Username atau password salah' in response.get_data(as_text=True)
