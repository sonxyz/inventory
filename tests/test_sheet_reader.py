"""Tolerant reading of the real Google Sheets layout.

The production spreadsheet does not match the header constants in app.py:

* ``Master Data Kendaraan`` stores its header in row 1 but column A is blank
  (``' '``), it has 30 columns against 25 expected, and two headers are
  duplicated (``Realisasi Pembayaran Pajak`` and ``PAJAK LANJUTAN``).
* ``History Service Kendaraan Motor`` keeps three blank rows above its header
  and spells the first header ``no``.
* Service dates are written ``DD-MM-YYYY``, not ``DD/MM/YYYY``.

``get_all_records()`` raises on a duplicate header row, and ``get_all_data``
swallowed that exception and returned ``[]`` - so pages rendered empty with no
error shown. These tests pin the behaviour the reader must provide instead.
"""

import pytest

import app as flask_app


class RawSheet:
    """A worksheet backed by literal rows, including its own header row."""

    def __init__(self, title, rows):
        self.title = title
        self._rows = [list(row) for row in rows]

    def get_all_values(self):
        return [list(row) for row in self._rows]

    def row_values(self, index):
        return list(self._rows[index - 1])

    def get_all_records(self):
        """Mirror gspread: a duplicate header row raises."""
        if not self._rows:
            return []
        header = self._rows[0]
        if len(set(header)) != len(header):
            raise RuntimeError(
                "the header row in the worksheet is not unique, "
                "try passing 'expected_headers' to get_all_records"
            )
        records = []
        for raw in self._rows[1:]:
            records.append({h: (raw[i] if i < len(raw) else '')
                            for i, h in enumerate(header)})
        return records


KENDARAAN_ROWS = [
    [' ', 'No. Kendaraan', 'Pemilik', 'Merk', 'Model Kendaraan', 'Jenis/Type',
     'Warna', 'Tahun Kendaraan', 'No. Rangka', 'No. Mesin', 'STNK 1 Tahun',
     'Realisasi Pembayaran Pajak', 'PAJAK LANJUTAN', 'STNK 5 Tahun',
     'Realisasi Pembayaran Pajak', 'PAJAK LANJUTAN', 'KIR',
     'Tanggal Realisasi KIR', 'JT KIR', 'No Asuransi', 'Nama Asuransi',
     'Jenis Asuransi', 'Tanggal Berlaku Asuransi', 'Periode Tahun Asuransi',
     'Biaya Premi Asuransi', 'GPS/APCT', 'No. BPKB', 'Posisi BPKB',
     'Bahan Bakar', 'Keterangan'],
    ['1', 'D 4785 SBG', 'BOBY', 'Honda', 'REVO FIT', 'HONDA/NF11T11C01 M/T',
     'Merah', '2020', 'RANGKA-1', 'MESIN-1', '21/08/2026', '01/01/2026', '',
     '31/12/2030', '', '', '', '01/01/2026', '', 'POLIS-1', 'Asuransi ABC',
     'All Risk', '01/01/2026', '2026', '2500000', 'GPS-1', 'BPKB-1',
     'Kantor', 'Bensin', 'catatan'],
]

MOTOR_ROWS = [
    [],
    [],
    [],
    ['no', 'No. Kendaraan', 'Nama Pemilik', 'Tanggal Service', 'Nama Bengkel ',
     'Jenis Service', 'Jumlah Part', 'Satuan', 'Pengajuan', 'Realisasi',
     'Total', 'KM Awal', 'KM Akhir', 'Selisih KM', 'KM Selanjutnya',
     'Keterangan'],
    ['1', 'D 4840 SBA', 'CV. DPP', '25-04-2026', '', 'Ganti oli', '1',
     'liter', '50000', '45000', '45000', '10000', '10500', '500', '15000',
     'rutin'],
]


