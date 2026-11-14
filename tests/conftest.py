"""Shared fixtures: an in-memory fake of the gspread worksheet API.

The app talks to Google Sheets through a handful of module-level helpers
(``get_sheet``, ``get_all_data``, ``find_row_by_no``, ``get_next_no``).  The
fake below implements just enough of the real worksheet surface that every
route can run offline, with no credentials and no network.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as flask_app


class FakeCell:
    """Mimics the ``.row`` attribute returned by ``worksheet.find()``."""

    def __init__(self, row):
        self.row = row


class FakeSheet:
    """List-of-lists worksheet backed by the sheet's header row."""

    def __init__(self, title, headers):
        self.title = title
        self.headers = list(headers)
        self._rows = []

    @property
    def rows(self):
        """Raw data rows (header excluded), as a defensive copy."""
        return [list(row) for row in self._rows]

    def get_all_records(self):
        records = []
        for raw in self._rows:
            record = {}
            for index, header in enumerate(self.headers):
                record[header] = raw[index] if index < len(raw) else ''
            records.append(record)
        return records

    def append_row(self, row, value_input_option=None):
        self._rows.append(list(row))

    def find(self, query, in_column=1):
        column = in_column - 1
        for index, raw in enumerate(self._rows):
            value = raw[column] if column < len(raw) else ''
            if str(value) == str(query):
                # +1 for the header row, +1 because sheet rows are 1-based.
                return FakeCell(index + 2)
        return None

    def update(self, range_name, values, value_input_option=None):
        """Write ``values`` into the A1 range, touching only those cells."""
        start, _, end = range_name.partition(':')
        start_col, start_row = _split_a1(start)
        end_col, end_row = _split_a1(end or start)

        row_index = start_row - 2
        while len(self._rows) <= row_index:
            self._rows.append([])

        target = self._rows[row_index]
        for offset, value in enumerate(values[0] if values else []):
            column = start_col + offset
            if column > end_col:
                break
            while len(target) <= column:
                target.append('')
            target[column] = value

    def delete_rows(self, row_number):
        self._rows.pop(row_number - 2)


def _split_a1(reference):
    """Turn ``'L3'`` into ``(11, 3)`` — zero-based column, 1-based row."""
    letters = ''.join(char for char in reference if char.isalpha())
    digits = ''.join(char for char in reference if char.isdigit())
    column = 0
    for char in letters.upper():
        column = column * 26 + (ord(char) - ord('A') + 1)
    return column - 1, int(digits)


@pytest.fixture
def sheets():
    """All worksheets the app expects, keyed by their exact sheet name."""
    return {
        flask_app.SHEET_KENDARAAN: FakeSheet(
            flask_app.SHEET_KENDARAAN, flask_app.HEADERS_KENDARAAN
        ),
        flask_app.SHEET_SERVICE_MOBIL: FakeSheet(
            flask_app.SHEET_SERVICE_MOBIL, flask_app.HEADERS_SERVICE
        ),
        flask_app.SHEET_SERVICE_MOTOR: FakeSheet(
            flask_app.SHEET_SERVICE_MOTOR, flask_app.HEADERS_SERVICE
        ),
        flask_app.SHEET_MASTER_ATK: FakeSheet(
            flask_app.SHEET_MASTER_ATK, flask_app.HEADERS_MASTER_ATK
        ),
        flask_app.SHEET_MASTER_DEPT: FakeSheet(
            flask_app.SHEET_MASTER_DEPT, flask_app.HEADERS_MASTER_DEPT
        ),
        flask_app.SHEET_PENGAJUAN_ATK: FakeSheet(
            flask_app.SHEET_PENGAJUAN_ATK, flask_app.HEADERS_PENGAJUAN_ATK
        ),
        flask_app.SHEET_MASTER_USERS: FakeSheet(
            flask_app.SHEET_MASTER_USERS, flask_app.HEADERS_MASTER_USERS
        ),
    }


@pytest.fixture
def client(sheets, monkeypatch):
    """Flask test client wired to the fake sheets, no session."""
    monkeypatch.setattr(flask_app, 'get_sheet', lambda name: sheets.get(name))
    monkeypatch.setattr(flask_app, 'get_spreadsheet', lambda: None)
    flask_app.app.config.update(TESTING=True)
    with flask_app.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def auth_client(client):
    """Test client already logged in with full admin rights."""
    with client.session_transaction() as session:
        session['user'] = 'tester'
        session['role'] = 'admin'
    return client


@pytest.fixture
def seed():
    """Append raw rows to a fake sheet."""

    def _seed(sheet, *rows):
        for row in rows:
            sheet.append_row(list(row))

    return _seed
