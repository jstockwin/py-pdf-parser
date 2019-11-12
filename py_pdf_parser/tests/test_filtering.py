from ddt import ddt, unpack, data
from unittest import TestCase

from py_pdf_parser.filtering import _combine_bounds, _sanitise_bounds, Bound


@ddt
class TestFilters(TestCase):
    @unpack
    @data(
        {
            "bounds_a": [Bound(0, 10)],
            "bounds_b": [Bound(5, 10)],
            "expected_result": [Bound(5, 10)],
        },
        {
            "bounds_a": [Bound(0, 5)],
            "bounds_b": [Bound(5, 10)],
            "expected_result": [Bound(5, 5)],
        },
        {
            "bounds_a": [Bound(10, 100)],
            "bounds_b": [Bound(5, 15), Bound(30, 35), Bound(60, 80), Bound(95, 105)],
            "expected_result": [
                Bound(10, 15),
                Bound(30, 35),
                Bound(60, 80),
                Bound(95, 100),
            ],
        },
        {"bounds_a": [Bound(0, 5)], "bounds_b": [Bound(10, 20)], "expected_result": []},
    )
    def test_combine_bounds(self, bounds_a, bounds_b, expected_result):
        self.assertListEqual(_combine_bounds(bounds_a, bounds_b), expected_result)

    @unpack
    @data(
        {"bounds": [Bound(0, 1), Bound(1, 2)], "expected_result": [Bound(0, 2)]},
        {"bounds": [Bound(0, 1), Bound(2, 3)], "expected_result": [Bound(0, 3)]},
        {"bounds": [Bound(0, 4), Bound(2, 3)], "expected_result": [Bound(0, 4)]},
        {"bounds": [Bound(0, 4), Bound(2, 4)], "expected_result": [Bound(0, 4)]},
        {"bounds": [Bound(0, 4), Bound(2, 6)], "expected_result": [Bound(0, 6)]},
    )
    def test_sanitise_bounds(self, bounds, expected_result):
        self.assertListEqual(_sanitise_bounds(bounds), expected_result)
