"""Is the Sun (or Earth) above the real terrain skyline?

Pure functions: data in, numbers out. No web server and no hardware code in here.
This is Steps 2 and 3 of docs/software-architecture.md.

Words used here:
  azimuth      compass direction, 0 = north, 90 = east, clockwise, in degrees
  elevation    angle above a flat horizon, in degrees (negative = below it)
  skyline      for each direction, the angle of the highest terrain you can see
  margin       body elevation minus skyline there. Above 0 = visible, below 0 = blocked.
"""
import csv
import math


def load_skyline(path):
    """Read the skyline CSV into a list of 360 angles. Index = whole-degree azimuth."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 360:
        raise ValueError(f"expected 360 skyline rows, got {len(rows)}")
    for i, row in enumerate(rows):
        if float(row["azimuth_deg"]) != i:
            raise ValueError(f"skyline row {i} has azimuth {row['azimuth_deg']}, expected {i}")
    return [float(row["skyline_deg"]) for row in rows]


def skyline_at(skyline, az_deg):
    """Skyline angle at any azimuth, blending the two nearest whole-degree rows.

    Example: az 213.4 = 60% of the 213 row + 40% of the 214 row.
    The % 360 and the (low + 1) % 360 make it wrap, so az 359.5 blends rows 359 and 0.
    """
    az = az_deg % 360
    low = math.floor(az)
    high = (low + 1) % 360
    frac = az - low
    return skyline[low] * (1 - frac) + skyline[high] * frac


def load_horizons(path):
    """Read a cached Horizons CSV into a list of dicts with real numbers."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "time_utc": r["time_utc"],
                "sun_az_deg": float(r["sun_az_deg"]),
                "sun_el_deg": float(r["sun_el_deg"]),
                "earth_az_deg": float(r["earth_az_deg"]),
                "earth_el_deg": float(r["earth_el_deg"]),
            })
    return rows


def analyse(horizons_rows, skyline):
    """Add skyline, margin and visible yes/no for the Sun and for Earth to every row.

    Simplification (also stated on the site): the Sun is treated as a point, not a disc,
    and Earth gets no safety margin.
    """
    out = []
    for r in horizons_rows:
        row = dict(r)
        for body in ("sun", "earth"):
            sky = skyline_at(skyline, r[f"{body}_az_deg"])
            margin = r[f"{body}_el_deg"] - sky
            row[f"{body}_skyline_deg"] = sky
            row[f"{body}_margin_deg"] = margin
            row[f"{body}_visible"] = margin > 0
        row["both_visible"] = row["sun_visible"] and row["earth_visible"]
        out.append(row)
    return out


def summarise(rows):
    """Percent of the time samples where the Sun, Earth and both are visible."""
    n = len(rows)
    return {
        "samples": n,
        "sun_visible_pct": 100 * sum(r["sun_visible"] for r in rows) / n,
        "earth_visible_pct": 100 * sum(r["earth_visible"] for r in rows) / n,
        "both_visible_pct": 100 * sum(r["both_visible"] for r in rows) / n,
    }
