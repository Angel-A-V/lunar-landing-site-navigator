#!/usr/bin/env python3
"""Fetch the Sun's and Earth's direction (azimuth, elevation) as seen from a Moon site.

Asks NASA JPL Horizons, standing at a point on the Moon's surface. Horizons does the
whole frame chain for us (space -> Moon-fixed incl. libration -> local east/north/up).
Results are cached in data/ so the demo works offline. No third-party packages needed.

Azimuth: compass direction, 0 = north, 90 = east. Elevation: angle above the flat
horizon (negative = below). No atmosphere on the Moon, so no refraction (AIRLESS).

Run:  python3 scripts/fetch_horizons.py                        (30 days, hourly)
      python3 scripts/fetch_horizons.py --days 365 --step "6 h"  (a full year)
"""
import argparse
import csv
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

from sites import SITE_HEIGHT_M, SITES

API = "https://ssd.jpl.nasa.gov/api/horizons.api"
BODIES = {"sun": "10", "earth": "399"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_params(body_id, lat, lon_east, height_m, start, stop, step):
    """The exact Horizons query. Saved next to the data for anyone who wants to re-run it."""
    return {
        "format": "json",
        "COMMAND": f"'{body_id}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@301'",            # observer on the Moon (body 301)
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{lon_east},{lat},{height_m / 1000:.4f}'",  # east lon, lat, km
        "START_TIME": f"'{start}'",
        "STOP_TIME": f"'{stop}'",
        "STEP_SIZE": f"'{step}'",
        "QUANTITIES": "'4'",                # 4 = azimuth and elevation
        "ANG_FORMAT": "'DEG'",
        "APPARENT": "'AIRLESS'",            # no atmosphere on the Moon
        "CSV_FORMAT": "'YES'",
    }


def parse_result(text):
    """Pull (time, az, el) rows out of the Horizons text between $$SOE and $$EOE."""
    if "$$SOE" not in text:
        raise ValueError("Horizons reply has no data block:\n" + text[:800])
    block = text.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    rows = []
    for line in block.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        rows.append((parts[0], float(parts[3]), float(parts[4])))
    return rows


def query(params):
    url = API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        data = json.load(r)
    if "result" not in data:
        raise RuntimeError(f"Horizons error: {data}")
    return data["result"], url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="shackleton_rim", choices=SITES)
    ap.add_argument("--start", default="2026-11-10", help="UTC date, YYYY-MM-DD")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--step", default="1 h", help='Horizons step, e.g. "1 h" or "6 h"')
    ap.add_argument("--refresh", action="store_true", help="ignore the cache")
    a = ap.parse_args()

    lat, lon = SITES[a.site]
    start = a.start
    stop = (dt.date.fromisoformat(a.start) + dt.timedelta(days=a.days)).isoformat()
    tag = f"{a.site}_{a.start}_{a.days}d_{a.step.replace(' ', '')}"
    out_csv = os.path.join(ROOT, "data", f"horizons_{tag}.csv")
    out_meta = os.path.join(ROOT, "data", f"horizons_{tag}.meta.json")
    if os.path.exists(out_csv) and not a.refresh:
        print("cached:", out_csv)
        return

    series, urls = {}, {}
    for name, body in BODIES.items():
        params = build_params(body, lat, lon, SITE_HEIGHT_M[a.site], start, stop, a.step)
        text, urls[name] = query(params)
        series[name] = parse_result(text)

    sun, earth = series["sun"], series["earth"]
    assert [r[0] for r in sun] == [r[0] for r in earth], "Sun and Earth times differ"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "sun_az_deg", "sun_el_deg", "earth_az_deg", "earth_el_deg"])
        for (t, saz, sel), (_, eaz, eel) in zip(sun, earth):
            w.writerow([t, f"{saz:.4f}", f"{sel:.4f}", f"{eaz:.4f}", f"{eel:.4f}"])
    meta = {
        "site": a.site, "lat_deg": lat, "lon_deg_east": lon,
        "site_height_m": SITE_HEIGHT_M[a.site],
        "start_utc": start, "stop_utc": stop, "step": a.step, "rows": len(sun),
        "source": "NASA JPL Horizons API (ssd.jpl.nasa.gov), ephemeris DE441, "
                  "Moon orientation MEAN_ME high precision (includes libration)",
        "azimuth": "0 = north, 90 = east",
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "queries": urls,
    }
    with open(out_meta, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote {out_csv} ({len(sun)} rows)")


if __name__ == "__main__":
    main()
