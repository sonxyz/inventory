"""Authentication and per-module role gating."""

import pytest


class TestLogin:
    def test_default_admin_can_log_in(self, client):
        response = client.post(
            '/login',
            data={'username': 'admin', 'password': 'admin123'},
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_wrong_password_is_rejected(self, client):
        response = client.post(
            '/login',
            data={'username': 'admin', 'password': 'wrong'},
            follow_redirects=True,
        )
        assert 'Username atau password salah' in response.get_data(as_text=True)

    def test_login_sets_session(self, client):
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        with client.session_transaction() as session:
            assert session['user'] == 'admin'
            assert session['role'] == 'admin'


class TestRouteAccess:
    def test_anonymous_user_redirected_to_login(self, client):
        response = client.get('/atk/master')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_public_pengajuan_form_needs_no_login(self, client):
        response = client.get('/atk/pengajuan/tambah')
        assert response.status_code == 200

    @pytest.mark.parametrize('role', ['atk', 'admin'])
    def test_atk_roles_can_open_atk_module(self, client, role):
        with client.session_transaction() as session:
            session['user'] = 'u'
            session['role'] = role
        assert client.get('/atk/master').status_code == 200

    def test_kendaraan_role_blocked_from_atk(self, client):
        with client.session_transaction() as session:
            session['user'] = 'u'
            session['role'] = 'kendaraan'
        response = client.get('/atk/master', follow_redirects=False)
        assert response.status_code == 302
        assert response.headers['Location'] != '/atk/master'

    def test_atk_role_blocked_from_kendaraan(self, client):
        with client.session_transaction() as session:
            session['user'] = 'u'
            session['role'] = 'atk'
        response = client.get('/kendaraan', follow_redirects=False)
        assert response.status_code == 302
        assert response.headers['Location'] != '/kendaraan'

    def test_non_admin_blocked_from_user_management(self, client):
        with client.session_transaction() as session:
            session['user'] = 'u'
            session['role'] = 'atk'
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
        assert response.headers['Location'] != '/admin/users'


class TestLogout:
    def test_logout_clears_session(self, client):
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        client.get('/logout')
        with client.session_transaction() as session:
            assert 'user' not in session
