"""Tests for scripts/export_site_json.py: the files the web page reads.

Offline, no network.
Run (from app/python):  python3 -m unittest tests.test_export -v
"""
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
sys.path.insert(0, PYDIR)
sys.path.insert(0, os.path.join(PYDIR, "scripts"))

from export_site_json import build_site_payload, build_sites_index  # noqa: E402
from sites import SITES  # noqa: E402


class SitePayload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ridge = build_site_payload("mons_mouton")
        cls.floor = build_site_payload("shackleton")

    def test_top_level_keys(self):
        for key in ("site", "label", "description", "lat_deg", "lon_deg_east",
                    "sources", "summary", "year", "skyline_deg", "rows"):
            self.assertIn(key, self.ridge)

    def test_identity(self):
        self.assertEqual(self.ridge["site"], "mons_mouton")
        self.assertEqual(self.ridge["label"], "Mons Mouton")
        self.assertEqual(self.ridge["lat_deg"], SITES["mons_mouton"][0])
        self.assertEqual(self.ridge["lon_deg_east"], SITES["mons_mouton"][1])

    def test_sizes(self):
        self.assertEqual(len(self.ridge["rows"]), 721)      # 30 days, hourly
        self.assertEqual(len(self.ridge["skyline_deg"]), 360)
        self.assertEqual(self.ridge["year"]["samples"], 1461)  # 365 days, 6-hourly

    def test_rows_carry_the_analysis_and_the_events(self):
        row = self.ridge["rows"][0]
        for key in ("time_utc", "sun_az_deg", "sun_el_deg", "sun_skyline_deg", "sun_margin_deg",
                    "sun_visible", "earth_visible", "sun_event", "sun_event_hours",
                    "earth_event", "earth_event_hours", "earth_window_hours"):
            self.assertIn(key, row)

    def test_sources_name_all_three_files(self):
        self.assertEqual(set(self.ridge["sources"]), {"horizons_30d", "horizons_year", "skyline"})

    def test_crater_floor_is_never_lit(self):
        self.assertEqual(self.floor["summary"]["sun_visible_pct"], 0.0)
        self.assertEqual(self.floor["year"]["sun_visible_pct"], 0.0)
        self.assertIsNone(self.floor["rows"][0]["sun_event_hours"])  # no sunrise in the data

    def test_says_where_the_coordinate_and_the_terrain_came_from(self):
        self.assertIn("Moon Trek", self.ridge["coordinate_source"])
        terrain = self.ridge["terrain"]
        self.assertEqual(terrain["near_map"], "80S_40M")          # 157 km from the pole: the 40 m map
        self.assertEqual(self.floor["terrain"]["near_map"], "85S_20M")  # 11 km from the pole: the 20 m map
        self.assertTrue(terrain["far_range_limited_by_map_edge"])
        self.assertAlmostEqual(self.ridge["pole_distance_km"], 157.5, delta=0.5)

    def test_model_site_uses_the_extended_skyline_not_the_wall_file(self):
        rim = build_site_payload("shackleton_rim")
        self.assertEqual(rim["sources"]["skyline"], "skyline_shackleton_rim_extended.csv")
        self.assertEqual(rim["terrain"]["far_range_km"], 250.0)
        self.assertTrue(rim["is_model_site"])
        self.assertFalse(self.ridge["is_model_site"])

    def test_floats_are_rounded_for_a_small_file(self):
        value = self.ridge["rows"][0]["sun_el_deg"]
        self.assertEqual(value, round(value, 4))


class PlanPayload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rim = build_site_payload("shackleton_rim")
        cls.floor = build_site_payload("shackleton")

    def test_plan_has_the_pieces_the_page_draws(self):
        plan = self.rim["plan"]
        for key in ("year_start_utc", "samples", "step_hours", "months", "windows", "best_starts"):
            self.assertIn(key, plan)
        self.assertEqual(plan["samples"], 1461)
        self.assertEqual(plan["step_hours"], 6.0)
        self.assertEqual(plan["year_start_utc"], "2026-Nov-10 00:00")

    def test_month_labels_cover_the_year(self):
        months = self.rim["plan"]["months"]
        self.assertEqual(months[0], {"index": 0, "label": "Nov 2026"})
        self.assertEqual(len(months), 13)  # Nov 2026 .. Nov 2027

    def test_windows_for_sun_earth_and_both(self):
        w = self.rim["plan"]["windows"]
        self.assertEqual(set(w), {"sun", "earth", "both"})
        self.assertGreater(len(w["sun"]), 0)
        self.assertEqual(len(w["sun"]), self.rim["year"]["sun_window_count"])
        for key in ("start_index", "end_index", "start_time_utc", "end_time_utc", "duration_hours"):
            self.assertIn(key, w["sun"][0])

    def test_best_starts_for_each_mission_length(self):
        best = self.rim["plan"]["best_starts"]
        self.assertEqual(set(best), {"7", "14", "30"})
        for days, picks in best.items():
            self.assertEqual([p["rank"] for p in picks], [1, 2, 3, 4, 5])
            self.assertEqual(picks[0]["mission_days"], int(days))
            self.assertGreaterEqual(picks[0]["both_pct"], picks[1]["both_pct"])

    def test_year_stats_include_days_and_window_counts(self):
        for key in ("sun_visible_days", "earth_visible_days", "both_visible_days",
                    "sun_window_count", "earth_window_count", "both_window_count"):
            self.assertIn(key, self.rim["year"])

    def test_crater_floor_has_no_lit_windows(self):
        self.assertEqual(self.floor["plan"]["windows"]["sun"], [])
        self.assertEqual(self.floor["plan"]["windows"]["both"], [])
        self.assertEqual(self.floor["year"]["sun_window_count"], 0)


class SitesIndex(unittest.TestCase):
    def test_lists_every_site_with_its_year_stats(self):
        index = build_sites_index()
        self.assertEqual([s["id"] for s in index], list(SITES))
        for entry in index:
            for key in ("id", "label", "description", "lat_deg", "lon_deg_east", "year"):
                self.assertIn(key, entry)
            self.assertIn("longest_sun_dark_hours", entry["year"])
            for key in ("pole_distance_km", "site_height_m", "coordinate_source", "is_model_site"):
                self.assertIn(key, entry)

    def test_has_the_model_site_and_the_seven_named_features(self):
        ids = [s["id"] for s in build_sites_index()]
        self.assertEqual(len(ids), 8)
        for name in ("shackleton", "de_gerlache", "haworth", "nobile", "mons_mouton", "malapert", "cabeus"):
            self.assertIn(name, ids)

    def test_first_site_is_the_model_site(self):
        self.assertEqual(build_sites_index()[0]["id"], "shackleton_rim")


if __name__ == "__main__":
    unittest.main()
