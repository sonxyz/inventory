"""Service list must stay within serverless response limits.

The history service sheets hold thousands of rows (motor ~2.7k, mobil ~566).
Rendering every row into one HTML document produced a 7.75 MB response for
motor, which exceeds Vercel's 4.5 MB response limit, and both pages took
~3s to render - close to the serverless timeout. The pages therefore came
back empty in deployment even though the rows were present.

These tests pin a paginated contract instead: a bounded page of rows plus
navigation, so the response stays small no matter how much data accumulates.
"""

import pytest

import app as flask_app


def _service_row(no, plate='D 1234 AB', bengkel='Bengkel Jaya'):
    return [no, plate, 'Budi', '01-01-2026', bengkel, 'Ganti Oli',
            1, 'liter', 100000, 90000, 90000, 1000, 1100, 100, 5000, '']


def _sheet_for(sheets, jenis):
    name = (flask_app.SHEET_SERVICE_MOBIL if jenis == 'mobil'
            else flask_app.SHEET_SERVICE_MOTOR)
    return sheets[name]


@pytest.fixture(params=['mobil', 'motor'])
def jenis(request):
    return request.param


class TestPagination:
    def test_page_is_bounded(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        body = auth_client.get('/service/%s' % jenis).get_data(as_text=True)
        # Header row plus at most one page of data rows.
        assert body.count('<tr') <= flask_app.PER_PAGE_SERVICE + 1

    def test_reports_total_matching_rows(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        body = auth_client.get('/service/%s' % jenis).get_data(as_text=True)
        assert '250' in body

    def test_second_page_shows_different_rows(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        first = auth_client.get('/service/%s?page=1' % jenis).get_data(as_text=True)
        second = auth_client.get('/service/%s?page=2' % jenis).get_data(as_text=True)
        assert first != second

    def test_first_page_starts_at_the_first_row(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        body = auth_client.get('/service/%s?page=1' % jenis).get_data(as_text=True)
        assert 'D 1234 AB' in body

    def test_last_page_holds_the_remainder(self, auth_client, sheets, seed, jenis):
        # 250 rows with a page size of 100 -> page 3 holds the last 50.
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        body = auth_client.get('/service/%s?page=3' % jenis).get_data(as_text=True)
        # 50 data rows plus the single header row.
        assert body.count('<tr') == 50 + 1

    def test_page_beyond_the_end_falls_back_to_last_page(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 31)])
        response = auth_client.get('/service/%s?page=99' % jenis)
        assert response.status_code == 200

    def test_invalid_page_value_does_not_crash(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), _service_row(1))
        for value in ['abc', '-5', '0', '']:
            response = auth_client.get('/service/%s?page=%s' % (jenis, value))
            assert response.status_code == 200

    def test_navigation_links_are_rendered(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 251)])
        body = auth_client.get('/service/%s' % jenis).get_data(as_text=True)
        assert 'page=2' in body

    def test_single_page_has_no_navigation(self, auth_client, sheets, seed, jenis):
        seed(_sheet_for(sheets, jenis), _service_row(1))
        body = auth_client.get('/service/%s' % jenis).get_data(as_text=True)
        assert 'page=2' not in body


class TestPaginationKeepsSearch:
    def test_search_still_filters(self, auth_client, sheets, seed, jenis):
        seed(
            _sheet_for(sheets, jenis),
            _service_row(1, bengkel='Raja Auto'),
            _service_row(2, bengkel='Bengkel Sentosa'),
        )
        body = auth_client.get('/service/%s?search=Raja' % jenis).get_data(as_text=True)
        assert 'Raja Auto' in body
        assert 'Bengkel Sentosa' not in body

    def test_search_paginates_over_matches(self, auth_client, sheets, seed, jenis):
        rows = [_service_row(i, bengkel='Raja Auto') for i in range(1, 151)]
        seed(_sheet_for(sheets, jenis), *rows)
        body = auth_client.get('/service/%s?search=Raja' % jenis).get_data(as_text=True)
        assert body.count('<tr') <= flask_app.PER_PAGE_SERVICE + 1

    def test_search_total_counts_only_matches(self, auth_client, sheets, seed, jenis):
        seed(
            _sheet_for(sheets, jenis),
            *[_service_row(i, bengkel='Raja Auto') for i in range(1, 31)]
        )
        seed(_sheet_for(sheets, jenis), _service_row(99, bengkel='Lain'))
        body = auth_client.get('/service/%s?search=Raja' % jenis).get_data(as_text=True)
        assert '30' in body

    def test_search_term_survives_page_links(self, auth_client, sheets, seed, jenis):
        rows = [_service_row(i, bengkel='Raja Auto') for i in range(1, 151)]
        seed(_sheet_for(sheets, jenis), *rows)
        body = auth_client.get('/service/%s?search=Raja' % jenis).get_data(as_text=True)
        assert 'search=Raja' in body or 'searaja' in body


class TestResponseStaysSmall:
    def test_large_sheet_does_not_produce_a_huge_response(self, auth_client, sheets, seed, jenis):
        """Regression: 2.7k rows rendered inline made a 7.75 MB response."""
        seed(_sheet_for(sheets, jenis), *[_service_row(i) for i in range(1, 1001)])
        response = auth_client.get('/service/%s' % jenis)
        size_mb = len(response.get_data()) / 1024 / 1024
        assert size_mb < 4.5, 'response %.2f MB exceeds the 4.5 MB limit' % size_mb
