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

## Folders

| Folder | What |
| --- | --- |
| `scripts/` | Data scripts (skyline now; Horizons Sun/Earth fetch next) |
| `tests/` | Self-tests |
| `data/` | Small committed outputs (CSV). Big raw downloads go in `data/raw/` and are ignored |
| `NasaSpaceApps-Challenges/` | Challenge text (11 primary, 3 backup) |

## Data sources

NASA LRO LOLA gridded elevation (LDEM_85S_20M, PDS Geosciences Node).
JPL Horizons for Sun/Earth directions (not added yet).
