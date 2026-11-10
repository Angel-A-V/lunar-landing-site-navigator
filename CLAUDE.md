# CLAUDE.md: Lunar Landing Site Navigator (NASA Space Apps 2026, Challenge 11)

Team: Angel (CS/CE, owns all code, electronics, integration), Gustavo (ME, Sun mechanism), Darren (ME, Earth arm, base, electronics bay).
The MEs do not write code. All main code (ephemeris, web app, main firmware) lives with Angel to avoid merge conflicts.
Backup: Challenge 3 (Junior Astronaut Mission Trainer). Go/no-go at the end of Phase 1; see the plan.

Source docs in this folder (read them for detail, do not duplicate them here):
- `Project Plan – Lunar Landing Site Navigator.md`: full plan, interface contract, assignments, risks.
- `SpaceApps Hackathon – Hardware Inventory.md`: what we own.
- `NasaSpaceApps-Challenges/nasachall11.pdf` (primary), `nasachall3.pdf` (backup). Challenge 11 text was read directly and matches the plan. Notes from it: no required deliverable list (everything is "you may consider"); the Moon has no atmosphere, so the horizon is local terrain plus the edge of the lunar sphere; it names libration and lunar orbital variation as accuracy factors; audiences are mission planners, educators, and the public; the Resources tab on the challenge page can still gain links before the hackathon. To extract PDF text here: `pip install --target <dir> pypdf` (poppler is not installed).

## What we are building

The problem: lunar south pole missions must pick a landing **site** and **date**. That decides (1) solar power, via the Sun's elevation above the local horizon, and (2) direct-to-Earth communication, via whether Earth is above the local horizon.

NASA tools exist (JPL Horizons, Quickmap, Moon Trek) but are hard for non-specialists to use for fast scenario comparison. We build an intuitive tool:
- Pick a site (curated list, optionally custom coordinates) and a date/time.
- Show Sun and Earth relative to the horizon (az/el diagram).
- Show numbers: Sun elevation, sunlight duration, time to sunset, Earth visible yes/no, time to Earthset.
- Compare sites or dates side by side. Explain data sources in the tool.

Two parts:
1. **Software core** (web app on the Arduino UNO Q Linux side). This answers the challenge and is judged first.
2. **Physical companion**: tabletop south pole model. Lamp on a stepper-driven ring = Sun (azimuth, 360°). SG90 servo arm = Earth (small libration wobble). Moves in sync with the app.

**Hard rule: the software must work fully without the hardware.** Hardware is a companion, never a dependency.

## The core concept (how the team should think about it)

The observer is **standing at the landing site on the Moon**, not on Earth. The computation answers: "from this spot, at this time, in which direction (azimuth, elevation) do I see the Sun and Earth?"

Frame chain:
1. **Space frame (inertial, e.g. ICRF/J2000).** Sun, Earth, Moon positions come from an ephemeris (JPL Horizons, or SPICE/Skyfield kernels).
2. **Moon-fixed frame** (body-fixed, lat/lon on the Moon). The rotation from inertial to Moon-fixed (a rotation matrix or quaternion) comes from the lunar orientation model and includes **libration**. This is where the quaternion lives.
3. **Site-local frame (east, north, up) at (lat, lon).** Dot the Sun/Earth direction vector (in the Moon-fixed frame) with the site's east/north/up basis. Then elevation = asin(up), azimuth = atan2(east, north).

The same operation gives both Sun and Earth. Sun mostly changes with hour angle (one lunar day = ~29.53 Earth days). Earth wobbles within a few degrees (libration), which at the pole decides whether Earth is above the horizon.

Practical consequence: JPL Horizons can already do the whole chain for an observer at lunar surface coordinates and return az/el. Prefer an API or library (Horizons, Skyfield) over hand-written orbital math. Precompute and cache results for demo sites so the demo works offline.

Terrain matters at the pole: a flat horizon (up if elevation > 0) is the first version; LOLA-derived horizon profiles (list of azimuth, skyline elevation) come next for 2 to 3 sites. The terrain silhouette ring (Gustavo) is printed from that same data.

An interactive explainer of this lives in the artifact built for the team (frames chain, globe, site sky, lunar-day timeline). It uses a simplified teaching model, not real ephemeris data.

## MUST / SHOULD / COULD

MUST: 3 to 5 curated sites; date/time picker; Sun and Earth vs horizon diagram; numbers (Sun elevation, time to sunset, Earth visible, time to Earthset); compare two sites or dates; data sources explained in-app.
SHOULD: timeline over one lunar day; custom coordinates; LOLA terrain horizon for the main site; plain-language explain mode.
COULD: 3D surface view; rigorous libration; many sites with "best date" suggestions.
Build MUST first. Do not add SHOULD/COULD before MUST works.

## Architecture and contract

