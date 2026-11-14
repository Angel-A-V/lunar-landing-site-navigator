"""Tests for the second terrain map in scripts/make_skyline.py (the Grid support).

Part 1 uses made-up terrain with known answers. Part 2 cross-checks the real 80S 40 m map
against the skyline already built from the 85S 20 m map, and is skipped until
data/raw/LDEM_80S_40M.IMG has been downloaded.

Run (from app/python):  python3 -m unittest tests.test_skyline_grid -v     (needs numpy)
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

SIZE = 1000
SITE = (-89.9, 90.0)   # about 3 km from the pole; at lon 90E, map +x is north
FAKE = M.Grid("fake", n=SIZE, px_m=40.0, center=SIZE / 2, scale=0.5)  # 40 km square, DN * 0.5 = metres


class GridGeometry(unittest.TestCase):
    def test_pole_is_at_the_centre(self):
        row, col = M.to_pixel(-90.0, 0.0, FAKE)
        self.assertAlmostEqual(row, SIZE / 2)
        self.assertAlmostEqual(col, SIZE / 2)

    def test_pixel_size_is_respected(self):
        # 0.1 degree from the pole is about 3.03 km; at 40 m per pixel that is about 75.8 pixels.
        row, col = M.to_pixel(-89.9, 90.0, FAKE)
        expected_px = 2 * M.R * math.tan(math.radians(0.1) / 2) / 40.0
        self.assertAlmostEqual(col - SIZE / 2, expected_px, places=6)  # lon 90E is map +x
        self.assertAlmostEqual(row, SIZE / 2, places=6)

    def test_real_map_descriptions(self):
        self.assertEqual(M.GRIDS["80S_40M"].n, 15200)
        self.assertEqual(M.GRIDS["80S_40M"].px_m, 40.0)
        self.assertEqual(M.GRIDS["80S_40M"].center, 7599.5)
        self.assertEqual(M.GRIDS["80S_40M"].scale, 0.5)

    def test_map_reach(self):
        # Half the map width, in km: 15200 / 2 * 40 m = 304 km (80 degrees south).
        self.assertAlmostEqual(M.GRIDS["80S_40M"].half_width_km, 304.0, places=1)


class NearAndFar(unittest.TestCase):
    def test_combine_keeps_the_higher_of_the_two_in_each_direction(self):
        near = [(0.0, 1.0), (1.0, -2.0), (2.0, 0.5)]
        far = [(0.0, 0.2), (1.0, -1.0), (2.0, 0.5)]
        self.assertEqual(M.combine(near, far), [(0.0, 1.0), (1.0, -1.0), (2.0, 0.5)])

    def test_combine_needs_matching_directions(self):
        with self.assertRaises(ValueError):
            M.combine([(0.0, 1.0)], [(1.0, 1.0)])

    def test_far_reach_is_capped_near_the_pole_and_limited_by_the_map_edge_further_out(self):
        self.assertEqual(M.far_reach_km(-90.0), 250.0)                 # capped
        self.assertAlmostEqual(M.far_reach_km(-84.798), 304.0 - 157.8 - 1, delta=0.5)  # Malapert: map edge


class GridSkyline(unittest.TestCase):
    def setUp(self):
        self.col_x = (np.arange(SIZE) - FAKE.center) * FAKE.px_m  # metres along map +x

    def test_flat_plain_is_flat(self):
        prof, h_site = M.skyline(np.zeros((SIZE, SIZE), dtype="<i2"), *SITE, max_km=5.0, grid=FAKE)
        self.assertLess(max(abs(v) for _, v in prof), 0.01)
        self.assertEqual(h_site, 0.0)

    def test_scale_factor_turns_stored_numbers_into_metres(self):
        # Stored numbers rise 0.1 per metre; with scale 0.5 the real slope is 0.05 (about 2.86 deg).
        dn = np.tile(0.1 * self.col_x, (SIZE, 1))
        prof = dict(M.skyline(dn, *SITE, max_km=5.0, grid=FAKE)[0])
        expect = math.degrees(math.atan(0.05))
        self.assertAlmostEqual(prof[0.0], expect, delta=0.1)     # uphill: north
        self.assertAlmostEqual(prof[180.0], -expect, delta=0.1)  # downhill: south

    def test_min_m_skips_terrain_closer_than_that(self):
        # A 100 m bump 400 to 600 m north of the site. Seen by default; ignored when starting at 1 km.
        dn = np.zeros((SIZE, SIZE))
        site_x = 2 * M.R * math.tan(math.radians(0.1) / 2)
        dn[:, (self.col_x > site_x + 400) & (self.col_x < site_x + 600)] = 200.0   # * 0.5 = 100 m
        seen = dict(M.skyline(dn, *SITE, max_km=5.0, grid=FAKE)[0])
        skipped = dict(M.skyline(dn, *SITE, max_km=5.0, min_m=1000.0, grid=FAKE)[0])
        self.assertGreater(seen[0.0], 5.0)
        self.assertLess(skipped[0.0], 0.01)

    def test_ray_that_leaves_the_map_is_an_error_not_a_wrong_answer(self):
        # The fake map is 20 km from centre to edge; a 30 km ray must not silently wrap around.
        with self.assertRaises(ValueError):
            M.skyline(np.zeros((SIZE, SIZE), dtype="<i2"), *SITE, max_km=30.0, grid=FAKE)

    def test_site_outside_the_map_is_an_error(self):
        with self.assertRaises(ValueError):
            M.skyline(np.zeros((SIZE, SIZE), dtype="<i2"), -80.0, 0.0, max_km=1.0, grid=FAKE)


REAL = os.path.join(ROOT, "data", "raw", "LDEM_80S_40M.IMG")


@unittest.skipUnless(os.path.exists(REAL) and os.path.getsize(REAL) == 15200 * 15200 * 2,
                     "80S 40 m terrain map not downloaded yet")
class RealMapCrossCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = M.load_grid("80S_40M")

    def test_shackleton_floor_is_deep_and_rim_is_high(self):
        g = M.GRIDS["80S_40M"]
        r, c = M.to_pixel(-89.654, 128.31, g)
        self.assertLess(M.sample(self.h, np.array(r), np.array(c)) * g.scale, -2000)
        r, c = M.to_pixel(-89.781, 203.743, g)
        self.assertGreater(M.sample(self.h, np.array(r), np.array(c)) * g.scale, 1500)

    def test_extended_rim_skyline_only_ever_raises_the_35_km_one(self):
        # Looking further out can only add terrain, never remove it. Measured 2026-11-14: mountains
        # 35 to 200 km away raise the model site's skyline in dozens of directions, by up to ~1.5 deg.
        saved = np.loadtxt(os.path.join(ROOT, "data", "skyline_shackleton_rim.csv"), delimiter=",", skiprows=1)[:, 1]
        prof, h_site, info = M.site_skyline("85S_20M", -89.781, 203.743)
        extended = np.array([v for _, v in prof])
        self.assertTrue((extended >= saved - 0.002).all())
        raised = (extended - saved) > 0.01
        self.assertGreater(raised.sum(), 50)
        self.assertLess((extended - saved).max(), 2.0)
        self.assertEqual(info["far_range_km"], 250.0)
        self.assertGreater(h_site, 1700)

    def test_far_terrain_agrees_with_the_20_m_map(self):
        # Same site, same 35 km reach, two different NASA products (20 m and 40 m per pixel).
        # Terrain beyond 2 km must agree closely: this checks the new map's projection, scale and
        # orientation. (Closer than a few hundred metres the 40 m map is too coarse to agree at a
        # sharp summit like this one: measured 0.58 deg mean difference on 2026-11-14. That is why
        # each site uses the finest map that covers it; see SITE_GRID in sites.py.)
        band = np.fromfile(M.RAW, dtype="<i2").reshape(M.BAND_ROWS, M.N) * 0.5
        fine, _ = M.skyline(band, -89.781, 203.743, max_km=35.0, min_m=2000.0)
        coarse, _ = M.skyline(self.h, -89.781, 203.743, max_km=35.0, min_m=2000.0, grid=M.GRIDS["80S_40M"])
        diff = np.abs(np.array([v for _, v in fine]) - np.array([v for _, v in coarse]))
        self.assertLess(diff.mean(), 0.02)
        self.assertLess(diff.max(), 0.1)


if __name__ == "__main__":
    unittest.main()
