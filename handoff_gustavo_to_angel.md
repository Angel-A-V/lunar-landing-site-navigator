# Handoff: Gustavo → Angel — terrain disc + wall

Nov 10, 2026 · from Gustavo (disc + terrain wall) · for Angel (code owner)

## TL;DR

- I have a printable disc + terrain wall built from your `data/skyline_shackleton_rim.csv`.
- To get it, a new script and test were added to the repo (made with Claude's help). Since you own all code, **please review and merge** them. Nothing you wrote was changed except the README and CLAUDE.md status lines.
- I need three things from you, listed at the bottom: a code review, the Earth direction from Horizons, and new skyline CSVs if we add sites.

## What was added

| File | What it is |
| --- | --- |
| `scripts/make_wall.py` | Reads the skyline CSV, writes the STL, shaft coupon, SolidWorks curves and a JSON of numbers into `cad/`. numpy only, runs in under 1 s. |
| `tests/test_wall.py` | 7 checks: mesh is closed and facing outward, wall height matches the formula, east = +X and north = +Y, auto pedestal height, shaft hole size, Earth direction math, and a full run. |
| `cad/terrain_disc_shackleton_rim.stl` | The printable part: disc, wall, centre pedestal, shaft socket. |
| `cad/shaft_coupon.stl` | 5 fit-test pucks for the 28BYJ-48 shaft. |
| `cad/sw_wall_top_{outer,inner}_shackleton_rim.txt` | Wall-top curves so I can model it in SolidWorks myself. |
| `cad/terrain_disc_shackleton_rim.json` | Every dimension used, plus a lamp-height table for Darren. |
| `README.md`, `CLAUDE.md` | A short "make the wall" section and updated Done / Not done lines. |

Run:

```
python3 scripts/make_wall.py              # defaults below
python3 scripts/make_wall.py --help       # every dimension is a flag
python3 -m unittest tests.test_wall tests.test_skyline -v
```

All 16 tests pass. The 3 real-terrain skyline tests skip until `data/raw/` is downloaded.

## How the wall is built from your CSV

The same exaggeration k is used for the wall and the lamp, so the lamp drops behind the wall exactly when the real Sun drops behind the real ridge:

```
wall height above disc = pedestal_h + r_wall * k * tan(skyline_deg)
lamp height above disc = pedestal_h + r_lamp * k * tan(sun_elevation)
```

- The pedestal top is the "eye", the spot the observer stands on.
- The pedestal height is chosen automatically, so the most negative skyline point still leaves a 2 mm wall.
- The wall's **outer** radius is the `r_wall` in the formula. A ray from the eye has to clear the outer top edge, so that edge is the one that blocks.

## Current numbers (defaults)

| Item | Value |
| --- | --- |
| Disc | 140 mm diameter, 4 mm thick |
| Wall | outer radius 60 mm, 2.4 mm thick |
| k (vertical exaggeration) | 10 |
| Pedestal (eye height) | 33 mm above the disc top, 12 mm diameter |
| Wall height | 2.4 to 43.9 mm above the disc. Lowest at az 293° (−2.92°), highest at az 31° (+1.04°) |
| Total part height | ~48 mm, about 83 cm³ of solid |
| Shaft socket | D-hole, 5.0 mm diameter / 3.0 mm across the flats + 0.15 mm clearance, 7 mm deep **[verify with calipers]** |
| North mark | V-notch in the rim at az 0 |
| Layout | Seen from above: north = +Y, east = +X, azimuth clockwise from north |

## Things that affect your code

1. **Disc angle and stepper.** The rim notch marks azimuth 0 (north). The firmware maps Sun azimuth to a disc angle using that zero. The spin direction in the handoff doc (surface turns clockwise seen from above) is still **[verify against the app]**.
2. **Earth marker direction.** I engraved a line toward Earth's **mean** direction: az 156.3°, el −0.20°. This comes from a simple calculation (sub-Earth point at lat 0, lon 0, no libration) in `earth_mean_direction()`. **Please check it against Horizons** for this site. If it's off by more than a degree or two, tell me the correct azimuth and I'll rerun.
3. **Lamp height for Darren.** It depends on the Sun elevation from your Horizons data. The JSON has a table for r_lamp = 150 mm (for example, a Sun at 1.5° puts the lamp 72 mm above the disc top). Once you have the real Sun elevation range for this site, Darren can fix the lamp slot height.
4. **If k, r_wall or the pedestal height change**, both the wall and the lamp table change. Please don't change those defaults without telling both of us.

## Adding another site later

- I'll send you the latitude and longitude. You add it to `SITES` in `make_skyline.py` and run it, then I run `make_wall.py --csv data/skyline_<site>.csv --site <site>`.
- Limit: the downloaded terrain band only covers about 50 km around the pole, and the skyline looks 35 km out. So the site has to be within about 15 km of the pole (latitude about −89.5° or further south). Off-pole sites like Malapert also break the fixed-lamp model.

## What I need from you

- [ ] Review and merge `scripts/make_wall.py` + `tests/test_wall.py` (or tell me what to change).
- [ ] Check the Earth mean azimuth (156.3°) for the site against Horizons.
- [ ] Give the Sun elevation range at the site (for Darren's lamp height).
- [ ] Confirm the spin direction and the "az 0 = rim notch" home position for the firmware.

## My next steps

1. Print `shaft_coupon.stl` (about 15 min). Pick the best fit, then rerun with `--clearance <value>`. The rim notches 1–5 mean clearances 0.10 / 0.15 / 0.20 / 0.25 / 0.30 mm.
2. Agree on the disc diameter, wall radius, lamp distance and shaft position with Darren.
3. Print the disc overnight: flat side down, no supports, 0.28 mm draft layers.

Data source: NASA LRO LOLA LDEM_85S_20M (PDS Geosciences Node), via Angel's `make_skyline.py`.
