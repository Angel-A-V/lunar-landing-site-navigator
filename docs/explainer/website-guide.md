# Moon Sky Explainer – Website Guide and Project Definition

Nov 6, 2026 · @Angel

Our website answers one question for any spot on the Moon at any time: where are the Sun and Earth in that spot's sky, and is it a good time to be there? Live page: [Moon Sky Explainer](https://claude.ai/artifact/T4NRv5LUhoz4NYVLKVnbVV).

## Project definition

We are building an easier tool on top of NASA's existing lunar tools so beginners, students and professionals can understand any Moon site and compare sites they choose.

**The problem.** NASA already has the data (JPL Horizons, LOLA) and map viewers (Quickmap, Moon Trek), but they are hard for non-specialists. None of them simply answers: is this a good time and place to be on the Moon, and how does it compare to another spot?

**The hard part.** Lighting near the lunar south pole. The Sun skims the horizon there, so a small ridge or crater rim can block it even when flat-ground math says it is up.

**Our product.** Pick one or more sites and a date range. The tool shows where the Sun and Earth sit in each site's sky, when each is visible, and a plain verdict, side by side.

### What counts as a good window

A good window is a time when both the Sun and Earth are above the site's real skyline.

| Condition | Why it matters | Rule |
| --- | --- | --- |
| Sun above the real skyline | Solar power and warmth | Sun clears the LOLA terrain profile, not just a flat horizon; count partial Sun disk separately |
| Earth above the real skyline | Direct radio link home, no relay needed | Earth clears the skyline by a user-set margin |
| Both at once | Best time to operate | The core "go window" |

What "good" means depends on the mission, so thresholds are user settings, not hard-coded. A solar lander cares most about Sun; a rover with a relay satellite may not need Earth.

### Numbers we report per site

- Percent of time sunlit
- Percent of time Earth is visible
- Percent of time with both
- Longest continuous stretch with both
- Longest dark stretch (what a lander must survive)

### Who it is for

| Audience | What they see first |
| --- | --- |
| Beginner | A calendar strip per site (green = both up, yellow = one up, red = neither) and a one-sentence verdict |
| Student | The sky view and frame chain explaining why the colors are what they are |
| Professional | Raw azimuth and elevation over time, window durations, export, and the exact Horizons query used |

### Team

| Member | Major | Owns |
| --- | --- | --- |
| Angel | Computer Science and Engineering | Data pipeline, website, UNO Q firmware, electronics |
| Gustavo | Mechanical Engineering | CAD: stepper Sun ring with lamp, printed terrain ring |
| Darren | Mechanical Engineering | CAD: servo arm showing Earth's wobble |

## How the math works

The observer stands on the Moon at the landing site; the Sun and Earth are what is being looked at. The same two direction arrows get re-described in three frames:

1. **Space frame (inertial).** Axes never rotate; everything moves. An ephemeris (JPL Horizons) gives where the Sun, Earth and Moon are.
2. **Moon-fixed frame.** Rotate by the Moon's orientation (a quaternion or rotation matrix, including libration, the Moon's slight rocking) so the Moon holds still. Now the Sun and Earth are directions sweeping around a fixed ball, and a site is just a latitude and longitude on it.
3. **Site frame (azimuth and elevation).** Project each direction onto the site's own east, north and up axes. Azimuth is the compass direction; elevation is height above the horizon. Only this frame answers power and radio questions.

The step from frame 2 to frame 3 is one dot product per axis, with **d** the unit direction to the Sun or Earth:

```latex
\text{elevation} = \arcsin(\mathbf{d} \cdot \mathbf{up}), \qquad \text{azimuth} = \operatorname{atan2}(\mathbf{d} \cdot \mathbf{east},\ \mathbf{d} \cdot \mathbf{north})
```

### Why the Sun and Earth move so differently

- **Sun:** circles the Moon once per lunar day (29.53 days) in the Moon-fixed frame.
- **Earth:** the Moon keeps the same face toward Earth, so Earth only wobbles a few degrees (libration).
- **Sun's latitude (lunar seasons):** the Moon's axis is tilted about 1.54°, so the Sun drifts between about +1.54° and −1.54° latitude over a roughly 346.6-day cycle. Within one lunar day it can shift up to about 0.8°, which matters a lot at the pole.

At the south pole, the Sun's height above a flat horizon is almost exactly its latitude, so the Sun circles the horizon at nearly constant height instead of rising and setting.

## Website walkthrough

The page has three controls, three graphs and a row of number cards; every graph shows the same Sun and Earth directions in a different frame.

### Controls

| Control | What it does |
| --- | --- |
| Site | Picks the landing site: South Pole, Shackleton crater rim, Malapert Mountain, or Apollo 11 (equator sanity check) |
| Day in lunar cycle | Moves the clock through one lunar day, 0 to 29.5 days |
| Season: Sun's latitude | Sets the Sun's latitude, −1.54° to +1.54°; held constant in the teaching model |

### Graph 1: the Moon, held still (globe)

This is frame 2. The Moon stays fixed while the Sun and Earth arrows move around it.

- **Gray ball with grid:** the Moon with latitude and longitude lines.
- **Black dot with a faint disc:** the site; the disc is its patch of flat ground, so it shows the horizon.
- **Orange arrow (Sun), blue arrow (Earth):** directions from the Moon's center. The bodies are so far away that the direction is nearly the same from anywhere on the Moon.
- **Solid vs. dashed:** solid means the body is on the camera's side; dashed and labeled "(behind)" means the far side.
- **Camera buttons:** above south pole, tilted, side-on. They change the view only, not the physics.

Drag the day slider: the Sun arrow sweeps a full circle, while the Earth arrow barely wobbles.

### Graph 2: sky at the site (strip)

