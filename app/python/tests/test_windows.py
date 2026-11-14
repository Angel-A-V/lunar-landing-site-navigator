"""Tests for analysis/windows.py: yearly statistics and longest stretches.

Offline, no network.
Run (from app/python):  python3 -m unittest tests.test_windows -v
"""
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, PYDIR)

from analysis.visibility import analyse, load_horizons, load_skyline  # noqa: E402
from analysis.windows import longest_run, window_stats  # noqa: E402


def make_rows(sun, earth):
    """Made-up rows from two lists of True/False."""
    return [
        {"sun_visible": s, "earth_visible": e, "both_visible": s and e}
        for s, e in zip(sun, earth)
    ]


class LongestRun(unittest.TestCase):
    def test_finds_the_longest_stretch_of_a_value(self):
        rows = make_rows([True, True, False, True, True, True, False], [False] * 7)
        self.assertEqual(longest_run(rows, "sun_visible", True, 1.0), 3.0)
        self.assertEqual(longest_run(rows, "sun_visible", False, 1.0), 1.0)

    def test_whole_series_one_value(self):
        rows = make_rows([True] * 5, [False] * 5)
        self.assertEqual(longest_run(rows, "sun_visible", True, 1.0), 5.0)

    def test_value_never_happens(self):
        rows = make_rows([True] * 5, [False] * 5)
        self.assertEqual(longest_run(rows, "sun_visible", False, 1.0), 0.0)

    def test_empty_rows(self):
        self.assertEqual(longest_run([], "sun_visible", True, 1.0), 0.0)

    def test_step_hours_scales_the_answer(self):
        rows = make_rows([True, True, True, False], [False] * 4)
        self.assertEqual(longest_run(rows, "sun_visible", True, 6.0), 18.0)


class WindowStats(unittest.TestCase):
    def setUp(self):
        sun = [True, True, False, False, False, True]
        earth = [False, True, True, False, False, False]
        self.stats = window_stats(make_rows(sun, earth), step_hours=6.0)

    def test_percentages(self):
        self.assertAlmostEqual(self.stats["sun_visible_pct"], 50.0)
        self.assertAlmostEqual(self.stats["earth_visible_pct"], 100 * 2 / 6)
        self.assertAlmostEqual(self.stats["both_visible_pct"], 100 / 6)

    def test_longest_stretches_in_hours(self):
        self.assertEqual(self.stats["longest_sun_dark_hours"], 18.0)       # 3 samples * 6 h
        self.assertEqual(self.stats["longest_sun_lit_hours"], 12.0)        # 2 samples * 6 h
        self.assertEqual(self.stats["longest_earth_blocked_hours"], 18.0)  # indices 3..5
        self.assertEqual(self.stats["longest_earth_visible_hours"], 12.0)

    def test_span_in_days(self):
        self.assertAlmostEqual(self.stats["span_days"], 6 * 6.0 / 24)

    def test_empty_rows_do_not_crash(self):
        s = window_stats([], step_hours=1.0)
        self.assertEqual(s["samples"], 0)
        self.assertEqual(s["sun_visible_pct"], 0.0)


class RealYear(unittest.TestCase):
    def _year(self, site):
        sky = load_skyline(os.path.join(ROOT, "data", f"skyline_{site}.csv"))
        path = os.path.join(ROOT, "data", f"horizons_{site}_2026-11-10_365d_6h.csv")
        return window_stats(analyse(load_horizons(path), sky), step_hours=6.0)

    def test_shackleton_rim_matches_the_earlier_notes(self):
        # CLAUDE.md (2026-11-10): Sun above the real skyline ~80%, Earth ~51%, both ~41%.
        # This is the ORIGINAL 35 km skyline (the wall file). The website uses the extended one.
        s = self._year("shackleton_rim")
        self.assertEqual(s["samples"], 1461)
        self.assertAlmostEqual(s["sun_visible_pct"], 80.0, delta=4.0)
        self.assertAlmostEqual(s["earth_visible_pct"], 51.0, delta=4.0)
        self.assertAlmostEqual(s["both_visible_pct"], 41.0, delta=4.0)

    def test_shackleton_crater_floor_never_sees_the_sun(self):
        # Its skyline is 18 to 22 degrees up in every direction; the Sun never passes about 2 degrees.
        s = self._year("shackleton")
        self.assertEqual(s["sun_visible_pct"], 0.0)
        self.assertAlmostEqual(s["longest_sun_dark_hours"], 1461 * 6.0)


if __name__ == "__main__":
    unittest.main()
