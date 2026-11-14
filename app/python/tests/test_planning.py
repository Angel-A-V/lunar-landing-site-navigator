"""Tests for the planning functions in analysis/windows.py:
find_windows, best_mission_windows, month_starts, and the extra window_stats fields.

Offline, no network.
Run (from app/python):  python3 -m unittest tests.test_planning -v
"""
import os
import sys
import unittest

PYDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/python
ROOT = os.path.dirname(os.path.dirname(PYDIR))                       # repo root (shared data/ lives here)
sys.path.insert(0, PYDIR)

from analysis.visibility import analyse, load_horizons, load_skyline  # noqa: E402
from analysis.windows import best_mission_windows, find_windows, month_starts, window_stats  # noqa: E402


def make_rows(sun, earth):
    """Made-up rows from two lists of True/False, with simple time labels t0, t1, ..."""
    return [
        {"time_utc": f"t{i}", "sun_visible": s, "earth_visible": e, "both_visible": s and e}
        for i, (s, e) in enumerate(zip(sun, earth))
    ]


T, F = True, False


class FindWindows(unittest.TestCase):
    def setUp(self):
        self.rows = make_rows([T, T, F, T, F, F, T, T, T], [F] * 9)
        self.found = find_windows(self.rows, "sun_visible", True, step_hours=6.0)

    def test_finds_each_stretch(self):
        self.assertEqual([(w["start_index"], w["end_index"]) for w in self.found], [(0, 1), (3, 3), (6, 8)])

    def test_durations_in_hours(self):
        self.assertEqual([w["duration_hours"] for w in self.found], [12.0, 6.0, 18.0])

    def test_start_and_end_times(self):
        first = self.found[0]
        self.assertEqual(first["start_time_utc"], "t0")
        self.assertEqual(first["end_time_utc"], "t2")  # the first sample after the stretch

    def test_stretches_touching_the_edges_of_the_data_are_flagged(self):
        self.assertTrue(self.found[0]["open_start"])
        self.assertFalse(self.found[0]["open_end"])
        self.assertFalse(self.found[1]["open_start"])
        self.assertFalse(self.found[1]["open_end"])
        self.assertTrue(self.found[2]["open_end"])
        self.assertEqual(self.found[2]["end_time_utc"], "t8")  # no sample after: last sample of the data

    def test_blocked_stretches(self):
        dark = find_windows(self.rows, "sun_visible", False, 6.0)
        self.assertEqual([(w["start_index"], w["end_index"]) for w in dark], [(2, 2), (4, 5)])

    def test_never_happens_and_empty(self):
        self.assertEqual(find_windows(make_rows([T, T], [F, F]), "sun_visible", False, 6.0), [])
        self.assertEqual(find_windows([], "sun_visible", True, 6.0), [])


class ExtraStats(unittest.TestCase):
    def setUp(self):
        sun = [T, T, F, F, F, T]
        earth = [F, T, T, F, F, F]
        self.stats = window_stats(make_rows(sun, earth), step_hours=6.0)

    def test_days_visible(self):
        self.assertAlmostEqual(self.stats["sun_visible_days"], 3 * 6.0 / 24)    # 3 samples
        self.assertAlmostEqual(self.stats["earth_visible_days"], 2 * 6.0 / 24)
        self.assertAlmostEqual(self.stats["both_visible_days"], 1 * 6.0 / 24)

    def test_window_counts(self):
        self.assertEqual(self.stats["sun_window_count"], 2)    # samples 0-1 and 5
        self.assertEqual(self.stats["earth_window_count"], 1)
        self.assertEqual(self.stats["both_window_count"], 1)

    def test_longest_stretch_with_both_visible(self):
        rows = make_rows([T, T, T, F, T, T], [T, T, F, F, T, T])
        s = window_stats(rows, 6.0)
        self.assertEqual(s["longest_both_visible_hours"], 12.0)  # samples 0-1 and 4-5, 2 samples each
        self.assertEqual(window_stats([], 6.0)["longest_both_visible_hours"], 0.0)

    def test_empty_rows_have_the_new_fields_too(self):
        s = window_stats([], 6.0)
        self.assertEqual(s["sun_window_count"], 0)
        self.assertEqual(s["sun_visible_days"], 0.0)