This is frame 3, like a 360° panorama from the site unrolled flat.

- **Horizontal axis:** azimuth, N → E → S → W → N (both edges are north).
- **Vertical axis:** elevation from −12° to +14°, stretched on purpose because polar action happens within a few degrees of the horizon.
- **Thick line and gray area:** the horizon and the ground below it.
- **Dots:** Sun and Earth with their elevation. Faded = below the horizon. "(off scale)" = outside −12° to +14°, pinned to the edge.

### Graph 3: one lunar day at this site (timeline)

This plays the sky strip over a whole lunar day.

- **Horizontal axis:** days 0 to 29.5. **Vertical axis:** elevation, same stretched scale.
- **Orange curve:** Sun elevation. **Blue curve:** Earth elevation.
- **Black horizontal line:** the horizon; a curve above it means that body is visible.
- **Black vertical line:** the current day slider position.
- **Bars underneath:** meant to show sunlit and Earth-visible stretches (see Model limits for a bug here).

### Number cards

| Card | Meaning |
| --- | --- |
| Sun elevation | Sun height, azimuth, and a sunlit or night label |
| Flat-panel power | sin(elevation) × 100%: power for a panel lying flat, vs. full overhead Sun. About 2% at the pole, which is why polar landers use vertical panels that track the Sun around the horizon |
| Sunset in / Sunrise in | Time until the Sun crosses the horizon, assuming flat ground |
| Earth elevation | Earth height, azimuth, and "direct link OK" or "needs relay" |
| Earthset in / Earthrise in | Same idea for Earth; libration only, no terrain |

## Reading results at example sites

The same sky geometry gives very different answers depending on where you stand; values below come from the teaching model with a flat horizon.

| Site | Sun | Earth | Takeaway |
| --- | --- | --- | --- |
| South Pole | Circles the horizon at nearly constant height, set by the season (about +1.2° when the Sun's latitude is −1.2°) | Bobs between about −7° and +7°; up roughly half the time | Light depends on season and terrain; comms often need a relay |
| Malapert Mountain | Rises and sets a few degrees each day | Up most of the time; site is tilted 4° toward Earth | Better direct-to-Earth coverage than the pole |
| Apollo 11 (equator) | Normal day and night, far off scale | About 66° high, always up | Sanity check: a near-side site always sees Earth |

### Try it (predict first, then check)

1. South Pole: drag the season from −1.5° to +1.5°. Prediction: the Sun drops below the horizon for the whole day (polar night), and its globe arrow turns dashed.
2. South Pole: drag the day slider slowly. Prediction: only azimuth changes; elevation moves about 0.1°.
3. Apollo 11: Prediction: Earth never sets.
4. Malapert vs. South Pole: Prediction: Malapert sees Earth more often.

## Where NASA tools and our hardware fit

NASA's tools are ingredients, not the product; our website is the friendly layer over them, and the hardware is frame 3 made physical.

Pipeline: site + date → ephemeris → frame chain → Sun and Earth azimuth/elevation → horizon check against terrain → power and comms numbers.

### NASA tools

| Tool | What it really is | Role in our pipeline |
| --- | --- | --- |
| JPL Horizons | Ephemeris service; can return Sun or Earth azimuth and elevation for a lunar surface point over a time range | Core data source; Angel calls it (or Skyfield offline) and caches results |
| LOLA | Laser altimeter data of Moon surface heights | Turns a site into a skyline (azimuth vs. horizon height); Gustavo prints it as the terrain ring |
| Quickmap, Moon Trek | Map viewers for lighting, terrain and other layers | Reference to check our numbers against |
| Our website | Friendly front end over the pipeline | Site picker, date picker, sky diagram, metrics, compare view |

### Hardware model

| Part | Represents | Owner |
| --- | --- | --- |
| Stepper ring + lamp | Sun azimuth, 0° to 360°; at the pole the Sun mostly circles the horizon | Gustavo |
| Servo arm | Earth's few degrees of libration wobble | Darren |
| Printed terrain ring | The site's real LOLA skyline; shows why "Sun up" on flat math can still be blocked | Gustavo |
| Arduino UNO Q | Receives `SUN az el` and `EARTH az el` and drives the motors | Angel |

The physical model shows a judge in seconds why the pole is hard: a lamp circling low, blocked by the printed ridge.

## Model limits and known issues

The current page is a teaching model, not real ephemeris data; the real app replaces each simplification below.

| Simplification or issue | Effect | Real-app fix |
| --- | --- | --- |
| Sun's latitude held constant | Misses up to about 0.8° of drift per lunar day, enough to flip polar light on or off | Horizons data; or let the slider set a starting season and drift over the month |
| No terrain (flat horizon) | Says "sunlit" or "direct link OK" when a ridge may block the view | LOLA horizon profile per site |
| Sun treated as a point | Ignores the 0.5°-wide Sun disk being partly up | Report percent of disk visible |
| Simple libration swing (about ±6.7° latitude, ±7.9° longitude) | Earth's path is approximate | Horizons data |
| Approximate site coordinates | Small position errors | Use published site coordinates |
| Bug: "sunlit" bar on the timeline | The Earth bar is drawn over it, so it shows Earth visibility instead of sunlight; the curves are correct | Fix the bar drawing order and labels |

## Open questions

- [ ] Confirm the exact challenge statement and judging criteria for Challenge 11
- [ ] Pick the default Earth clearance margin and partial-Sun rule users start with
- [ ] Choose which sites ship in the demo, and get their published coordinates
- [ ] Decide whether to call Horizons live or cache results for the demo
- [ ] Pick the LOLA data product for skylines and how Gustavo turns it into a printable ring
- [ ] Fix the timeline's "sunlit" bar and add Sun-latitude drift to the teaching model
