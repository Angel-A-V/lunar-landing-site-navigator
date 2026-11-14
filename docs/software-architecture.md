# Software Architecture: Analysis and Stack

Written 2026-11-12 for Angel, Gustavo and Darren. Planning-phase document: it explains, it does not build.
Tags: **EXISTS** (in the repo now), **PROPOSED** (my recommendation, team decides), **[verify]** (unconfirmed).

---

## 1. The one-paragraph version

Two NASA datasets answer two questions. **JPL Horizons** tells us *where the Sun and Earth are in the sky* of a spot on the Moon, hour by hour. **LOLA terrain** tells us *how high the local skyline is* in every compass direction. The software compares the two: a body is "up" when its elevation is above the skyline at its azimuth. Everything the app shows (sunset time, Earth visible yes/no, sunlit percentage, compare two sites) comes from that one comparison.

### Who computes what (updated 2026-11-13)

| Step | Who |
|---|---|
| Sun and Earth direction (az, el) from the site, including libration | **NASA Horizons.** We only request it. |
| Terrain heights around the site | **NASA LOLA.** We only download them. |
| Skyline built from those heights | **Us.** NASA does not publish one per site. |
| Is the body above the skyline? Time to sunset, sunlit %, compare two sites | **Us.** Horizons only knows the flat horizon. |
| Making it understandable to a non-expert | **Us.** This is the value of the site. |

So the hard orbital and frame maths is NASA's. Our own calculation is two small pieces: build the skyline, and compare elevation against it.

### What "skyline" means

From the reference paper (`docs/references/skyline-photogrammetry-ntrs-19950008265.pdf`): the skyline is "the highest elevation angle separating sky and terrestrial objects at each azimuth." Stand at the site, turn in a full circle, and in each compass direction note how high the terrain reaches above the flat horizon.

It is **not the crater rim itself**. Our pick sits on the Shackleton rim, so the rim is where we stand and the skyline is the terrain around us. Real values for the pick (`data/skyline_shackleton_rim.csv`): highest +1.04° (azimuth 31°), lowest -2.92° (azimuth 293°), mean -1.24°, and **344 of 360 directions are below 0°**, because the ground falls away from a high perch. At the pole, Sun and Earth stay within a few degrees of the horizon, so these small angles decide visibility.

### Does this already exist? (searched 2026-11-13; cannot prove nothing exists [verify])
- The **method** is published: Mazarico et al. 2011 (*Icarus*) computed horizon elevations in many directions from polar terrain models and found a spot near the Shackleton rim sunlit about 240 days a year. https://ntrs.nasa.gov/citations/20120010094
- NASA PGDA publishes **static** south-pole illumination and Earth-visibility maps averaged over an 18.6-year cycle. https://pgda.gsfc.nasa.gov/products/69
- A JPL radar-DEM study put the best site's direct-to-Earth availability near 50%. https://ipnpr.jpl.nasa.gov/progress_report/42-176/176C.html
- These are specialist papers and fixed maps. Horizons gives any date but only against a flat horizon. We found nothing that lets a non-expert pick a site and date and see Sun and Earth against the real terrain with times.

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

**Update 2026-11-13:** caching is a speed and safety choice, not the goal of the site, and users never see it. The two datasets differ: the **skyline must be built ahead of time** (about 150 MB of terrain and millions of lookups), but **Sun and Earth can be fetched live** from Horizons for any date outside the cache. Use the cache as a fallback, and see section 5d for how browsers can reach Horizons.

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
5. **Not yet cross-checked** against Quickmap, Moon Trek or the NASA PGDA illumination and Earth-visibility maps. Planned (see section 7).
6. **Mazarico et al. 2011 model the Sun as a finite disc**, as does the Earth-visibility approach. Our point-Sun is a known gap to close or state.
7. **Skyline error** is limited by terrain resolution (20 m) and the 1° azimuth step. The 1995 photo-based paper reports about 4° mean error for its method; ours is geometric, not image-based, but we should still state our own error bound.

---

## 4. Components and the stack

