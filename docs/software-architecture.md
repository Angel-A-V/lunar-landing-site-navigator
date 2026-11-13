# Software Architecture: Analysis and Stack

Written 2026-11-12 for Angel, Gustavo and Darren. Planning-phase document: it explains, it does not build.
Tags: **EXISTS** (in the repo now), **PROPOSED** (my recommendation, team decides), **[verify]** (unconfirmed).

---

## 1. The one-paragraph version

Two NASA datasets answer two questions. **JPL Horizons** tells us *where the Sun and Earth are in the sky* of a spot on the Moon, hour by hour. **LOLA terrain** tells us *how high the local skyline is* in every compass direction. The software compares the two: a body is "up" when its elevation is above the skyline at its azimuth. Everything the app shows (sunset time, Earth visible yes/no, sunlit percentage, compare two sites) comes from that one comparison.

---

## 2. Pipeline at a glance

```
 OFFLINE (run at home, results saved in data/)               ONLINE (UNO Q, Linux side)
 ─────────────────────────────────────────────              ──────────────────────────────────────
 scripts/sites.py        site list (lat, lon, height)
        │
        ├─► fetch_horizons.py ─► data/horizons_<site>_...csv      ┌────────────────────────┐
        │     (Sun + Earth az/el per hour)                  ────► │ Analysis core (Python) │
        │                                                         │  load, interpolate,    │
        └─► make_skyline.py ──► data/skyline_<site>.csv    ────► │  compare, find events  │
              (skyline elevation per azimuth)                     └───────────┬────────────┘
                                                                              │ JSON
                                                                  ┌───────────▼────────────┐
                                                                  │ Server: serves web app │
                                                                  │ + small JSON API       │
                                                                  └──────┬──────────┬──────┘
                                                                         │ HTTP     │ text lines
                                                                   Browser app   STM32 (motors, LED)
```

Why precompute (Wi-Fi is available, so this is not about being offline): (1) a Horizons call takes seconds and the app should answer instantly when someone drags the slider; (2) a cached table makes every number traceable and repeatable, because the `.meta.json` stores the exact Horizons query; (3) the app should not break if the Horizons service is slow or down during judging. A live "fetch any date" path can be added later on top of the cache.

---

## 3. The calculation, step by step

### Step 0: Frames (why we can lean on Horizons)
Sun and Earth positions start in a space frame. To know "which direction do I look from this spot," you need (1) the Moon's orientation, including **libration** (the Moon's small rocking, a few degrees, which decides whether Earth clears the horizon near the pole), and (2) the site's local east/north/up directions. Horizons already does all of this when asked as an observer on the Moon (`CENTER='coord@301'`), so we do not write orbital math. This is already in `fetch_horizons.py` (**EXISTS**).

- **Azimuth**: compass direction, 0 = north, 90 = east.
- **Elevation**: angle above the flat horizon at the site. Negative = below it.

### Step 1: The two input tables (**EXISTS**)

| File | Columns | Rows | Meaning |
|---|---|---|---|
| `horizons_<site>_<start>_<days>d_<step>.csv` | `time_utc, sun_az_deg, sun_el_deg, earth_az_deg, earth_el_deg` | 721 for 30 d hourly | Where each body is, per time sample |
| `skyline_<site>.csv` | `azimuth_deg, skyline_deg` | 360 | Highest terrain angle blocking the view in each direction |

