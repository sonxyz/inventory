"""Error paths in the Google-Sheets helper layer.

These helpers are the app's only barrier between a flaky remote API and the
request handlers, so each must swallow failures and return a safe default
rather than propagate an exception into a template.
"""

import pytest

import app as flask_app


class BrokenSheet:
    """A worksheet whose every call raises, like a revoked token would."""

    def get_all_records(self):
        raise RuntimeError('network down')

    def find(self, *args, **kwargs):
        raise RuntimeError('network down')

    def append_row(self, *args, **kwargs):
        raise RuntimeError('network down')

    def update(self, *args, **kwargs):
        raise RuntimeError('network down')

    def delete_rows(self, *args, **kwargs):
        raise RuntimeError('network down')


class TestGetAllData:
    def test_returns_empty_list_when_sheet_raises(self):
        assert flask_app.get_all_data(BrokenSheet()) == []

    def test_returns_records_on_success(self, sheets):
        sheet = sheets[flask_app.SHEET_MASTER_DEPT]
        sheet.append_row([1, 'HRD'])
        assert flask_app.get_all_data(sheet) == [{'No': 1, 'Departement': 'HRD'}]


class TestFindRowByNo:
    def test_returns_none_when_sheet_raises(self):
        assert flask_app.find_row_by_no(BrokenSheet(), 1) is None

    def test_returns_none_when_no_is_absent(self, sheets):
        sheet = sheets[flask_app.SHEET_MASTER_DEPT]
        sheet.append_row([1, 'HRD'])
        assert flask_app.find_row_by_no(sheet, 99) is None

    def test_returns_sheet_row_when_found(self, sheets):
        sheet = sheets[flask_app.SHEET_MASTER_DEPT]
        sheet.append_row([1, 'HRD'])
        sheet.append_row([2, 'IT'])
        # Data row 2 lives on sheet row 3 (row 1 is the header).
        assert flask_app.find_row_by_no(sheet, 2) == 3


class TestGetNextNo:
    def test_first_row_is_one(self, sheets):
        assert flask_app.get_next_no(sheets[flask_app.SHEET_MASTER_DEPT]) == 1

    def test_increments_past_existing_max(self, sheets):
        sheet = sheets[flask_app.SHEET_MASTER_DEPT]
        sheet.append_row([1, 'HRD'])
        sheet.append_row([7, 'IT'])
        assert flask_app.get_next_no(sheet) == 8

    def test_ignores_non_numeric_no_values(self, sheets):
        sheet = sheets[flask_app.SHEET_MASTER_DEPT]
        sheet.append_row([1, 'HRD'])
        sheet.append_row(['x', 'Broken'])
        assert flask_app.get_next_no(sheet) == 2

    def test_returns_one_when_sheet_raises(self):
        assert flask_app.get_next_no(BrokenSheet()) == 1


class TestSafeNumEdgeCases:
    @pytest.mark.parametrize('raw', ['Rp', 'rp', ' ', '-', 'Rp.'])
    def test_degenerate_strings_become_zero(self, raw):
        assert flask_app.safe_num(raw) == 0.0

    def test_negative_numbers_are_preserved(self):
        assert flask_app.safe_num('-150.000') == -150000.0


class TestFormatCurrencyEdgeCases:
    def test_none_renders_zero(self):
        assert flask_app.format_currency(None) == 'Rp 0'

    def test_unparseable_text_renders_zero(self):
        assert flask_app.format_currency('bukan angka') == 'Rp 0'

    def test_negative_renders_with_sign(self):
        assert flask_app.format_currency(-150000) == 'Rp -150.000'


class TestRouteErrorHandling:
    """A broken sheet must surface as a flash message, not a 500."""

    def test_kendaraan_list_survives_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        assert auth_client.get('/kendaraan').status_code == 200

    def test_atk_master_list_survives_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        assert auth_client.get('/atk/master').status_code == 200

    def test_atk_pengajuan_list_survives_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        assert auth_client.get('/atk/pengajuan').status_code == 200

    def test_atk_rekap_survives_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        assert auth_client.get('/atk/rekap').status_code == 200

    def test_delete_with_broken_sheet_redirects(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/master/delete/1')
        assert response.status_code == 302


class TestLoginEdgeCases:
    def test_redirects_when_already_logged_in(self, auth_client):
        response = auth_client.get('/login')
        assert response.status_code == 302
        assert response.headers['Location'] != '/login'

    def test_next_url_is_honoured_after_login(self, client):
        response = client.post(
            '/login?next=/atk/master',
            data={'username': 'admin', 'password': 'admin123'},
        )
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/atk/master')

    def test_default_password_triggers_security_warning(self, client):
        response = client.post(
            '/login',
            data={'username': 'admin', 'password': 'admin123'},
            follow_redirects=True,
        )
        assert 'PERINGATAN KEAMANAN' in response.get_data(as_text=True)


class TestMutationErrorPaths:
    """Create/edit/delete must redirect with a flash when the sheet fails."""

    def test_master_tambah_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/master/tambah', data={'kode': 'X'})
        assert response.status_code == 302

    def test_master_edit_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/master/edit/1', data={'kode': 'X'})
        assert response.status_code == 302

    def test_dept_tambah_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/departement/tambah', data={'departement': 'X'})
        assert response.status_code == 302

    def test_dept_delete_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/departement/delete/1')
        assert response.status_code == 302

    def test_pengajuan_edit_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/pengajuan/edit/1', data={'jumlah': '1'})
        assert response.status_code == 302

    def test_pengajuan_delete_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/atk/pengajuan/delete/1')
        assert response.status_code == 302

    def test_kendaraan_tambah_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/kendaraan/tambah', data={'no_kendaraan': 'B 1'})
        assert response.status_code == 302

    def test_kendaraan_edit_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/kendaraan/edit/1', data={'no_kendaraan': 'B 1'})
        assert response.status_code == 302

    def test_kendaraan_delete_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/kendaraan/delete/1')
        assert response.status_code == 302

    def test_service_tambah_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/service/mobil/tambah', data={'no_kendaraan': 'B 1'})
        assert response.status_code == 302

    def test_service_edit_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/service/mobil/edit/1', data={'no_kendaraan': 'B 1'})
        assert response.status_code == 302

    def test_service_delete_with_broken_sheet(self, auth_client, monkeypatch):
        monkeypatch.setattr(flask_app, 'get_sheet', lambda name: BrokenSheet())
        response = auth_client.post('/service/motor/delete/1')
        assert response.status_code == 302
