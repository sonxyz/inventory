"""Per-vehicle service tracking timeline."""

import app as flask_app

KENDARAAN = [1, 'B 1234 XY', 'Budi', 'Toyota', 'Avanza', 'MPV', 'Putih', 2020,
             'RANGKA-1', 'MESIN-1', '31/12/2026', '01/01/2026', '31/12/2030',
             '01/01/2026', 'POLIS-1', 'Asuransi ABC', 'All Risk', '01/01/2026',
             '2026', '2500000', 'GPS-1', 'BPKB-1', 'Kantor', 'Bensin', '']

MOBIL_1 = [1, 'B 1234 XY', 'Budi', '01/01/2026', 'Bengkel Jaya', 'Ganti Oli',
           4, 'liter', 500000, 450000, 450000, 10000, 10500, 500, 15000, '']
MOBIL_2 = [2, 'B 1234 XY', 'Budi', '01/06/2026', 'Bengkel Jaya', 'Tune Up',
           1, 'paket', 800000, 750000, 750000, 10500, 11000, 500, 20000, '']
MOTOR_1 = [1, 'B 1234 XY', 'Budi', '01/03/2026', 'Bengkel Motor', 'Servis Ringan',
           1, 'paket', 200000, 180000, 180000, 5000, 5500, 500, 8000, '']
OTHER = [9, 'B 9999 ZZ', 'Lain', '01/01/2026', 'Bengkel X', 'Ganti Oli',
         1, 'liter', 100000, 90000, 90000, 1000, 1100, 100, 5000, '']


class TestTracking:
    def test_renders_for_known_vehicle(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], KENDARAAN)
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], MOBIL_1)
        response = auth_client.get('/kendaraan/tracking/B 1234 XY')
        assert response.status_code == 200

    def test_combines_mobil_and_motor_history(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], KENDARAAN)
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], MOBIL_1, MOBIL_2)
        seed(sheets[flask_app.SHEET_SERVICE_MOTOR], MOTOR_1)
        body = auth_client.get('/kendaraan/tracking/B 1234 XY').get_data(as_text=True)
        assert 'Ganti Oli' in body
        assert 'Tune Up' in body
        assert 'Servis Ringan' in body

    def test_excludes_other_vehicles(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], KENDARAAN)
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], MOBIL_1, OTHER)
        body = auth_client.get('/kendaraan/tracking/B 1234 XY').get_data(as_text=True)
        assert 'Ganti Oli' in body
        assert 'Bengkel X' not in body

    def test_plate_match_is_case_insensitive(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], KENDARAAN)
        seed(sheets[flask_app.SHEET_SERVICE_MOBIL], MOBIL_1)
        body = auth_client.get('/kendaraan/tracking/b 1234 xy').get_data(as_text=True)
        assert 'Ganti Oli' in body

    def test_vehicle_without_service_history(self, auth_client, sheets, seed):
        seed(sheets[flask_app.SHEET_KENDARAAN], KENDARAAN)
        assert auth_client.get('/kendaraan/tracking/B 1234 XY').status_code == 200
