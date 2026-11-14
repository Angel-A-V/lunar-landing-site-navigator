"""Yearly statistics for a site: how often, and the longest stretches.

Pure functions, no web or hardware code. Works on the rows that
analysis.visibility.analyse() produces.

A "stretch" (run) is a series of consecutive samples with the same visible/blocked state.
Its length is counted in whole samples times the step, so it is only as exact as the step
(6 hours for the yearly file).
"""


def longest_run(rows, key, value, step_hours):
    """Hours in the longest stretch where row[key] == value (0.0 if it never happens)."""
    best = 0
    current = 0
    for row in rows:
        if row[key] == value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best * step_hours


def _run_bounds(rows, key, value):
    """(first_index, last_index) of every stretch where row[key] == value."""
    bounds = []
    n = len(rows)
    i = 0
    while i < n:
        if rows[i][key] == value:
            j = i
            while j + 1 < n and rows[j + 1][key] == value:
                j += 1
            bounds.append((i, j))
            i = j + 1
        else:
            i += 1
    return bounds


def find_windows(rows, key, value, step_hours):
    """Every stretch where row[key] == value, as a list of dicts.

    Each dict: start_index, end_index (first and last sample in the stretch), start_time_utc,
    end_time_utc (the first sample AFTER the stretch, or the last sample of the data if the
    stretch runs to the end), duration_hours, open_start / open_end (the stretch touches the
    edge of the data, so its true start or end is not known).
    """
    n = len(rows)
    windows = []
    for i, j in _run_bounds(rows, key, value):
        open_end = j == n - 1
        windows.append({
            "start_index": i,
            "end_index": j,
            "start_time_utc": rows[i]["time_utc"],
            "end_time_utc": rows[-1]["time_utc"] if open_end else rows[j + 1]["time_utc"],
            "duration_hours": (j - i + 1) * step_hours,
            "open_start": i == 0,
            "open_end": open_end,
        })
    return windows


def best_mission_windows(rows, mission_days, step_hours, top_n=5):
    """The best start times for a mission of `mission_days` days, best first.

    Every possible start is scored by the share of the mission with BOTH the Sun and Earth
    visible (power and a direct line to Earth). Ties go to more Sun, then more Earth, then the
    earlier start. Picks never overlap: a start closer than one mission length to a better pick
    is skipped. Returns [] if the mission is longer than the data.
    """
    if mission_days <= 0:
        raise ValueError("mission_days must be positive")
    n = len(rows)
    length = max(1, round(mission_days * 24 / step_hours))
    if length > n:
        return []

    scored = []
    for i in range(n - length + 1):
        seg = rows[i:i + length]
        scored.append({
            "start_index": i,
            "start_time_utc": rows[i]["time_utc"],
            "end_time_utc": rows[i + length]["time_utc"] if i + length < n else rows[-1]["time_utc"],
            "mission_days": mission_days,
            "sun_pct": 100 * sum(r["sun_visible"] for r in seg) / length,
            "earth_pct": 100 * sum(r["earth_visible"] for r in seg) / length,
            "both_pct": 100 * sum(r["both_visible"] for r in seg) / length,
            "longest_sun_dark_hours": longest_run(seg, "sun_visible", False, step_hours),
            "longest_earth_blocked_hours": longest_run(seg, "earth_visible", False, step_hours),
        })
    scored.sort(key=lambda w: (-w["both_pct"], -w["sun_pct"], -w["earth_pct"], w["start_index"]))

    picked = []
    for w in scored:
        if all(abs(w["start_index"] - p["start_index"]) >= length for p in picked):
            picked.append(w)
        if len(picked) == top_n:
            break
    for rank, w in enumerate(picked, start=1):
        w["rank"] = rank
    return picked


def month_starts(rows):
    """The first sample of each calendar month, for labelling a timeline: [{index, label}]."""
    ticks = []
    seen = None
    for i, r in enumerate(rows):
        key = r["time_utc"][:8]  # "2026-Nov"
        if key != seen:
            ticks.append({"index": i, "label": f"{key[5:8]} {key[:4]}"})
            seen = key
    return ticks


def window_stats(rows, step_hours):
    """Percent of time visible plus the longest lit/dark and in-contact/blocked stretches."""
    n = len(rows)
    if n == 0:
        return {
            "samples": 0, "span_days": 0.0,
            "sun_visible_pct": 0.0, "earth_visible_pct": 0.0, "both_visible_pct": 0.0,
            "longest_sun_dark_hours": 0.0, "longest_sun_lit_hours": 0.0,
            "longest_earth_blocked_hours": 0.0, "longest_earth_visible_hours": 0.0,
            "sun_visible_days": 0.0, "earth_visible_days": 0.0, "both_visible_days": 0.0,
            "sun_window_count": 0, "earth_window_count": 0, "both_window_count": 0,
            "longest_both_visible_hours": 0.0,
        }
    return {
        "samples": n,
        "span_days": n * step_hours / 24,
        "sun_visible_pct": 100 * sum(r["sun_visible"] for r in rows) / n,
        "earth_visible_pct": 100 * sum(r["earth_visible"] for r in rows) / n,
        "both_visible_pct": 100 * sum(r["both_visible"] for r in rows) / n,
        "longest_sun_dark_hours": longest_run(rows, "sun_visible", False, step_hours),
        "longest_sun_lit_hours": longest_run(rows, "sun_visible", True, step_hours),
        "longest_earth_blocked_hours": longest_run(rows, "earth_visible", False, step_hours),
        "longest_earth_visible_hours": longest_run(rows, "earth_visible", True, step_hours),
        "sun_visible_days": sum(r["sun_visible"] for r in rows) * step_hours / 24,
        "earth_visible_days": sum(r["earth_visible"] for r in rows) * step_hours / 24,
        "both_visible_days": sum(r["both_visible"] for r in rows) * step_hours / 24,
        "sun_window_count": len(_run_bounds(rows, "sun_visible", True)),
        "earth_window_count": len(_run_bounds(rows, "earth_visible", True)),
        "both_window_count": len(_run_bounds(rows, "both_visible", True)),
        "longest_both_visible_hours": longest_run(rows, "both_visible", True, step_hours),
    }