class BestMissionWindows(unittest.TestCase):
    def setUp(self):
        #            0  1  2  3  4  5  6  7  8  9
        sun = [F, F, T, T, T, F, F, T, T, F]
        earth = [F, F, T, T, T, F, F, F, T, T]
        self.rows = make_rows(sun, earth)
        # 0.75 day at 6 h steps = 3 samples per mission
        self.best = best_mission_windows(self.rows, mission_days=0.75, step_hours=6.0, top_n=2)

    def test_best_start_is_the_fully_covered_window(self):
        first = self.best[0]
        self.assertEqual(first["rank"], 1)
        self.assertEqual(first["start_index"], 2)
        self.assertAlmostEqual(first["both_pct"], 100.0)
        self.assertAlmostEqual(first["sun_pct"], 100.0)
        self.assertAlmostEqual(first["earth_pct"], 100.0)
        self.assertEqual(first["longest_sun_dark_hours"], 0.0)

    def test_second_pick_does_not_overlap_the_first_and_ties_break_on_earth(self):
        # After the first window (2..4), start 7 and start 6 both have 33% both-visible and 67% Sun;
        # start 7 sees Earth 67% of the time versus 33%, so it ranks higher.
        self.assertEqual([w["start_index"] for w in self.best], [2, 7])
        self.assertEqual(self.best[1]["rank"], 2)

    def test_no_two_picks_overlap(self):
        many = best_mission_windows(self.rows, 0.75, 6.0, top_n=10)
        starts = sorted(w["start_index"] for w in many)
        for a, b in zip(starts, starts[1:]):
            self.assertGreaterEqual(b - a, 3)

    def test_start_and_end_times(self):
        first = self.best[0]
        self.assertEqual(first["start_time_utc"], "t2")
        self.assertEqual(first["end_time_utc"], "t5")  # the sample after the 3-sample mission

    def test_mission_longer_than_the_data_gives_nothing(self):
        self.assertEqual(best_mission_windows(self.rows, mission_days=30, step_hours=6.0), [])

    def test_mission_length_must_be_positive(self):
        with self.assertRaises(ValueError):
            best_mission_windows(self.rows, mission_days=0, step_hours=6.0)

    def test_records_the_mission_length(self):
        self.assertEqual(self.best[0]["mission_days"], 0.75)


class MonthStarts(unittest.TestCase):
    def test_marks_the_first_sample_of_each_month(self):
        rows = [{"time_utc": t} for t in
                ["2026-Nov-29 00:00", "2026-Nov-30 18:00", "2026-Dec-01 00:00", "2026-Dec-15 06:00", "2027-Jan-01 00:00"]]
        self.assertEqual(month_starts(rows), [
            {"index": 0, "label": "Nov 2026"},
            {"index": 2, "label": "Dec 2026"},
            {"index": 4, "label": "Jan 2027"},
        ])

    def test_empty(self):
        self.assertEqual(month_starts([]), [])


class RealYear(unittest.TestCase):
    def _rows(self, site):
        sky = load_skyline(os.path.join(ROOT, "data", f"skyline_{site}.csv"))
        path = os.path.join(ROOT, "data", f"horizons_{site}_2026-11-10_365d_6h.csv")
        return analyse(load_horizons(path), sky)

    def test_best_14_day_start_beats_the_yearly_average(self):
        rows = self._rows("shackleton_rim")
        year = window_stats(rows, 6.0)
        best = best_mission_windows(rows, 14, 6.0, top_n=3)
        self.assertEqual(len(best), 3)
        self.assertGreater(best[0]["both_pct"], year["both_visible_pct"])
        self.assertGreaterEqual(best[0]["both_pct"], best[1]["both_pct"])
        self.assertGreaterEqual(best[1]["both_pct"], best[2]["both_pct"])

    def test_picks_are_non_overlapping_on_real_data(self):
        best = best_mission_windows(self._rows("mons_mouton"), 14, 6.0, top_n=5)
        starts = sorted(w["start_index"] for w in best)
        for a, b in zip(starts, starts[1:]):
            self.assertGreaterEqual(b - a, 14 * 4)  # 14 days * 4 samples per day

    def test_crater_floor_has_no_lit_windows_and_every_start_is_zero(self):
        rows = self._rows("shackleton")
        self.assertEqual(find_windows(rows, "sun_visible", True, 6.0), [])
        best = best_mission_windows(rows, 7, 6.0, top_n=3)
        self.assertTrue(all(w["both_pct"] == 0.0 for w in best))

    def test_window_durations_add_up_to_the_yearly_visible_time(self):
        rows = self._rows("shackleton_rim")
        year = window_stats(rows, 6.0)
        total_hours = sum(w["duration_hours"] for w in find_windows(rows, "sun_visible", True, 6.0))
        self.assertAlmostEqual(total_hours / 24, year["sun_visible_days"], places=6)


if __name__ == "__main__":
    unittest.main()
