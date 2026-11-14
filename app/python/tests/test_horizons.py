"""Tests for scripts/fetch_horizons.py. Offline: no network needed.

Run:  python3 -m unittest tests.test_horizons -v
"""
import csv
import glob
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, os.path.join(PYDIR, "scripts"))
import fetch_horizons as H  # noqa: E402

# A real reply snippet from Horizons (Sun seen from Shackleton rim, 2026-11-10).
SAMPLE = """header junk
 Date__(UT)__HR:MN, , ,Azi_(a-app), Elev_(a-app),
*************************************************
$$SOE
 2026-Nov-10 00:00,*, , 331.659769,     1.737020,
 2026-Nov-10 02:00,*, , 330.642797,     1.735654,
$$EOE
footer junk
"""


class Parser(unittest.TestCase):
    def test_parses_rows(self):
        rows = H.parse_result(SAMPLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ("2026-Nov-10 00:00", 331.659769, 1.737020))

    def test_rejects_reply_without_data(self):
        with self.assertRaises(ValueError):
            H.parse_result("No ephemeris for target")

    def test_query_uses_moon_surface_observer(self):
        p = H.build_params("10", -89.781, 203.743, 1738.0, "2026-11-10", "2026-11-11", "1 h")
        self.assertEqual(p["CENTER"], "'coord@301'")           # observer on the Moon
        self.assertEqual(p["SITE_COORD"], "'203.743,-89.781,1.7380'")  # east lon, lat, km
        self.assertEqual(p["QUANTITIES"], "'4'")               # azimuth + elevation
        self.assertEqual(p["APPARENT"], "'AIRLESS'")           # no atmosphere


class CachedData(unittest.TestCase):
    """Physics sanity checks on the saved data (skipped if not fetched yet)."""

    def rows(self):
        # The limits below are for the model site, 6.6 km from the pole.
        files = glob.glob(os.path.join(ROOT, "data", "horizons_shackleton_rim_*_365d_*.csv"))
        if not files:
            self.skipTest("no cached 365-day Horizons file")
        with open(files[0]) as f:
            return list(csv.DictReader(f))

    def test_sun_stays_near_horizon_at_the_pole(self):
        sun = [float(r["sun_el_deg"]) for r in self.rows()]
        self.assertGreater(min(sun), -2.5)
        self.assertLess(max(sun), 2.5)

    def test_earth_wobbles_a_few_degrees(self):
        earth = [float(r["earth_el_deg"]) for r in self.rows()]
        self.assertTrue(-10 < min(earth) < -3)    # libration: roughly +/- 7 deg
        self.assertTrue(3 < max(earth) < 10)

    def test_earth_stays_in_one_part_of_the_sky(self):
        az = [float(r["earth_az_deg"]) for r in self.rows()]
        self.assertLess(max(az) - min(az), 40)    # Earth never circles the sky

    def test_sun_circles_all_the_way_round(self):
        az = [float(r["sun_az_deg"]) for r in self.rows()]
        self.assertLess(min(az), 10)
        self.assertGreater(max(az), 350)


if __name__ == "__main__":
    unittest.main()
