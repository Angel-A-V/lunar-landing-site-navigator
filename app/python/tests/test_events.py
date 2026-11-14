"""Tests for analysis/events.py: time to the next sunset / sunrise / Earthset / Earthrise.

Offline, no network.
Run (from app/python):  python3 -m unittest tests.test_events -v
"""
import math
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, PYDIR)

from analysis.events import annotate_events, next_event  # noqa: E402
from analysis.visibility import analyse, load_horizons, load_skyline  # noqa: E402

SKYLINE_CSV = os.path.join(ROOT, "data", "skyline_shackleton_rim.csv")
HORIZONS_CSV = os.path.join(ROOT, "data", "horizons_shackleton_rim_2026-11-10_30d_1h.csv")


def rows_from_margins(margins, body="sun"):
    """Tiny made-up rows: only the margin matters to next_event."""
    return [{f"{body}_margin_deg": m, f"{body}_visible": m > 0} for m in margins]


class MadeUpCases(unittest.TestCase):
    def test_visible_now_then_sets_halfway_between_samples(self):
        # margin +1 at hour 1, -1 at hour 2 -> crosses zero at hour 1.5
        rows = rows_from_margins([2.0, 1.0, -1.0, -2.0])
        e = next_event(rows, 0, "sun")
        self.assertEqual(e["state"], "visible")
        self.assertEqual(e["event"], "sunset")
        self.assertAlmostEqual(e["hours"], 1.5)

    def test_blocked_now_then_rises(self):
        rows = rows_from_margins([-1.0, -0.5, 0.5, 1.0])
        e = next_event(rows, 0, "sun")
        self.assertEqual(e["state"], "blocked")
        self.assertEqual(e["event"], "sunrise")
        self.assertAlmostEqual(e["hours"], 1.5)

    def test_earth_uses_earthset_and_earthrise_names(self):
        up = next_event(rows_from_margins([1.0, -1.0], "earth"), 0, "earth")
        down = next_event(rows_from_margins([-1.0, 1.0], "earth"), 0, "earth")
        self.assertEqual(up["event"], "earthset")
        self.assertEqual(down["event"], "earthrise")

    def test_no_change_in_the_data_returns_none_and_the_window_length(self):
        rows = rows_from_margins([1.0, 2.0, 3.0, 4.0, 5.0])
        e = next_event(rows, 1, "sun")
        self.assertIsNone(e["hours"])
        self.assertAlmostEqual(e["window_hours"], 3.0)  # 3 more hourly samples after index 1

    def test_step_hours_scales_the_answer(self):
        rows = rows_from_margins([2.0, 1.0, -1.0, -2.0])
        e = next_event(rows, 0, "sun", step_hours=6.0)
        self.assertAlmostEqual(e["hours"], 9.0)  # 1.5 steps * 6 h

    def test_start_in_the_middle(self):
        rows = rows_from_margins([5.0, 4.0, 3.0, 1.0, -1.0, -3.0])
        e = next_event(rows, 3, "sun")
        self.assertAlmostEqual(e["hours"], 0.5)

    def test_last_row_has_no_future_so_no_event(self):
        rows = rows_from_margins([1.0, 2.0])
        e = next_event(rows, 1, "sun")
        self.assertIsNone(e["hours"])
        self.assertAlmostEqual(e["window_hours"], 0.0)

    def test_index_out_of_range_raises(self):
        rows = rows_from_margins([1.0, 2.0])
        with self.assertRaises(ValueError):
            next_event(rows, 5, "sun")
        with self.assertRaises(ValueError):
            next_event(rows, -1, "sun")

    def test_margin_exactly_zero_counts_as_blocked(self):
        # visible means margin > 0, so 0.0 is blocked and the next positive margin is a rise
        rows = rows_from_margins([0.0, 1.0])
        e = next_event(rows, 0, "sun")
        self.assertEqual(e["state"], "blocked")
        self.assertEqual(e["event"], "sunrise")


class AnnotateEvents(unittest.TestCase):
    def test_adds_event_fields_for_sun_and_earth_to_every_row(self):
        rows = [
            {"sun_margin_deg": m, "sun_visible": m > 0, "earth_margin_deg": -m, "earth_visible": -m > 0}
            for m in (2.0, 1.0, -1.0, -2.0)
        ]
        out = annotate_events(rows, step_hours=1.0)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[0]["sun_event"], "sunset")
        self.assertAlmostEqual(out[0]["sun_event_hours"], 1.5)
        self.assertEqual(out[0]["earth_event"], "earthrise")
        self.assertAlmostEqual(out[0]["earth_event_hours"], 1.5)
        # last row: nothing after it
        self.assertIsNone(out[3]["sun_event_hours"])
        self.assertAlmostEqual(out[3]["sun_window_hours"], 0.0)

    def test_does_not_change_the_input_rows(self):
        rows = [{"sun_margin_deg": 1.0, "sun_visible": True, "earth_margin_deg": 1.0, "earth_visible": True}]
        annotate_events(rows)
        self.assertNotIn("sun_event", rows[0])


class RealData(unittest.TestCase):
    def setUp(self):
        sky = load_skyline(SKYLINE_CSV)
        self.rows = analyse(load_horizons(HORIZONS_CSV), sky)

    def _margin_at(self, rows, key, t_hours):
        """Straight-line margin at fractional hour t (hourly samples)."""
        i = math.floor(t_hours)
        frac = t_hours - i
        a = rows[i][f"{key}_margin_deg"]
        b = rows[i + 1][f"{key}_margin_deg"]
        return a + (b - a) * frac

    def test_sun_stays_visible_for_the_whole_30_days(self):
        e = next_event(self.rows, 0, "sun")
        self.assertEqual(e["state"], "visible")
        self.assertIsNone(e["hours"])
        self.assertAlmostEqual(e["window_hours"], 720.0)

    def test_earth_event_lands_where_the_margin_is_zero(self):
        e = next_event(self.rows, 0, "earth")
        self.assertIsNotNone(e["hours"])
        self.assertGreaterEqual(e["hours"], 0.0)
        self.assertAlmostEqual(self._margin_at(self.rows, "earth", e["hours"]), 0.0, places=6)

    def test_every_earth_event_in_the_file_is_consistent(self):
        # For every starting row that has an event, the margin at that time is ~0
        # and the state flips across it.
        for i in range(0, len(self.rows) - 1, 25):
            e = next_event(self.rows, i, "earth")
            if e["hours"] is None:
                continue
            t = i + e["hours"]
            self.assertAlmostEqual(self._margin_at(self.rows, "earth", t), 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
