"""Self-test for scripts/make_skyline.py.

Part 1 uses made-up terrain with a known answer (catches math mistakes).
Part 2 checks the real downloaded data (catches data/orientation mistakes) and
is skipped if data/raw/band_85S_20M.bin has not been downloaded yet.

Run:  python3 -m unittest tests.test_skyline -v     (needs numpy)
"""
import math
import os
import sys
import unittest

import numpy as np

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, os.path.join(PYDIR, "scripts"))
import make_skyline as M  # noqa: E402

SIZE = 1000          # small fake map: 1000 x 1000 pixels of 20 m = 20 km square
SITE = (-89.9, 90.0)  # about 3 km from the pole; at lon 90E, map +x is north
SLOPE = 0.05         # rise over run for the ramp test


class FakeTerrain(unittest.TestCase):
    """Terrain we can reason about by hand. The pole sits at the map centre."""

    def setUp(self):
        self._saved = (M.CENTER, M.ROW0)
        M.CENTER, M.ROW0 = SIZE / 2, 0
        self.col_x = (np.arange(SIZE) - M.CENTER) * M.PX_M   # metres east in the map
        self.site_x = self.col_x[0] * 0 + 2 * M.R * math.tan(math.radians(0.1) / 2)

    def tearDown(self):
        M.CENTER, M.ROW0 = self._saved

    def run_skyline(self, h, max_km=5.0):
        prof, h_site = M.skyline(h, *SITE, step_deg=1.0, max_km=max_km)
        return dict(prof), h_site

    def test_flat_plain_is_flat(self):
        # Flat ground: the skyline should be ~0 (only a tiny curvature dip).
        prof, _ = self.run_skyline(np.zeros((SIZE, SIZE)))
        self.assertLess(max(abs(v) for v in prof.values()), 0.01)

    def test_ramp_up_north_down_south(self):
        # Ground rises 5 m per 100 m toward map +x, which is north at this site.
        h = np.tile(SLOPE * self.col_x, (SIZE, 1))
        prof, _ = self.run_skyline(h)
        expect = math.degrees(math.atan(SLOPE))                  # about 2.86 deg
        self.assertAlmostEqual(prof[0.0], expect, delta=0.1)     # uphill: north
        self.assertAlmostEqual(prof[180.0], -expect, delta=0.1)  # downhill: south
        self.assertAlmostEqual(prof[90.0], 0.0, delta=0.3)       # sideways: ~level

    def test_wall_2km_north(self):
        # A 200 m wall starting 2 km north of the site: angle ~ atan(200/2000) = 5.7 deg.
        h = np.zeros((SIZE, SIZE))
        h[:, self.col_x > self.site_x + 2000] = 200.0
        prof, _ = self.run_skyline(h)
        expect = math.degrees(math.atan(200 / 2000))
        self.assertAlmostEqual(prof[0.0], expect, delta=0.2)
        self.assertLess(prof[180.0], 0.01)   # nothing blocks the south

    def test_curvature_hides_low_distant_hill(self):
        # The Moon curves away by d^2 / 2R: 10.4 m at 6 km. A hill there that is
        # lower than that is hidden; a hill higher than that shows above the horizon.
        for height, visible in [(8.0, False), (15.0, True)]:
            h = np.zeros((SIZE, SIZE))
            near = self.site_x + 6000
            h[:, (self.col_x > near) & (self.col_x < near + 200)] = height
            prof, _ = self.run_skyline(h, max_km=6.5)
            north = prof[0.0]
            if visible:
                self.assertGreater(north, 0.02)   # about +0.044 deg expected
            else:
                self.assertLess(north, 0.001)     # same as bare flat ground

    def test_pole_pixel_and_north_direction(self):
        row, col = M.to_pixel(-90.0, 0.0)
        self.assertAlmostEqual(row, M.CENTER - M.ROW0)
        self.assertAlmostEqual(col, M.CENTER)
        la, _ = M.destination(*SITE, 0.0, 10_000.0)
        self.assertGreater(la, SITE[0])   # bearing 0 = north = away from the south pole

    def test_distance_of_one_degree(self):
        la, _ = M.destination(0.0, 0.0, 0.0, M.R * math.pi / 180)
        self.assertAlmostEqual(la, 1.0, places=6)


@unittest.skipUnless(os.path.exists(M.RAW), "real terrain band not downloaded yet")
class RealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = np.fromfile(M.RAW, dtype="<i2").reshape(M.BAND_ROWS, M.N) * 0.5

    def test_shackleton_floor_is_deep(self):
        # Crater floor centre found earlier at about -89.654, 128.31: should be ~ -2.5 km or lower.
        r, c = M.to_pixel(-89.654, 128.31)
        self.assertLess(M.sample(self.h, np.array(r), np.array(c)), -2000)

    def test_site_is_on_high_ground(self):
        r, c = M.to_pixel(*M.SITES["shackleton_rim"])
        self.assertGreater(M.sample(self.h, np.array(r), np.array(c)), 1500)

    def test_skyline_matches_saved_csv(self):
        path = os.path.join(ROOT, "data", "skyline_shackleton_rim.csv")
        if not os.path.exists(path):
            self.skipTest("no CSV yet")
        prof, _ = M.skyline(self.h, *M.SITES["shackleton_rim"])
        saved = np.loadtxt(path, delimiter=",", skiprows=1)
        self.assertEqual(len(saved), len(prof))
        self.assertLess(np.abs(saved[:, 1] - np.array([v for _, v in prof])).max(), 0.002)


if __name__ == "__main__":
    unittest.main()
