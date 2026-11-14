"""Tests for analysis/visibility.py. Offline, no network.

Run:  python3 -m unittest tests.test_visibility -v
"""
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, PYDIR)

from analysis.visibility import analyse, load_horizons, load_skyline, skyline_at, summarise  # noqa: E402

SKYLINE_CSV = os.path.join(ROOT, "data", "skyline_shackleton_rim.csv")
HORIZONS_CSV = os.path.join(ROOT, "data", "horizons_shackleton_rim_2026-11-10_30d_1h.csv")


class SkylineLookup(unittest.TestCase):
    def test_flat_skyline_is_zero_everywhere(self):
        flat = [0.0] * 360
        for az in (0, 12.5, 180, 359.99, 720.3, -10):
            self.assertAlmostEqual(skyline_at(flat, az), 0.0)

    def test_whole_degree_returns_that_row(self):
        sky = [float(i) for i in range(360)]
        self.assertEqual(skyline_at(sky, 213.0), 213.0)

    def test_blends_neighbours(self):
        sky = [float(i) for i in range(360)]
        self.assertAlmostEqual(skyline_at(sky, 213.4), 213.4)

    def test_wraps_around_north(self):
        sky = [0.0] * 360
        sky[359] = 1.0
        sky[0] = 3.0
        self.assertAlmostEqual(skyline_at(sky, 359.5), 2.0)

    def test_negative_and_over_360_azimuths_wrap(self):
        sky = [float(i) for i in range(360)]
        self.assertAlmostEqual(skyline_at(sky, -1.0), 359.0)
        self.assertAlmostEqual(skyline_at(sky, 361.0), 1.0)


class VisibilityLogic(unittest.TestCase):
    def _row(self, sun_el, earth_el):
        return {"time_utc": "t", "sun_az_deg": 90.0, "sun_el_deg": sun_el,
                "earth_az_deg": 180.0, "earth_el_deg": earth_el}

    def test_above_skyline_is_visible_below_is_blocked(self):
        sky = [1.0] * 360  # a 1 degree wall all the way round
        out = analyse([self._row(1.5, 0.5)], sky)[0]
        self.assertTrue(out["sun_visible"])
        self.assertAlmostEqual(out["sun_margin_deg"], 0.5)
        self.assertFalse(out["earth_visible"])
        self.assertFalse(out["both_visible"])

    def test_body_below_flat_horizon_can_still_be_visible(self):
        sky = [-2.0] * 360  # looking down from a high rim
        out = analyse([self._row(-1.0, -3.0)], sky)[0]
        self.assertTrue(out["sun_visible"])
        self.assertFalse(out["earth_visible"])

    def test_summary_percentages(self):
        sky = [0.0] * 360
        rows = analyse([self._row(1, 1), self._row(1, -1), self._row(-1, -1), self._row(-1, 1)], sky)
        s = summarise(rows)
        self.assertEqual(s["samples"], 4)
        self.assertAlmostEqual(s["sun_visible_pct"], 50.0)
        self.assertAlmostEqual(s["earth_visible_pct"], 50.0)
        self.assertAlmostEqual(s["both_visible_pct"], 25.0)


class RealData(unittest.TestCase):
    def test_skyline_file_loads(self):
        sky = load_skyline(SKYLINE_CSV)
        self.assertEqual(len(sky), 360)

    def test_first_row_matches_hand_calculation(self):
        # Sun az 331.6598 sits between row 331 (-1.240) and row 332 (-1.208):
        # -1.240 + 0.6598 * 0.032 = -1.2189. Sun el 1.7370 -> margin +2.9559.
        sky = load_skyline(SKYLINE_CSV)
        first = analyse(load_horizons(HORIZONS_CSV), sky)[0]
        self.assertAlmostEqual(first["sun_skyline_deg"], -1.2189, places=3)
        self.assertAlmostEqual(first["sun_margin_deg"], 2.9559, places=3)
        self.assertTrue(first["sun_visible"])

    def test_row_count(self):
        self.assertEqual(len(load_horizons(HORIZONS_CSV)), 721)


if __name__ == "__main__":
    unittest.main()