| # | Component | Language / tool | Status | Notes |
|---|---|---|---|---|
| 1 | Site list | Python dict (`app/python/scripts/sites.py`) | EXISTS | One site today. Needs 3 to 5 for the MUST list [verify coordinates]. |
| 2 | Ephemeris fetch | Python, standard library only (`urllib`, `csv`, `json`) → JPL Horizons API | EXISTS | Caches CSV + meta. Needs one fetch per site. |
| 3 | Skyline builder | Python + numpy → NASA LOLA LDEM_85S_20M | EXISTS | Downloads about 150 MB once (git-ignored). The band covers ±50 km of the pole, so sites within about 15 km of the pole reuse the same download. |
| 4 | Tests | Python `unittest` | EXISTS | 16 checks, run with `cd app/python && python3 -m unittest discover -s tests -t . -v`. |
| 5 | Analysis core | Python (numpy optional) | PROPOSED, not written | Steps 2 to 6 above. Pure functions: data in, numbers out. No web or hardware knowledge in it. |
| 6 | Window statistics | Python script `compute_windows.py` | PROPOSED, not written | Precomputes per-site yearly stats (sunlit %, longest dark stretch) into JSON so the UI loads instantly. |
| 7 | Server | Python on the UNO Q Linux side | PROPOSED | See decision A. Serves the web files and answers JSON requests. |
| 8 | Web app | Vite + JavaScript + three.js (3D) + SVG | PROPOSED (Vite chosen by Angel 2026-11-13) | See "Frontend choice" below. |
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

### Frontend choice (updated 2026-11-13)
**Vite** (a build tool and dev server) with plain JavaScript, **three.js** for the 3D animations, and SVG for the flat diagrams. Reason: the team wants 3D to make the site stand out.
- Vite builds ordinary static files. The same output goes to Cloudflare Pages (public mode) and is served by the UNO Q (hardware mode).
- It adds a build step: Node is needed on a development laptop, **not on the UNO Q**.
- three.js runs on the visitor's graphics chip, so UNO Q speed only matters if the UNO Q's own monitor opens the page [verify].
- Start with plain JavaScript; React (react-three-fiber) is optional later.
- Order of work stays: MUST list and the data layer first, 3D surface view is COULD. Leave a clear place for the 3D scene in the page.

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

## 5d. What the Horizons API reference says (tested 2026-11-13)

Source: `docs/references/horizons-api-v1.3.pdf` (Horizons API v1.3, June 2025), plus one live test request.

- **We can make the calls.** Endpoint `https://ssd.jpl.nasa.gov/api/horizons.api`, no API key. A test for the Shackleton rim pick returned HTTP 200 and JSON, with values consistent with the cache.
- **`coord@301` is not in this PDF.** The PDF only lists `'coord'` for `CENTER`. The `@301` (observer on the Moon) comes from the longer Horizons manual but demonstrably works.
- **Version:** the PDF says check the `signature` version in the reply. The live reply said 1.2, the PDF says 1.3 (1.3 only added a mention of `TIME_TYPE`). Our fetch script should record it in the `.meta.json`.
- **No CORS header** was returned, so a browser page on another domain (Cloudflare Pages) probably cannot read Horizons directly. Use a go-between: the UNO Q Python server in hardware mode, or a small Cloudflare Worker (which can also cache at the edge) in public mode.
- **Errors can arrive as HTTP 200.** Input errors come in the payload; JSON replies carry an `error` field. Our script checks for the data block but not that field.
- **Overload:** 500 = database unavailable, 503 = overloaded or in maintenance. Add a retry with a pause (the current script has none).
- **Limits:** a list of specific times (`TLIST`) is capped at 10,000 and may hit URL-length limits. The PDF states no rate limit or terms [verify]. Request a whole date range in one call; do not make one call per slider move.
- **Privacy:** `EMAIL_ADDR` is optional. Leave it blank or use a team address, never a personal one.
- **Rise/transit/set from NASA:** `STEP_SIZE='5m RAD'` returns rise/transit/set rows for the **flat horizon** and worked at the rim pick. The only filter, `ELEV_CUT`, is one fixed angle, so it cannot use our skyline. Use it to cross-check our flat-horizon sunset finder. The marker letters in its output are not explained in the PDF [verify].

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

## 5e. Decision (Angel, 2026-11-14): the website covers the whole Moon

The challenge asks for "a curated list of notable landing sites – such as past Apollo missions, future CLPS mission targets ... as well as the ability to input custom lunar coordinates". Apollo sites are near the equator, so a south-pole-only tool is not enough. **The website covers the whole Moon. The physical model stays a one-site south-pole demo.** Tracked in GitHub issue #17 (moved to the Day 1 milestone).

| Piece | Whole Moon today? |
|---|---|
| Sun and Earth direction (Horizons) | **Yes.** `coord@301` accepts any latitude and longitude. Browsers cannot call Horizons directly (no CORS header, section 5d), so a Python go-between is needed. |
| Terrain skyline (our LOLA map) | **No, south pole only.** The map is `LDEM_85S_20M` (85°S to the pole). We only downloaded a ±50 km band and each ray looks out 35 km, so sites must be within about 15 km of the pole. The skyline math is fine; the data coverage is the limit. |
| The physical model | One site by design. |

