"""Rekap Pengajuan ATK, including the per-departement filter.

Rows use a fixed 2026 period, so requests pass ``tahun=2026`` explicitly.
The default-year behaviour is covered separately in TestRekapDefaultYear.
"""

from datetime import datetime

import app as flask_app

YEAR = '2026'

HRD_KERTAS = [1, '01/01/2026', 'Januari', 2026, 'HRD', 'ATK-001',
              'Kertas HVS A4', 2, 'rim', 50000, 100000, '']
HRD_PULPEN = [2, '02/01/2026', 'Januari', 2026, 'HRD', 'ATK-002',
              'Pulpen Hitam', 5, 'pcs', 3000, 15000, '']
IT_PULPEN = [3, '03/01/2026', 'Januari', 2026, 'IT', 'ATK-002',
             'Pulpen Hitam', 10, 'pcs', 3000, 30000, '']
FEB_HRD = [4, '05/02/2026', 'Februari', 2026, 'HRD', 'ATK-009',
           'Spidol', 1, 'pcs', 5000, 5000, '']


def _pengajuan(sheets):
    return sheets[flask_app.SHEET_PENGAJUAN_ATK]


def _dept(sheets):
    return sheets[flask_app.SHEET_MASTER_DEPT]


class TestRekapDepartementFilter:
    """ISSUE-REKAP-DEPT.md: the rekap page must be filterable by department."""

    def test_dropdown_lists_master_departements(self, auth_client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        assert 'value="HRD"' in body
        assert 'value="IT"' in body

    def test_filter_narrows_rekap_to_one_department(self, auth_client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get(
            '/atk/rekap?departement=HRD&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'value="IT" selected' not in body

    def test_filter_changes_grand_total(self, auth_client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get(
            '/atk/rekap?departement=HRD&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Rp 100.000' in body
        assert 'Rp 130.000' not in body

    def test_selected_department_is_echoed_back(self, auth_client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get(
            '/atk/rekap?departement=IT&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'value="IT" selected' in body

    def test_no_filter_includes_every_department(self, auth_client, sheets, seed):
        seed(_dept(sheets), [1, 'HRD'], [2, 'IT'])
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        assert 'Rp 130.000' in body

    def test_filter_combines_with_bulan(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS, FEB_HRD)
        body = auth_client.get(
            '/atk/rekap?departement=HRD&bulan=Februari&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas HVS A4' not in body

    def test_unknown_department_yields_empty_rekap(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS)
        body = auth_client.get(
            '/atk/rekap?departement=Ghost&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Tidak ada data rekap' in body


class TestRekapAggregation:
    def test_department_total_sums_its_rows(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS, HRD_PULPEN)
        body = auth_client.get(
            '/atk/rekap?departement=HRD&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Rp 115.000' in body

    def test_barang_total_sums_quantity_across_departments(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_PULPEN, IT_PULPEN)
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        # Pulpen Hitam: 5 (HRD) + 10 (IT) = 15 units.
        assert '>15<' in body

    def test_barang_total_sums_harga_across_departments(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_PULPEN, IT_PULPEN)
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        # Pulpen Hitam: 15.000 + 30.000 = 45.000.
        assert 'Rp 45.000' in body

    def test_stats_cards_render(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS, IT_PULPEN)
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        assert 'Total Departemen' in body
        assert 'Total Item' in body
        assert 'Grand Total' in body

    def test_empty_data_renders_empty_state(self, auth_client):
        body = auth_client.get('/atk/rekap?tahun=' + YEAR).get_data(as_text=True)
        assert 'Tidak ada data rekap' in body


class TestRekapBulanFilter:
    def test_bulan_narrows_rows(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS, FEB_HRD)
        body = auth_client.get(
            '/atk/rekap?bulan=Februari&tahun=' + YEAR
        ).get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas HVS A4' not in body

    def test_all_months_option_keeps_everything(self, auth_client, sheets, seed):
        seed(_pengajuan(sheets), HRD_KERTAS, FEB_HRD)
        body = auth_client.get('/atk/rekap?bulan=&tahun=' + YEAR).get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas HVS A4' in body


class TestRekapDefaultYear:
    """With no ``tahun`` param the page filters to the current year."""

    def test_default_filters_to_current_year(self, auth_client, sheets, seed):
        year = datetime.today().year
        this_year = [1, '01/01/%d' % year, 'Januari', year, 'HRD',
                     'ATK-001', 'Kertas HVS A4', 2, 'rim', 50000, 100000, '']
        last_year = [2, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), this_year, last_year)
        body = auth_client.get('/atk/rekap').get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'Spidol' not in body

    def test_default_year_is_shown_even_when_data_lacks_it(self, auth_client, sheets, seed):
        """The active filter must be visible, or empty results look like a bug."""
        year = datetime.today().year
        last_year = [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), last_year)
        body = auth_client.get('/atk/rekap').get_data(as_text=True)
        assert 'Spidol' not in body
        assert 'value="%d" selected' % year in body

    def test_explicit_year_overrides_default(self, auth_client, sheets, seed):
        year = datetime.today().year
        last_year = [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), last_year)
        body = auth_client.get(
            '/atk/rekap?tahun=%d' % (year - 1)
        ).get_data(as_text=True)
        assert 'Spidol' in body
        assert 'value="%d" selected' % (year - 1) in body

    def test_blank_year_means_all_years(self, auth_client, sheets, seed):
        year = datetime.today().year
        seed(
            _pengajuan(sheets),
            [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
             'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, ''],
            [2, '01/01/%d' % year, 'Januari', year, 'HRD',
             'ATK-001', 'Kertas', 1, 'rim', 50000, 50000, ''],
        )
        body = auth_client.get('/atk/rekap?tahun=').get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas' in body


class TestRekapDefaultYear:
    """With no ``tahun`` param the page filters to the current year.

    Regression: the year dropdown used to be built only from years present in
    the data, so when the current year had no rows the page filtered everything
    out while the dropdown showed a *different* year as the only option and
    nothing selected - empty results with no visible cause.
    """

    def test_default_filters_to_current_year(self, auth_client, sheets, seed):
        year = datetime.today().year
        this_year = [1, '01/01/%d' % year, 'Januari', year, 'HRD',
                     'ATK-001', 'Kertas HVS A4', 2, 'rim', 50000, 100000, '']
        last_year = [2, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), this_year, last_year)
        body = auth_client.get('/atk/rekap').get_data(as_text=True)
        assert 'Kertas HVS A4' in body
        assert 'Spidol' not in body

    def test_active_year_is_shown_even_when_data_lacks_it(self, auth_client, sheets, seed):
        year = datetime.today().year
        last_year = [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), last_year)
        body = auth_client.get('/atk/rekap').get_data(as_text=True)
        # Rows are filtered out by the implicit current-year filter...
        assert 'Spidol' not in body
        # ...so the year actually in effect must be visible and selected.
        assert 'value="%d" selected' % year in body

    def test_explicit_year_overrides_default(self, auth_client, sheets, seed):
        year = datetime.today().year
        last_year = [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
                     'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, '']
        seed(_pengajuan(sheets), last_year)
        body = auth_client.get('/atk/rekap?tahun=%d' % (year - 1)).get_data(as_text=True)
        assert 'Spidol' in body
        assert 'value="%d" selected' % (year - 1) in body

    def test_blank_year_means_all_years(self, auth_client, sheets, seed):
        year = datetime.today().year
        seed(
            _pengajuan(sheets),
            [1, '01/01/%d' % (year - 1), 'Januari', year - 1, 'HRD',
             'ATK-009', 'Spidol', 1, 'pcs', 5000, 5000, ''],
            [2, '01/01/%d' % year, 'Januari', year, 'HRD',
             'ATK-001', 'Kertas', 1, 'rim', 50000, 50000, ''],
        )
        body = auth_client.get('/atk/rekap?tahun=').get_data(as_text=True)
        assert 'Spidol' in body
        assert 'Kertas' in body
