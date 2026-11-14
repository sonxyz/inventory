"""Tracking page must load within the serverless time budget.

``kendaraan_tracking`` needs three worksheets (Kendaraan, Service Mobil,
Service Motor). Every ``get_sheet()`` call re-opens the spreadsheet through
Google's API, and ``get_spreadsheet()`` alone measured ~1.55s against the
live spreadsheet. With three sheets that is ~4.6s of pure connection setup
on top of ~2s of row fetching, putting the page at ~7.7s - dangerously close
to the 10s serverless timeout, and past it once a cold start is included.

The page therefore timed out in deployment and rendered nothing, even though
every row was present. These tests pin a bounded connection budget so the
page cannot regress into re-opening the spreadsheet once per sheet.
"""

import pytest

import app as flask_app


def _kendaraan(no, plate):
    return [no, plate, 'Budi', 'Toyota', 'Avanza', 'MPV', 'Putih', '2020',
            'RANGKA', 'MESIN', '31/12/2026', '', '', '01/01/2026', '', '',
            '', '01/01/2026', '2026', '2500000', 'GPS', 'BPKB', 'Kantor',
            'Bensin', '']


def _service(no, plate):
    return [no, plate, 'Budi', '01-01-2026', 'Bengkel Jaya', 'Ganti Oli',
            1, 'liter', 100000, 90000, 90000, 1000, 1100, 100, 5000, '']


@pytest.fixture
def counting_client(client, sheets, monkeypatch):
    """Count how often each worksheet is resolved for one request."""
    calls = {'get_sheet': 0, 'names': []}

    def counted_get_sheet(name):
        calls['get_sheet'] += 1
        calls['names'].append(name)
        return sheets.get(name)

    monkeypatch.setattr(flask_app, 'get_sheet', counted_get_sheet)
    with client.session_transaction() as session:
        session['user'] = 'tester'
        session['role'] = 'admin'
    return client, calls


class TestTrackingConnectionBudget:
    def test_resolves_each_worksheet_at_most_once(self, counting_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], _service(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOTOR], _service(1, 'D 1 AB'))
        client, calls = counting_client
        client.get('/kendaraan/tracking/D 1 AB')
        # One request must not resolve the same worksheet twice.
        assert len(calls['names']) == len(set(calls['names'])), calls['names']

    def test_resolves_at_most_three_worksheets(self, counting_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], _service(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOTOR], _service(1, 'D 1 AB'))
        client, calls = counting_client
        client.get('/kendaraan/tracking/D 1 AB')
        assert calls['get_sheet'] <= 3, calls['names']


class TestTrackingRendersData:
    def test_shows_vehicle_identity(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        body = auth_client.get('/kendaraan/tracking/D 1 AB').get_data(as_text=True)
        assert 'D 1 AB' in body

    def test_shows_mobil_service_rows(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], _service(1, 'D 1 AB'))
        body = auth_client.get('/kendaraan/tracking/D 1 AB').get_data(as_text=True)
        assert 'Ganti Oli' in body

    def test_shows_motor_service_rows(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOTOR], _service(1, 'D 1 AB'))
        body = auth_client.get('/kendaraan/tracking/D 1 AB').get_data(as_text=True)
        assert 'Ganti Oli' in body

    def test_merges_both_service_kinds(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], _service(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOTOR],
             [1, 'D 1 AB', 'Budi', '02-02-2026', 'Bengkel Motor', 'Servis Ringan',
              1, 'paket', 50000, 40000, 40000, 2000, 2100, 100, 4000, ''])
        body = auth_client.get('/kendaraan/tracking/D 1 AB').get_data(as_text=True)
        assert 'Ganti Oli' in body
        assert 'Servis Ringan' in body

    def test_excludes_other_plates(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN],
             _kendaraan(1, 'D 1 AB'), _kendaraan(2, 'D 2 CD'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL],
             _service(1, 'D 1 AB'),
             [2, 'D 2 CD', 'Ani', '01-01-2026', 'Bengkel Lain', 'Tune Up',
              1, 'paket', 1, 1, 1, 1, 2, 1, 3, ''])
        body = auth_client.get('/kendaraan/tracking/D 1 AB').get_data(as_text=True)
        assert 'Ganti Oli' in body
        assert 'Tune Up' not in body

    def test_plate_match_ignores_case_and_padding(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], _service(1, 'D 1 AB'))
        body = auth_client.get('/kendaraan/tracking/d 1 ab').get_data(as_text=True)
        assert 'Ganti Oli' in body

    def test_unknown_plate_still_renders(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], _kendaraan(1, 'D 1 AB'))
        response = auth_client.get('/kendaraan/tracking/D 9 ZZ')
        assert response.status_code == 200


class TestSpreadsheetIsNotReopened:
    """Regression: get_sheet() re-authorised and re-opened the spreadsheet
    on every call, costing ~2s each. Tracking resolves three sheets, so the
    page spent ~6s just reconnecting and timed out in deployment.
    """

    def test_three_sheet_lookups_reuse_one_connection(self, monkeypatch, sheets):
        opens = {'client': 0, 'spreadsheet': 0}

        class FakeSpreadsheet:
            def worksheet(self, name):
                return sheets.get(name)

        class FakeClient:
            def open(self, name):
                opens['spreadsheet'] += 1
                return FakeSpreadsheet()

        def fake_client():
            opens['client'] += 1
            return FakeClient()

        monkeypatch.setattr(flask_app, '_SPREADSHEET_CACHE', None)
        monkeypatch.setattr(flask_app, 'get_sheets_client', fake_client)

        for name in (flask_app.SHEET_KENDARAAN,
                     flask_app.SHEET_SERVICE_MOBIL,
                     flask_app.SHEET_SERVICE_MOTOR):
            flask_app.get_sheet(name)

        assert opens['spreadsheet'] == 1, (
            'spreadsheet opened %d times for 3 sheet lookups' % opens['spreadsheet']
        )
        assert opens['client'] == 1, (
            'client authorised %d times for 3 sheet lookups' % opens['client']
        )