### Terrain layers, best available first
1. **Polar map (have it):** `LDEM_85S_20M`, 20 m per pixel. Store the whole file (about 460 MB) on the backend to cover about 115 km from the pole.
2. **Global LOLA map:** `LDEM_128` (about 237 m per pixel, about 2 GB **[verify]** sizes and file names). A real, coarser skyline anywhere. Finer tiles (`LDEM_512`, about 59 m per pixel) later if time allows.
3. **Flat horizon, clearly labelled on screen,** only when no terrain data is available.

Source for the product list: PDS LOLA gridded data records (https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/LOLA/GDR/GDRDEM.htm).

### What this adds to the work
- **A second map reader.** The global map is a flat latitude/longitude grid, not the polar projection `make_skyline.py` reads. The skyline math is unchanged.
- **Different physics away from the pole.** At the pole the Sun barely changes elevation (±1.75°). Elsewhere it climbs high and sets every lunar day, and far-side sites never see Earth. Yearly percentages and "time to sunset" mean different things there, and the page must show them honestly.
- **Non-polar curated sites** (for example Apollo 11) **[verify coordinates]**.
- **Storage on the UNO Q:** about 17 GB free on the user partition, about 3.3 GB on the root partition. Terrain files go on the user partition; mount path **[verify]**.
- **Hosting:** public Cloudflare mode is static files, so custom coordinates there need a hosted backend. **Open decision:** custom points in public mode, or hardware mode only?