**How the skyline is made** (`make_skyline.py`): for each of 360 azimuths, walk outward in 40 m steps up to 35 km across the 20 m LOLA height map. At each step, compute the angle from the site up to that terrain point (curvature of the Moon included, using the Moon's centre as reference). The skyline for that azimuth is the maximum angle seen. Heights are read from a polar-stereographic map, so `to_pixel` converts latitude/longitude to map pixels, and `destination` walks a great-circle path on the sphere.

### Step 2: Look up the skyline at any azimuth (**PROPOSED**)
Sun azimuth is rarely a whole degree, so we interpolate (blend) between the two neighbouring skyline rows. Wrap-around matters: azimuth 359.5 blends rows 359 and 0.

```
skyline_at(az):
    a = az mod 360
    i = floor(a); f = a - i            # whole part, fractional part
    return skyline[i]*(1-f) + skyline[(i+1) mod 360]*f
```

### Step 3: The visibility test (**PROPOSED**)
```
margin(body, t) = body.elevation(t) - skyline_at(body.azimuth(t))
body is visible  <=>  margin > 0
```
`margin` is the key number: how many degrees the body clears (or misses) the terrain. Positive = visible.

**Worked example, real data**, first row of the cache, 2026-11-10 00:00 UTC at the Shackleton rim pick:

| Body | Azimuth | Elevation | Skyline there | Margin | Visible? |
|---|---|---|---|---|---|
| Sun | 331.66° | +1.737° | -1.219° | +2.956° | **yes** |
| Earth | 159.69° | -7.019° | -0.928° | -6.091° | **no** |

(Note the skyline is slightly *negative* here: the pick is a high rim point, so some terrain falls away below the flat horizon. That is expected and is why "above the real skyline" differs from "above a flat horizon.")

### Step 4: Values at an arbitrary time (**PROPOSED**)
The table is hourly, but the user picks any minute. Linearly interpolate each column between the two surrounding rows. Azimuth needs wrap-aware blending (go the short way around 360). Hourly steps are fine because the Sun and Earth move slowly at this site (the Sun's azimuth sweeps a full circle over ~29.5 days, about 0.5° per hour).

### Step 5: Events and durations (**PROPOSED**)
- **Time to sunset** at time `t`: scan forward from `t` to the first sample where Sun margin goes from positive to negative. Refine by interpolating between those two samples to find where margin = 0. Answer = that time minus `t`. If the Sun is already down, the same scan finds **sunrise** instead.
- **Time to Earthset**: identical, with Earth.
- **Sunlit percentage** (over a window): number of samples with margin > 0, divided by total samples.
- **Both up**: both margins > 0 at the same sample. This is the number that matters for a mission (power and a comms link).
- **Longest dark stretch**: longest run of consecutive samples with Sun margin ≤ 0. Interesting for batteries.

### Step 6: Compare (**PROPOSED**)
Run Steps 2 to 5 for (site A, time A) and (site B, time B). Return both result sets plus per-row differences. "Compare two dates" is the same site twice with different times. No special logic: compare is just calling the same function twice.

### Known simplifications (state these in the app's data-sources page)
1. **The Sun is a point.** In reality it is a ~0.5° disc, so real sunset is a little later than "centre crosses the skyline." Earth's disc is ~1.9°. Refinement: test the body's upper edge, e.g. `elevation + radius`.
2. **Skyline is 360 samples, 1° apart** and out to 35 km. Distant peaks beyond 35 km are ignored.
3. **Earth margin is zero** (no safety buffer). A real radio link may need a few degrees. Make the margin a setting.
4. **The site pick is a working choice, not an official landing site** [verify].
5. **Not yet cross-checked** against Quickmap or Moon Trek illumination maps. Planned.

---

## 4. Components and the stack

| # | Component | Language / tool | Status | Notes |
|---|---|---|---|---|
| 1 | Site list | Python dict (`scripts/sites.py`) | EXISTS | One site today. Needs 3 to 5 for the MUST list [verify coordinates]. |
| 2 | Ephemeris fetch | Python, standard library only (`urllib`, `csv`, `json`) → JPL Horizons API | EXISTS | Caches CSV + meta. Needs one fetch per site. |
| 3 | Skyline builder | Python + numpy → NASA LOLA LDEM_85S_20M | EXISTS | Downloads about 150 MB once (git-ignored). The band covers ±50 km of the pole, so sites within about 15 km of the pole reuse the same download. |
| 4 | Tests | Python `unittest` | EXISTS | 16 checks, run with `python3 -m unittest discover -s tests -t . -v`. |
| 5 | Analysis core | Python (numpy optional) | PROPOSED, not written | Steps 2 to 6 above. Pure functions: data in, numbers out. No web or hardware knowledge in it. |
| 6 | Window statistics | Python script `compute_windows.py` | PROPOSED, not written | Precomputes per-site yearly stats (sunlit %, longest dark stretch) into JSON so the UI loads instantly. |
| 7 | Server | Python on the UNO Q Linux side | PROPOSED | See decision A. Serves the web files and answers JSON requests. |
| 8 | Web app | HTML + JavaScript + SVG | PROPOSED | See decision B. |
| 9 | Hardware link | Server → serial or UNO Q Bridge → Arduino sketch (STM32) | PROPOSED | Plain text lines: `SUN az el`, `EARTH az el`, `HOME`, `STATUS`. Bridge API [verify]. |
| 10 | Firmware | Arduino C++ sketch | Not started | Stepper (28BYJ-48 + ULN2003), LED, pot, LCD. Out of scope for this doc. |

**Dependency rule:** the analysis core (5) must never import the server (7) or the hardware link (9). That is what keeps the hard rule true: *the software works fully without the hardware.*

### Decision A: Python server flavour (needs a team decision)
| Option | Pro | Con |
|---|---|---|
| Standard library `http.server` | Zero installs, everything visible | We write routing and JSON headers ourselves |
| **Flask** (recommended) | Tiny, widely documented, a route is 3 lines | One `pip install` |
| FastAPI | Auto docs, type checks | More concepts (async, typing) for a 2-day build |

### Decision B: Where does the calculation run? (needs a team decision)
| Option | Pro | Con |
|---|---|---|
| **Python computes, browser displays** (recommended) | One place for the maths (matches "understand it all the way down"); same code feeds the hardware | App needs the server running |
| Browser computes from CSV files | App works as static files, even without Python | Maths written twice (JS for UI, Python for motors) |

**Recommendation:** Python computes. As a backup for a dead server on demo day, export a few ready-made JSON snapshots that the browser can read directly.

### Frontend choice (PROPOSED)
Plain HTML/CSS/JavaScript, drawing the sky diagram and timeline as **SVG**, with no build step and no framework. Reason: two days, one developer, and the screens are simple (see the Figma wireframe). If the team later wants a 3D Moon, add a library then. That is COULD, not MUST.

---

## 5. Proposed server interface (the contract the web app relies on)

All answers JSON. `t` is UTC ISO time. [PROPOSED, names can change]

| Request | Returns |
|---|---|
| `GET /api/sites` | List of curated sites: id, name, lat, lon |
| `GET /api/state?site=<id>&t=<time>` | Sun and Earth az, el, skyline there, margin, visible; time to sunset/sunrise; time to Earthset/Earthrise |
| `GET /api/skyline?site=<id>` | The 360 `(azimuth, skyline)` pairs for drawing the horizon |
| `GET /api/timeline?site=<id>&start=<time>&days=<n>` | Sun and Earth visibility per sample, for the timeline bars |
| `GET /api/compare?a=<id>@<time>&b=<id>@<time>` | Both state objects + differences |
| `GET /api/sources` | Source names, versions, retrieval time (from the `.meta.json` files) so the app can show attribution |

Hardware: the server converts a state into `SUN <az> <el>` and `EARTH <az> <el>` lines and writes them to the serial/Bridge link only if one is present. No device, no error, the app still works.

---

## 5b. Hosting: can it be public (Cloudflare) and still drive the hardware?

**Yes.** The public website and the hardware link are two separate questions.

The catch: the UNO Q sits on a home or venue network behind a router. A website on Cloudflare cannot open a connection *into* it. And a page served over `https://` is blocked by the browser from calling a plain `http://` device on the local network ("mixed content"; Chrome also restricts public pages reaching private addresses). So the hardware connection must be built one of these ways:

| Option | How it works | Pro | Con |
|---|---|---|---|
| **1. Static site on Cloudflare Pages, no hardware** | Web app and cached JSON are static files. Visitors get the full app anywhere. | Simplest, public link for judges, proves "software works without hardware" | No motors |
| **2. Cloudflare Tunnel from the UNO Q** | `cloudflared` runs on the UNO Q and gives the local server a public `https://` name. Browser talks to it; the server talks to the STM32. | Real server logic stays in Python, works from anywhere, HTTPS solved | Needs `cloudflared` for the UNO Q's ARM Linux [verify]; the demo depends on the UNO Q being on and online |
| **3. Cloud relay (Worker + WebSocket)** | UNO Q makes an *outbound* WebSocket to a Cloudflare Worker. The browser sends the chosen site/time to the same Worker, which forwards it down to the UNO Q. | No tunnel software, works through any router, clean "cloud brain, device listens" model | More moving parts; we write and run a relay |
| **4. Same-network local only** | Browser opens `http://<unoq-address>` on the same Wi-Fi. | Easiest hardware path | Not public; only people on that network |

**Recommendation (PROPOSED):** do 1 and 2 together.
- **Public site (option 1)** on Cloudflare Pages: the full analysis app with no hardware needed. This is the link for judges and the submission.
- **Hardware mode (option 2)**: the same app also served from the UNO Q through a tunnel, so a remote viewer can move the physical model. Option 3 is the fallback if the tunnel is a problem on the UNO Q.

**What this changes in the design**
- The Cloudflare-hosted version has no Python server. So the public app needs its numbers from either (a) **precomputed JSON** produced by the Python analysis core and committed with the site, or (b) the maths re-implemented in JavaScript. Precomputed JSON keeps the maths in one place. This makes Decision B in section 4 more important: if we want live "any minute" answers in the public version, the browser needs the interpolation and margin logic (Steps 2 to 5), which are small.
- **Safety and control:** a public page that can move motors needs protection. Minimum: the device (not the website) clamps every command to the allowed range, and hardware control sits behind a simple access check (for example Cloudflare Access, or a shared token) while the read-only app stays open.
- Everything in the hardware contract stays the same: `SUN az el`, `EARTH az el`, `HOME`, `STATUS`.
- Cloudflare is not needed for the analysis at all. It is only the delivery route.

---

## 5c. Decision (Angel, 2026-11-13): one codebase, two modes

The team wants both a public site and a hardware-connected site. We build **one codebase that runs in two modes**, not two separate sites, so the screens never drift apart and the work is not done twice.

| | **Public mode** (Cloudflare Pages) | **Hardware mode** (local, on the UNO Q) |
|---|---|---|
| Diagram, numbers, compare, data sources | same code | same code |
| Source of the numbers | precomputed JSON files | the Python server (or the same JSON) |
| "Send to model" panel and status light | hidden | shown |
| Needs the hardware | no | yes |

**Order of work**
1. Build **hardware mode first, locally.** It is what makes this entry unique and it must work in a demo room anyway.
2. Keep the public version cheap: the page reads its numbers through **one small data layer** (a single place that fetches state, skyline and timeline). Public mode just points that layer at static JSON and hides the hardware panel.
3. Only afterwards decide on a tunnel (option 2 in 5b) so the physical model can be moved from the public link. Optional polish.

**Design rule to keep:** the data layer stays separate from the page code from day one. If time runs out, "local only now, public later" costs very little.

Naming note: the board is the Arduino UNO Q (Linux side plus an STM32 chip), not a Raspberry Pi.

---

## 6. Repo layout (PROPOSED, nothing created yet)

```
scripts/        offline data jobs (EXISTS: fetch_horizons, make_skyline, sites)
analysis/       the pure calculation core            (new)
server/         web server + API routes              (new)
app/            HTML, JavaScript, CSS                (new)
firmware/       Arduino sketch                       (new)
data/           cached CSV, JSON, meta               (EXISTS)
tests/          unittest checks                      (EXISTS, grows with analysis/)
```

---

## 7. How we know the numbers are right (checks to write on the day)

1. **Made-up inputs with known answers**: flat skyline at 0°, a Sun that climbs from -1° to +1°. Sunset must land at the exact crossing time. (Same style as the existing skyline tests.)
2. **Wrap-around**: azimuth 359.9 and 0.1 give nearly the same skyline value.
3. **Real-data sanity** (these already hold for the current cache): Sun elevation stays within about -1.75° to +1.74° at the pick; Earth az stays about 148° to 164°.
4. **Reproducibility**: every cached CSV has a meta file with the exact queries, so anyone can re-run and diff.
5. **External cross-check** (not done): compare sunlit/dark periods against NASA Quickmap illumination for the same location and dates.

First rough results over a year at the pick (Sun as a point, Earth with no margin): Sun above real skyline about 80% (54% on a flat horizon), Earth about 51%, both about 41%. Treat as provisional until step 5 above.

---

## 8. Open decisions for the team

1. Flask, standard library, or FastAPI (Decision A)?
2. Python computes or browser computes (Decision B)?
3. Which 3 to 5 sites, with verified coordinates? Each costs one Horizons fetch plus one skyline run.
4. Date range the picker supports. The cache covers 365 days from 2026-11-10. Beyond that we either fetch more or limit the picker.
5. Earth visibility margin: 0° or a few degrees? Treat the Sun as a point or as a disc?
6. UNO Q Bridge details: how does Python on Linux reach the STM32 sketch? [verify]

## 9. Glossary (short)
- **Azimuth**: compass bearing, 0 = north, 90 = east.
- **Elevation**: angle above the local flat horizon.
- **Skyline / horizon profile**: highest terrain angle in each direction.
- **Libration**: the Moon's small rocking that shifts where Earth appears.
- **Ephemeris**: a table of where bodies are over time (Horizons produces ours).
- **LOLA**: the laser altimeter on NASA's Lunar Reconnaissance Orbiter that measured the terrain heights.
- **Margin**: body elevation minus skyline at the same azimuth. Positive = visible.
- **DTE**: direct-to-Earth radio link, which needs Earth above the skyline.