class TestHeaderRowDetection:
    def test_skips_blank_leading_rows(self):
        sheet = RawSheet('History Service Kendaraan Motor', MOTOR_ROWS)
        records = flask_app.get_all_data(sheet)
        assert len(records) == 1
        assert records[0]['No. Kendaraan'] == 'D 4840 SBA'

    def test_tolerates_duplicate_headers(self):
        sheet = RawSheet('Master Data Kendaraan', KENDARAAN_ROWS)
        records = flask_app.get_all_data(sheet)
        assert len(records) == 1

    def test_duplicate_headers_do_not_lose_the_first_value(self):
        sheet = RawSheet('Master Data Kendaraan', KENDARAAN_ROWS)
        row = flask_app.get_all_data(sheet)[0]
        # First occurrence of the duplicated header keeps the real value.
        assert row['Realisasi Pembayaran Pajak'] == '01/01/2026'

    def test_blank_first_header_maps_to_no(self):
        sheet = RawSheet('Master Data Kendaraan', KENDARAAN_ROWS)
        row = flask_app.get_all_data(sheet)[0]
        assert row['No'] == '1'

    def test_columns_after_the_extra_block_still_align(self):
        sheet = RawSheet('Master Data Kendaraan', KENDARAAN_ROWS)
        row = flask_app.get_all_data(sheet)[0]
        # These live past the three extra columns (PAJAK LANJUTAN / KIR /
        # JT KIR); positional mapping would shift them by three.
        assert row['STNK 5 Tahun'] == '31/12/2030'
        assert row['Tanggal Realisasi KIR'] == '01/01/2026'
        assert row['No Asuransi'] == 'POLIS-1'
        assert row['GPS/APCT'] == 'GPS-1'
        assert row['Keterangan'] == 'catatan'

    def test_empty_sheet_returns_empty_list(self):
        assert flask_app.get_all_data(RawSheet('Master Data Kendaraan', [])) == []


class TestServiceDateFormats:
    @pytest.mark.parametrize('raw', ['25-04-2026', '25/04/2026'])
    def test_both_separators_parse(self, raw):
        assert flask_app.parse_date(raw).strftime('%d/%m/%Y') == '25/04/2026'

    def test_service_rows_keep_their_values(self):
        sheet = RawSheet('History Service Kendaraan Mobil', [
            ['No', 'No. Kendaraan', 'Nama Pemilik', 'Tanggal Service',
             'Nama Bengkel', 'Jenis Service', 'Jumlah Part', 'Satuan',
             'Pengajuan', 'Realisasi', 'Total', 'KM Awal', 'KM Akhir',
             'Selisih KM', 'KM Selanjutnya', 'Keterangan'],
            ['1', 'D 1', 'A', '01-01-2026', 'B', 'Ganti Oli', '1', 'liter',
             '1', '1', '1', '0', '100', '100', '200', ''],
            ['2', 'D 1', 'A', '01-06-2026', 'B', 'Tune Up', '1', 'paket',
             '1', '1', '1', '100', '200', '100', '300', ''],
        ])
        records = flask_app.get_all_data(sheet)
        assert [r['Jenis Service'] for r in records] == ['Ganti Oli', 'Tune Up']
        assert records[0]['Tanggal Service'] == '01-01-2026'


class TestPagesRenderRealSheetShapes:
    """The reported bug: pages rendered empty while the data was present."""

    def _client_for(self, auth_client, monkeypatch, sheets_by_name):
        monkeypatch.setattr(
            flask_app, 'get_sheet', lambda name: sheets_by_name.get(name)
        )
        return auth_client

    def test_kendaraan_list_shows_rows(self, auth_client, monkeypatch):
        self._client_for(auth_client, monkeypatch, {
            flask_app.SHEET_KENDARAAN: RawSheet(
                flask_app.SHEET_KENDARAAN, KENDARAAN_ROWS),
        })
        body = auth_client.get('/kendaraan').get_data(as_text=True)
        assert 'D 4785 SBG' in body
        assert 'BOBY' in body

    def test_kendaraan_list_shows_shifted_document_columns(self, auth_client, monkeypatch):
        self._client_for(auth_client, monkeypatch, {
            flask_app.SHEET_KENDARAAN: RawSheet(
                flask_app.SHEET_KENDARAAN, KENDARAAN_ROWS),
        })
        body = auth_client.get('/kendaraan').get_data(as_text=True)
        # 'Bensin' sits in Bahan Bakar, past the three extra columns; a
        # positional read would shift it and the cell would render as '-'.
        assert 'Bensin' in body

    def test_service_motor_list_shows_rows(self, auth_client, monkeypatch):
        self._client_for(auth_client, monkeypatch, {
            flask_app.SHEET_SERVICE_MOTOR: RawSheet(
                flask_app.SHEET_SERVICE_MOTOR, MOTOR_ROWS),
        })
        body = auth_client.get('/service/motor').get_data(as_text=True)
        assert 'D 4840 SBA' in body
        assert 'Ganti oli' in body