### Precomputed averages (bonus, not a replacement)
NASA publishes LOLA-derived average illumination and Earth-visibility maps for the poles (https://pgda.gsfc.nasa.gov/products/69; PDS GDRVIS). They are averages over about 18.6 years, not date-specific, so they cannot answer "this date" or "time to sunset". Use them as a bonus statistic for polar points and as a cross-check for issue #1.

### Order of work
1. Finish the south pole site end to end.
2. Add the global terrain layer and the second reader.
3. Add non-polar sites and typed coordinates.

---

## 6. Repo layout (PROPOSED, nothing created yet)

```
app/                         ALL CODE LIVES HERE (decided 2026-11-14); everything outside is team context
  index.html, src/, public/  the web app (Vite)
  python/analysis/           the pure calculation core            (EXISTS: visibility.py)
  python/scripts/            offline data jobs (fetch_horizons, make_skyline, sites, export_site_json)
  python/tests/              unittest checks
  python/server/             web server + API routes              (not created yet)
  sketch/                    Arduino sketch                       (not created yet)
data/                        shared cached CSV, JSON, meta (team data; code reads it from here)
```

### 6b. Frontend code architecture (PROPOSED 2026-11-13, nothing created)

Who writes this: the team, with their own prompts and agents. This section is the **map** so everyone builds the same shape, and so Angel can design the dashboard knowing where each piece lives. To understand the numbers behind it, read `how-the-calculations-work.md`.

```
app/
  index.html
  vite.config.js
  package.json
  public/data/        exported JSON for public mode (state tables, skylines, sources)
  src/
    main.js           start-up: reads the mode, builds the data layer, mounts the first view
    config.js         MODE = "public" or "hardware" (set with a Vite env variable at build time)
    data/             THE DATA LAYER (the only place that fetches anything)
      index.js        picks one implementation based on MODE
      api.js          asks the Python server (hardware mode)
      static.js       reads the exported JSON (public mode)
    state/            one small store: selected site(s), picked time, compare slots, explain mode
    views/            Explore, Compare, Sources (one per wireframe screen)
    components/       SitePicker, TimePicker, SkyDiagram (SVG), NumbersPanel, Timeline,
                      VerdictPills, HardwarePanel (hidden in public mode)
    three/            3D scenes (see below), kept apart from the flat components
    styles/
```

**Rules that keep it simple**
1. **Only `data/` talks to the outside.** Views and components ask the store or the data layer, never `fetch` directly. This is what lets one codebase run in both modes.
2. **Components receive plain numbers** (azimuths, elevations, margin, event times) and draw them. No NASA maths inside a component.
3. **The calculation lives once**, in the Python analysis core (or, for public mode, in precomputed JSON). The page displays results; it does not redo the physics.
4. **Hardware mode only adds things**: the HardwarePanel and the server connection. Remove them and the public site must still be complete.

**Build and run** (a build step now exists): on a laptop, install Node, then Vite builds a `dist/` folder of plain files. Public mode: upload `dist/` to Cloudflare Pages. Hardware mode: copy `dist/` onto the UNO Q and let the Python server serve it. Node is not needed on the UNO Q.

**The 3D parts (three.js), all COULD, after the MUST list works**
- **Moon globe**: a sphere with the site marked; click-to-pick-a-site is the later feature.
- **View from the site**: a ring of vertical walls, one per azimuth, whose heights come from the **same 360-row skyline file** (height ∝ tan of the skyline angle). This is the same idea as Gustavo's printed terrain wall, so the screen and the physical model show the same data.
- **Sun and Earth placement** in that view: convert (azimuth, elevation) back into a direction. With azimuth from north and elevation from level: east = sin(az)·cos(el), north = cos(az)·cos(el), up = sin(el). This is the reverse of the conversion Horizons already did, and ties directly to the frame chain.
- The 3D scene reads the **same store** as the flat diagram, so moving the time slider moves both.

**What to decide before building** (open): plain JavaScript or React for the views (default plain), and which visual elements matter most for the 3D budget.

---

## 7. How we know the numbers are right (checks to write on the day)

**Goal of the first version:** a bare-minimum, unstyled page that computes the real data and lets anyone verify it. Pick the site and a date/time, then show a table: Sun and Earth az/el (straight from Horizons), the skyline at that azimuth, the margin, visible yes/no, time to sunset and Earthset.

Checks, in order of value:
1. **Show NASA's raw numbers beside ours** on the page, so nobody has to trust that we did not alter them.
2. **Made-up inputs with known answers**: flat skyline at 0°, a Sun that climbs from -1° to +1°. Sunset must land at the exact crossing time. (Same style as the existing skyline tests.)
3. **Wrap-around**: azimuth 359.9 and 0.1 give nearly the same skyline value.
4. **Flat-horizon cross-check against NASA**: compare our sunset/sunrise on a flat skyline with Horizons' own rise/set mode (`STEP_SIZE='5m RAD'`, section 5d).
5. **Compare yearly percentages with published results**: our Sun about 80% and Earth about 51% against the NASA PGDA maps and the published figures in section 1 (Mazarico 2011 about 240 sunlit days a year near Shackleton; JPL about 50% direct-to-Earth). Expect the same range, not an exact match: cycle length, Sun disc and site pixel differ.
6. **Spot-check a few skyline azimuths by hand** against LOLA heights or Moon Trek's profile tool [verify].
7. **Real-data sanity** (already holds for the current cache): Sun elevation stays within about -1.75° to +1.74° at the pick; Earth az stays about 148° to 164°.
8. **Reproducibility**: every cached CSV has a meta file with the exact queries, so anyone can re-run and diff.

**Extra statistics from the skyline paper** (cheap, from the 360-row file): mean skyline, 90th-percentile skyline, and the percentage of sky visible above a given elevation. For the pick: mean -1.24°, 90th percentile about -0.4°.

First rough results over a year at the pick (Sun as a point, Earth with no margin): Sun above real skyline about 80% (54% on a flat horizon), Earth about 51%, both about 41%. Treat as provisional until step 5 above.

---

## 8. Open decisions for the team

1. Flask, standard library, or FastAPI (Decision A)?
2. Python computes or browser computes (Decision B)?
3. Which 3 to 5 sites, with verified coordinates? Each costs one Horizons fetch plus one skyline run.
4. Date range the picker supports. The cache covers 365 days from 2026-11-10. Beyond that we either fetch more or limit the picker.
5. Earth visibility margin: 0° or a few degrees? Treat the Sun as a point or as a disc?
6. UNO Q Bridge details: how does Python on Linux reach the STM32 sketch? [verify]
7. Horizons access for the public site: Cloudflare Worker go-between, or hardware mode only? (section 5d)
8. Does the UNO Q's own monitor run the 3D page? If yes, test three.js performance on it [verify].

## 9. Glossary (short)
- **Azimuth**: compass bearing, 0 = north, 90 = east.
- **Elevation**: angle above the local flat horizon.
- **Skyline / horizon profile**: highest terrain angle in each direction.
- **Libration**: the Moon's small rocking that shifts where Earth appears.
- **Ephemeris**: a table of where bodies are over time (Horizons produces ours).
- **LOLA**: the laser altimeter on NASA's Lunar Reconnaissance Orbiter that measured the terrain heights.
- **Margin**: body elevation minus skyline at the same azimuth. Positive = visible.
- **DTE**: direct-to-Earth radio link, which needs Earth above the skyline.
