# Lunar Landing Site Navigator (NASA Space Apps 2026, Challenge 11)

A website that compares two spots on the Moon's south pole and shows which is
better for a landing: is the Sun up (power) and is Earth up (radio link)?
A small tabletop model shows one site with a lamp as the Sun and a printed copy
of the real horizon.

Team: Angel (code, electronics), Gustavo (disc and terrain wall), Darren (stand and lamp).
Start with `CLAUDE.md` (short project brief) and `spaceapps_context_handoff.md` (full context).

## Setup

You need Python 3.10+ and numpy.

```
# Ubuntu / WSL (simplest)
sudo apt install python3-numpy

# or anywhere
python3 -m pip install --user -r requirements.txt
# if pip says "externally-managed-environment":
#   python3 -m pip install --user --break-system-packages -r requirements.txt
```

## Run the self-test

```
python3 -m unittest tests.test_skyline -v
```

All tests should pass. Three of them skip if the terrain file is not downloaded yet.

## Make the skyline for the model

```
python3 scripts/make_skyline.py
```

Downloads about 150 MB of NASA LOLA terrain into `data/raw/` (not committed) and
writes `data/skyline_shackleton_rim.csv` and a `.meta.json` next to it.
The CSV is what the CAD script for the printed wall reads.

## Get the Sun and Earth directions (NASA JPL Horizons)

```
python3 scripts/fetch_horizons.py                          # 30 days, hourly
python3 scripts/fetch_horizons.py --days 365 --step "6 h"  # a full year
```

Needs internet once; results are cached in `data/horizons_*.csv` (with a `.meta.json`
holding the exact queries) so the demo works offline. No numpy needed.
Columns: `time_utc, sun_az_deg, sun_el_deg, earth_az_deg, earth_el_deg`.

## Folders

| Folder | What |
| --- | --- |
| `scripts/` | Data scripts: `make_skyline.py` (terrain), `fetch_horizons.py` (Sun/Earth), `sites.py` (site list) |
| `tests/` | Self-tests |
| `data/` | Small committed outputs (CSV). Big raw downloads go in `data/raw/` and are ignored |
| `NasaSpaceApps-Challenges/` | Challenge text (11 primary, 3 backup) |

## Data sources

NASA LRO LOLA gridded elevation (LDEM_85S_20M, PDS Geosciences Node).
NASA JPL Horizons (ephemeris DE441, Moon orientation including libration) for Sun/Earth directions.
