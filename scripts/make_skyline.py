#!/usr/bin/env python3
"""Build a skyline (horizon profile) for a Moon site from NASA LOLA terrain data.

For each compass direction (azimuth, 0 = north, 90 = east) it walks outward from
the site across the terrain map and records the highest angle above the flat
horizon that any terrain blocks. Output CSV: azimuth_deg, skyline_deg.

Data: LOLA LDEM_85S_20M (20 m per pixel, polar stereographic, heights in metres
above a 1737.4 km sphere). Source: https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
Only the central band of rows is downloaded (about 150 MB instead of 460 MB).

Run:  python3 scripts/make_skyline.py            (needs numpy)
"""
import argparse
import csv
import json
import os
import urllib.request

import numpy as np

URL = "https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/LDEM_85S_20M.IMG"
N = 15168                 # map is N x N pixels, 16-bit little-endian
PX_M = 20.0               # metres per pixel
CENTER = 7583.5           # pole is at this pixel (row and column)
R = 1737400.0             # reference sphere radius in metres
BAND_ROWS = 5000          # rows kept: +/- 50 km from the pole
ROW0 = 5084               # first row of the band
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "band_85S_20M.bin")

# Working site choices (NOT official landing sites). Found from the terrain data:
# highest point on the Shackleton crater rim, on the ridge facing the pole.
# [verify] against published candidate-site coordinates before using in the pitch.
SITES = {"shackleton_rim": (-89.781, 203.743)}


def fetch_band():
    if os.path.exists(RAW) and os.path.getsize(RAW) == BAND_ROWS * N * 2:
        return
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    start = ROW0 * N * 2
    end = (ROW0 + BAND_ROWS) * N * 2 - 1
    req = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}"})
    print("downloading terrain band (~150 MB)...")
    with urllib.request.urlopen(req) as r, open(RAW, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def to_pixel(lat, lon):
    """Latitude/longitude (degrees, south negative) -> fractional (row, col) in the band."""
    rho = 2 * R * np.tan(np.radians(90.0 + lat) / 2)
    lo = np.radians(lon)
    x, y = rho * np.sin(lo), rho * np.cos(lo)
    return CENTER - y / PX_M - ROW0, CENTER + x / PX_M


def sample(h, row, col):
    """Bilinear height lookup (metres)."""
    r0, c0 = np.floor(row).astype(int), np.floor(col).astype(int)
    fr, fc = row - r0, col - c0
    return (h[r0, c0] * (1 - fr) * (1 - fc) + h[r0, c0 + 1] * (1 - fr) * fc
            + h[r0 + 1, c0] * fr * (1 - fc) + h[r0 + 1, c0 + 1] * fr * fc)


def destination(lat, lon, az, dist):
    """Point reached from (lat, lon) going `dist` metres on bearing `az` (great circle)."""
    la, lo, b, t = np.radians(lat), np.radians(lon), np.radians(az), dist / R
    la2 = np.arcsin(np.sin(la) * np.cos(t) + np.cos(la) * np.sin(t) * np.cos(b))
    lo2 = lo + np.arctan2(np.sin(b) * np.sin(t) * np.cos(la),
                          np.cos(t) - np.sin(la) * np.sin(la2))
    return np.degrees(la2), np.degrees(lo2)


def skyline(h, lat, lon, step_deg=1.0, max_km=35.0, step_m=40.0, mast_m=0.0):
    row, col = to_pixel(lat, lon)
    h_site = sample(h, np.array(row), np.array(col)) + mast_m
    d = np.arange(step_m, max_km * 1000, step_m)
    out = []
    for az in np.arange(0, 360, step_deg):
        la2, lo2 = destination(lat, lon, az, d)
        r, c = to_pixel(la2, lo2)
        ht = sample(h, r, c)
        theta = d / R   # angle at the Moon's centre; accounts for curvature exactly
        up = (R + ht) * np.cos(theta) - (R + h_site)
        out_ = (R + ht) * np.sin(theta)
        out.append((az, float(np.degrees(np.arctan2(up, out_)).max())))
    return out, float(h_site)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="shackleton_rim", choices=SITES)
    ap.add_argument("--step-deg", type=float, default=1.0)
    ap.add_argument("--max-km", type=float, default=35.0)
    a = ap.parse_args()

    fetch_band()
    h = np.fromfile(RAW, dtype="<i2").reshape(BAND_ROWS, N) * 0.5
    lat, lon = SITES[a.site]
    prof, h_site = skyline(h, lat, lon, a.step_deg, a.max_km)

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    path = os.path.join(ROOT, "data", f"skyline_{a.site}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["azimuth_deg", "skyline_deg"])
        for az, el in prof:
            w.writerow([f"{az:.1f}", f"{el:.3f}"])
    els = [e for _, e in prof]
    meta = {
        "site": a.site, "lat_deg": lat, "lon_deg_east": lon,
        "site_height_m_above_1737.4km_sphere": h_site,
        "azimuth": "0 = north, 90 = east, step %.1f deg" % a.step_deg,
        "max_range_km": a.max_km,
        "skyline_min_deg": min(els), "skyline_max_deg": max(els),
        "skyline_mean_deg": sum(els) / len(els),
        "source": "NASA LRO LOLA LDEM_85S_20M (PDS Geosciences Node GDR)",
        "status": "site choice is a working pick, [verify] before publishing",
    }
    with open(os.path.join(ROOT, "data", f"skyline_{a.site}.meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(path)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
