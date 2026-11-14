"""Unit tests for the pure helpers shared by every module."""

from datetime import datetime, timedelta

import pytest

from app import (
    filter_records,
    format_currency,
    is_expiring_soon,
    parse_date,
    safe_num,
)


class TestSafeNum:
    @pytest.mark.parametrize('raw,expected', [
        ('150.000', 150000.0),
        ('1.500.000', 1500000.0),
        ('Rp 25.000', 25000.0),
        ('1500', 1500.0),
        ('1,5', 1.5),
        ('150.000,50', 150000.5),
        ('1,500,000.00', 1500000.0),
        (150000.0, 150000.0),
        (7, 7.0),
    ])
    def test_parses_formatted_numbers(self, raw, expected):
        assert safe_num(raw) == pytest.approx(expected)

    @pytest.mark.parametrize('raw', ['', None, 'abc', '   '])
    def test_unparseable_values_become_zero(self, raw):
        assert safe_num(raw) == 0.0


class TestFormatCurrency:
    @pytest.mark.parametrize('value,expected', [
        (150000, 'Rp 150.000'),
        (1500000, 'Rp 1.500.000'),
        ('Rp 25.000', 'Rp 25.000'),
        (0, 'Rp 0'),
    ])
    def test_formats_rupiah_with_dot_separators(self, value, expected):
        assert format_currency(value) == expected

    def test_millions_do_not_lose_a_digit(self):
        # Regression: a naive float format once turned 1_000_000 into 100_000.
        assert format_currency(1000000) == 'Rp 1.000.000'


class TestParseDate:
    @pytest.mark.parametrize('raw', ['01/01/2026', '1/1/2026'])
    def test_accepts_dd_mm_yyyy(self, raw):
        parsed = parse_date(raw)
        assert parsed == datetime(2026, 1, 1)

    @pytest.mark.parametrize('raw', ['2026-01-01', '2026/01/01', '01-01-2026', '', None, 'nonsense'])
    def test_rejects_other_formats(self, raw):
        assert parse_date(raw) is None


class TestIsExpiringSoon:
    def test_true_inside_window(self):
        soon = (datetime.today() + timedelta(days=10)).strftime('%d/%m/%Y')
        assert is_expiring_soon(soon, days=30) is True

    def test_false_outside_window(self):
        later = (datetime.today() + timedelta(days=45)).strftime('%d/%m/%Y')
        assert is_expiring_soon(later, days=30) is False

    def test_false_for_past_dates(self):
        past = (datetime.today() - timedelta(days=1)).strftime('%d/%m/%Y')
        assert is_expiring_soon(past, days=30) is False

    def test_false_for_unparseable_input(self):
        assert is_expiring_soon('', days=30) is False
        assert is_expiring_soon(None, days=30) is False


class TestFilterRecords:
    RECORDS = [
        {'Kode': 'ATK-001', 'Nama Barang': 'Kertas HVS A4', 'Satuan': 'rim'},
        {'Kode': 'ATK-002', 'Nama Barang': 'Pulpen Hitam', 'Satuan': 'pcs'},
    ]

    def test_empty_search_returns_everything(self):
        assert filter_records(self.RECORDS, '', ['Kode']) == self.RECORDS

    def test_matches_code(self):
        result = filter_records(self.RECORDS, 'ATK-002', ['Kode', 'Nama Barang'])
        assert [r['Kode'] for r in result] == ['ATK-002']

    def test_matches_name_case_insensitively(self):
        result = filter_records(self.RECORDS, 'pulpen', ['Kode', 'Nama Barang'])
        assert [r['Kode'] for r in result] == ['ATK-002']

    def test_matches_only_configured_fields(self):
        # 'rim' lives in Satuan, which is not in the searchable field list.
        assert filter_records(self.RECORDS, 'rim', ['Kode', 'Nama Barang']) == []

    def test_no_match_returns_empty_list(self):
        assert filter_records(self.RECORDS, 'zzz', ['Kode', 'Nama Barang']) == []
