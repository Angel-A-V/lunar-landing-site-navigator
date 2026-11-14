"""Tests for scripts/fetch_trek_sites.py: named lunar features from NASA Moon Trek.

Offline: uses canned replies shaped like the real Moon Trek search service.
Run (from app/python):  python3 -m unittest tests.test_trek_sites -v
"""
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
sys.path.insert(0, os.path.join(PYDIR, "scripts"))

from fetch_trek_sites import pick_feature, pole_distance_km, slug  # noqa: E402

# Real reply shape (2026-11-14): bbox is "west,south,east,north" = "lon,lat,lon,lat".
MALAPERT_DOCS = [
    {"title": "Malapert A", "itemType": "nomenclature", "bbox": "-3.46315,-80.194918,-3.46315,-80.194918"},
    {"title": "Malapert", "itemType": "nomenclature", "bbox": "12.305737,-84.798043,12.305737,-84.798043"},
    {"title": "Malapert B", "itemType": "nomenclature", "bbox": "-2.925273,-78.782084,-2.925273,-78.782084"},
]


class PickFeature(unittest.TestCase):
    def test_takes_the_exact_name_not_a_longer_one(self):
        lat, lon = pick_feature(MALAPERT_DOCS, "Malapert")
        self.assertAlmostEqual(lat, -84.798043)
        self.assertAlmostEqual(lon, 12.305737)

    def test_negative_longitude_becomes_east_longitude(self):
        lat, lon = pick_feature(MALAPERT_DOCS, "Malapert A")
        self.assertAlmostEqual(lat, -80.194918)
        self.assertAlmostEqual(lon, 360 - 3.46315)

    def test_name_match_ignores_case(self):
        self.assertEqual(pick_feature(MALAPERT_DOCS, "malapert"), pick_feature(MALAPERT_DOCS, "Malapert"))

    def test_missing_name_is_an_error(self):
        with self.assertRaises(LookupError):
            pick_feature(MALAPERT_DOCS, "Shackleton")

    def test_only_named_features_count(self):
        docs = [{"title": "Shackleton", "itemType": "product", "bbox": "0,0,1,1"}]
        with self.assertRaises(LookupError):
            pick_feature(docs, "Shackleton")

    def test_an_area_uses_its_centre(self):
        docs = [{"title": "Somewhere", "itemType": "nomenclature", "bbox": "10,-86,20,-84"}]
        self.assertEqual(pick_feature(docs, "Somewhere"), (-85.0, 15.0))


class Helpers(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slug("Mons Mouton"), "mons_mouton")
        self.assertEqual(slug("de Gerlache"), "de_gerlache")
        self.assertEqual(slug("Malapert A"), "malapert_a")

    def test_pole_distance(self):
        self.assertAlmostEqual(pole_distance_km(-90.0), 0.0)
        self.assertAlmostEqual(pole_distance_km(-80.0), 304.0, delta=0.1)  # the edge of the 80S map
        self.assertAlmostEqual(pole_distance_km(-89.781), 6.6, delta=0.1)  # the model site


if __name__ == "__main__":
    unittest.main()