Browser web app <-> (HTTP/WebSocket, Wi-Fi) <-> Arduino UNO Q.
- Linux side (Python): ephemeris math, serves the web app, sends motor commands.
- MCU side (STM32, Arduino sketch): drives stepper (28BYJ-48 + ULN2003) and servo (SG90) in real time; reads pot (timeline scrub), buttons (site select), photoresistor (solar power reading); LCD1602 status.
- Motors powered from the breadboard supply module, never from UNO Q pins.

Command format (draft, plain text lines over serial or UNO Q Bridge):
```
SUN <azimuth_deg> <elevation_deg>
EARTH <azimuth_deg> <elevation_deg>
HOME
STATUS
```
Interface contract fields still blank in the plan: model footprint, stepper/servo measured dimensions, degrees per step after gearing, Earth arm range, home switch location, wire exits and electronics bay. Do not invent values; ask or leave blank.

## Conventions for working in this repo

- Items tagged **[verify]** in the plan are unconfirmed (site coordinates, part dimensions, pin numbers, UNO Q Bridge API, orbital numbers). Do not treat them as fact. Check before depending on them.
- Build small testable pieces first: stepper moves N degrees, then reads pot, then parses `SUN 215 1.2`, then the app.
- Explain things in plain language for a mixed ME/software team. Define terms (azimuth, elevation, libration, LOLA, DTE) when used.
- Keep a screen-recorded backup demo and an offline data cache. Attribute all data sources in the submission.
- Hardware: Arduino UNO Q, ELEGOO UNO R3, "Tiny" mini board, ELEGOO kit, perfboards, soldering kit, Bambu Lab A1 (about 256 mm bed, [verify]). See the inventory file.

## Current state (updated 2026-11-10) and decisions since the plan

Read `spaceapps_context_handoff.md` for the full story. Short version:
- **No machine learning.** Everything is physics and geometry from NASA data, so numbers can be traced and checked. Do not add ML.
- **Time is about 2 days.** The hardware was cut to a two-day design: the Moon surface (a ~140 mm disc with the printed terrain wall) rotates on the stepper under a fixed lamp. Nothing electrical rides on the disc. One site only for the model. The older plan text still describes the moving Sun ring and servo Earth arm; the handoff file overrides it.
- **Model site: Shackleton crater rim, working pick at -89.781, 203.743 E.** Found from LOLA data as the highest rim point on the ridge facing the pole. It is NOT an official landing site. [verify] against a published candidate list before the pitch.
- **Website vision:** compare two spots, chosen from curated sites first, then typed coordinates, then clicking a 3D Moon (the last two are SHOULD/COULD; see MUST list).
- **Done:** `scripts/make_skyline.py` builds `data/skyline_shackleton_rim.csv` (azimuth_deg, skyline_deg; 360 rows) from real LOLA terrain. `tests/` has 16 passing checks (skyline: made-up terrain with known answers plus real-data checks; Horizons: parser, query and physics sanity). Gustavo's wall script reads that CSV. Raw terrain (`data/raw/`) is git-ignored; the script re-downloads it.
- **Done (Horizons):** `scripts/fetch_horizons.py` queries JPL Horizons as an observer on the Moon (`CENTER='coord@301'`, `SITE_COORD` east-lon,lat,km, `QUANTITIES=4`, `APPARENT=AIRLESS`) and caches `data/horizons_<site>_<start>_<days>d_<step>.csv` + `.meta.json` (exact queries). Cached: 30 days hourly and 365 days 6-hourly from 2026-11-10. Horizons uses DE441 and the high-precision Moon orientation (includes libration), so no hand-written orbital math. Findings at the Shackleton rim pick: Sun elevation stays within about -1.75 to +1.74 deg over a year; Earth elevation about -7.3 to +6.4 deg, azimuth about 148 to 164 deg. First rough result over the year (Sun as a point, Earth with no margin): Sun above the real skyline ~80% (54% on a flat horizon), Earth ~51%, both ~41%. Not yet cross-checked against Quickmap illumination maps.
- **Not done yet:** the website, firmware, Quickmap/Moon Trek cross-check, the CAD script, window statistics script (`compute_windows.py`), Darren's lamp-height number (derive from the Sun elevation data).
- **Repo:** https://github.com/Angel-A-V/lunar-landing-site-navigator (private). Work is tracked in GitHub Issues and Milestones.
- **Teammate needs:** Gustavo needs only the skyline CSV (+ `r_wall`, `k`, pedestal height). Darren needs lamp height/distance and spin direction, not the terrain data. Neither needs the ephemeris code.
- **Run it:** needs numpy (`sudo apt install python3-numpy`), then `python3 -m unittest discover -s tests -t . -v`. See `README.md`.
- **Repo hygiene:** `.claude/`, `data/raw/`, caches, and the 12 unused challenge PDFs are git-ignored on purpose.

## Open questions (from the plan)

- Which 3 to 5 sites and exact coordinates [verify]
- USB-C supply, monitor, camera for the UNO Q
- Filament type, colors, amount
- Extra SG90 servos and LED strip (optional)
- Read the Resources tab on each challenge page and add links to the plan
