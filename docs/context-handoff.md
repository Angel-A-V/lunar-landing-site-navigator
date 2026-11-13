# Context handoff: NASA Space Apps 2026, Challenge 11 (Lunar Landing Site Navigator)

This file summarizes a planning conversation so another assistant can pick up where it left off. It separates **decisions the team made** from **suggestions that are not yet confirmed**. Items marked **[verify]** come from general knowledge and must be checked before anyone depends on them.

---

## 1. Team

| Member | Major | Strengths | What they want from the project |
| --- | --- | --- | --- |
| Angel | Computer Science and Engineering (UC Merced, 5th year) | Software, web development | A hardware-focused challenge: electronics, embedded, integration. Owns all code. |
| Gustavo | Mechanical Engineering | CAD; no coding experience | Real mechanical design work for his resume |
| Darren | Mechanical Engineering | CAD; no coding experience | Real mechanical design work for his resume |

- The MEs will not write the main code. They may use their own AI agents for CAD scripting or small motor test sketches.
- **Time available: about 2 days, possibly less.** This is the main constraint now, and it drove the latest design cuts.
- Angel learns best with simple but detailed conceptual explanations.

---

## 2. The challenge (from the team's Project Plan, quoting the challenge PDF)

Missions to the lunar south pole must pick a **site** and a **date**. That choice decides:

- **Power:** how much sunlight the panels get. At the pole the Sun sits very low on the horizon.
- **Communication:** whether Earth is above the local horizon for a direct-to-Earth radio link.

NASA tools already exist (JPL Horizons, LROC Quickmap, Moon Trek, LOLA terrain data), but the challenge says they are "difficult for non-specialists to use effectively for rapid scenario comparison."

**MUST list (minimum viable product):**

- Pick from 3 to 5 curated sites, for example Shackleton crater rim, Malapert Mountain, Connecting Ridge, plus an Apollo site as a sanity check **[verify names and coordinates]**.
- Pick a date and time.
- Show Sun and Earth positions relative to the horizon.
- Show numbers: Sun elevation, time to sunset, Earth visible yes/no, time to Earthset.
- Compare two sites or two dates side by side.
- Explain the data sources inside the tool.

**SHOULD:** a timeline over one lunar day, custom coordinates input, a terrain-aware horizon (LOLA) for at least the main site, and an explanation mode for students.

**COULD:** a 3D view, rigorous libration modeling, automatic "best date" suggestions.

**Backup plan:** Challenge 3, "Junior Astronaut Mission Trainer," a kids' outpost-management game using DONKI and OSDR data. A go/no-go check decides whether to switch. If 2 or more of these answers are "no", switch:

1. Can Angel get correct-looking Sun and Earth azimuth/elevation for one site?
2. Does the stepper move to a commanded angle reliably?
3. Does everyone understand the MUST list?
4. Is the team on pace for the MUST list?

---

## 3. Project definition (decided by Angel)

Build an **easier tool on top of NASA's existing tools**, for beginners, students and professionals, to understand chosen Moon sites and compare them. The core question it answers: are the Sun and Earth above the horizon at this site and time? The **south pole lighting** is the hard part, because the Sun skims the horizon and terrain blocks it.

**Rule (from the Project Plan): the software must work without the hardware.** The website is what judges score. The physical model is a companion that makes the data tangible.

### "Good window" definition (suggested refinement, discussed with Angel)

A good window is when both the Sun and Earth are above the site's **real skyline** (terrain from LOLA), not just a flat horizon.

- Count a partly visible Sun disk separately; the disk is about 0.5° wide.
- Earth needs a user-set clearance margin above the skyline for a radio link.
- Thresholds should be user settings, because missions differ. A solar lander cares most about Sun; a rover with a relay may not need Earth.

Suggested per-site numbers:

- % of time sunlit
- % of time Earth is visible
- % of time with both
- longest continuous stretch with both
- longest dark stretch

### Audience layers (suggested)

| Audience | What they see first |
| --- | --- |
| Beginner | Calendar strip per site (green = both up, amber = one up, red = neither) and a one-sentence verdict |
| Student | Sky view plus the frame-chain explanation |
| Professional | Raw azimuth/elevation over time, window durations, CSV export, the exact Horizons query used |

---

## 4. The math (frame chain)

The observer stands at the landing site. The Sun and Earth directions are re-described in three frames:

1. **Space (inertial) frame:** an ephemeris (JPL Horizons, or Skyfield offline **[verify]**) gives Sun, Earth and Moon positions.
2. **Moon-fixed frame:** rotate by the Moon's orientation, including libration, so the Moon holds still. A site is a latitude/longitude.
3. **Site frame:** project the unit direction **d** onto the site's east, north and up axes:

```
elevation = asin(d · up)
azimuth   = atan2(d · east, d · north)
```

Key physical facts:

- **Sun:** circles the Moon once per lunar day (29.53 days) in the Moon-fixed frame.
- **Earth:** only wobbles a few degrees (libration), because the Moon keeps one face toward Earth.
- **Lunar seasons:** the Moon's axis is tilted about 1.54°, so the Sun's latitude on the Moon drifts between about +1.54° and −1.54° over about 346.6 days. Within one lunar day it can shift up to about 0.8°.
- **At the south pole:** the Sun's elevation above a flat horizon is roughly the negative of its latitude (Sun latitude −1.2° gives about +1.2° elevation). So the Sun circles the horizon at nearly constant height instead of rising and setting.
- **Flat-panel power:** roughly sin(elevation), so about 2% at the pole **[verify]**. Real polar landers use vertical panels that track the Sun's azimuth.

---

## 5. Current website: "Moon Sky Explainer" (teaching model, built earlier)

Link (claude.ai artifact, may not be accessible to you): https://claude.ai/artifact/T4NRv5LUhoz4NYVLKVnbVV. The HTML was also uploaded as `Moon_Sky_Explainer.html`.

It is a **simplified teaching model, not real ephemeris data**: no terrain, approximate site coordinates, and simple sine-based libration.

**Controls:**

- **Site:** South Pole (about −89.9°), Shackleton crater rim (about −89.7°, 129°), Malapert Mountain (about −86°, 0°), Apollo 11 (about 0.67°, 23.47°) as a sanity check.
- **Day in lunar cycle:** 0 to 29.5 days.
- **Season (Sun's latitude):** −1.54° to +1.54°, held constant through the month.

**Graphs:**

1. **Globe (frame 2):** the Moon held still. Sun (orange) and Earth (blue) arrows start at the Moon's center; dashed means behind the globe. Camera buttons only change the view.
2. **Sky strip (frame 3):** azimuth N, E, S, W, N on the x-axis; elevation from −12° to +14° (deliberately stretched). Faded dot means below the horizon; "(off scale)" means pinned at the edge.
3. **Timeline over one lunar day:** orange Sun curve, blue Earth curve, horizon line, a cursor at the current day, and sunlit/Earth-visible bars.
4. **Number cards:** Sun elevation and azimuth, flat-panel power, sunset/sunrise in, Earth elevation with "direct link OK" or "needs relay", Earthset/Earthrise in.

**Model parameters:** libration about ±6.7° in latitude (27.21-day period) and ±7.9° in longitude.

**Known issues and limits:**

- **Bug:** in the timeline, the Earth bar is drawn at the same y as the "sunlit" bar, after it. It erases the Sun bar, so the bar labeled "sunlit" actually shows Earth visibility. The curves are correct. The fix is to draw the bars at separate y positions and tidy the labels.
- Sun latitude doesn't drift through the month.
- No terrain (flat horizon).
- Sun treated as a point.
- Approximate coordinates.

**Expected behavior (sanity checks):**

- **South Pole:** Sun nearly constant height; Earth bobs between about −7° and +7°, up about half the time.
- **Malapert:** Earth up most of the time.
- **Apollo 11:** Earth about 66° high, always up.

### Target dashboard (mockup made, not built)

- Header with a Beginner/Student/Pro toggle.
- Controls: Site A, Site B, date, time (UTC).
- Two compare cards. Each has: a verdict badge, a sky strip with the terrain skyline, a 2x2 metric grid (Sun elevation, sunset in, Earth elevation, Earthrise/Earthset in), and a summary line ("Both up X% of lunar day · longest dark Y d").
- A lunar-day timeline card with 30 colored day cells per site and a legend.
- Footer listing data sources (JPL Horizons, LOLA), with "Export CSV" and "Horizons query" buttons.
- Data cached for offline use, because venue Wi-Fi is unreliable.

---

## 6. NASA tools and where they fit

| Tool | Role |
| --- | --- |
| JPL Horizons | Core ephemeris; can return Sun/Earth azimuth/elevation for a lunar surface point **[verify the API details]**. Cache results for demo sites and dates. |
| LOLA | Terrain heights, turned into a skyline (horizon profile) per site |
| Quickmap, Moon Trek | Map viewers; use them to check our numbers |
| Our website | The friendly layer over all of the above |

### Skyline (horizon profile) computation

For each azimuth (every 1° to 2°), march outward from the site across the LOLA height map, out to several tens of km. Compute this at each step:

```
angle = atan((h_terrain − h_site − d²/(2R)) / d)
```

Here d is the distance and R = 1737 km. Keep the maximum angle; that is the skyline angle for that azimuth. The curvature term matters: at 30 km, terrain sits about 260 m lower than it would on flat ground.

Output a CSV with columns `azimuth_deg, skyline_deg`.

---

## 7. Hardware inventory (summary)

- **Boards:**
  - Arduino UNO Q: Qualcomm Dragonwing QRB2210 running Linux, plus an STM32U585 MCU; 4 GB RAM, 32 GB eMMC; Wi-Fi and BLE; USB and 2x MIPI CSI camera support; LED matrix.
  - ELEGOO UNO R3.
  - A "Tiny" mini board, likely an ATtiny88 MH-Tiny clone **[verify the chip]**.
- **ELEGOO starter kit:**
  - Actuators and drivers: SG90 servo, 28BYJ-48 stepper + ULN2003 driver, DC motor + fan blade, 5V relay, active/passive buzzers, L293D, 74HC595, PN2222 transistors.
  - Sensors: HC-SR04 ultrasonic, DHT11, thermistor, 2 photoresistors, IR receiver + remote, joystick.
  - Inputs: 5 buttons, 10k potentiometer, tilt switch.
  - Displays: LCD1602, 1-digit and 4-digit 7-segment, 25 LEDs, 2 RGB LEDs.
  - Wiring and power: 830-point breadboard, jumper and Dupont wires, breadboard power supply module, 9V battery clip, 120 resistors, diodes.
- **Prototyping:** double-sided perfboards in 7x9, 5x7, 4x6, 3x7 and 2x8 cm.
- **Tools:** adjustable soldering iron kit (63/37 1.0 mm solder, desoldering pump, tweezers, heat shrink, cable ties), Jameco ReliaPro and Plusivo multimeters.
- **Fabrication:** Bambu Lab A1 3D printer, bed about 256 x 256 x 256 mm **[verify]**. Filament type and amount TBD.

---

## 8. Hardware design: how it evolved

1. **Original plan:** a lamp on a rotating Sun ring (stepper), an Earth pointer on a servo arm, a printed terrain ring around the center site, a base with an electronics bay, a photoresistor "power" reading, plus LCD, pot and buttons.
2. **The teammates wanted the surface to move, not the LED.** Both are physically valid, because only relative motion matters. A spinning surface under a fixed lamp is actually closer to reality: the Moon spins and the Sun stays roughly put.
   - Consequence: anything fixed to the Moon's surface (terrain, site, Earth pointer) must ride on the turntable.
   - Spin direction: seen from above, the surface turns clockwise (the Moon's spin seen over its south pole), so the Sun appears to move counterclockwise around the site **[verify against the app]**.
3. **Angel said the full version is too much to print and build in about 2 days.** It was cut to the version below.

### Current proposed design (two-day version, not yet confirmed by the team)

- **Rotating top (Gustavo):**
  - One printed disc, about 140 mm diameter, with the **terrain wall printed as part of it**: one part.
  - A site marker at the center, a small fixed Earth marker on the disc.
  - A press-fit socket onto the 28BYJ-48's D-shaft. Print a fit-test coupon first.
- **Fixed stand (Darren):**
  - The stepper mounted at the center, shaft up.
  - A fixed lamp tower outside the disc, with a slot to set its height once.
  - The disc support: a store-bought lazy susan bearing (about $5) or 3 printed skid pads.
  - Electronics in a foam-board or box base. Don't print the base.
- **Nothing electrical on the turntable.** There's no wire twisting, and the disc can spin forever.
- **Firmware:** turn the stepper to an angle and switch the LED on. The `SUN <az> <el>` command format stays; the firmware maps Sun azimuth to a disc angle.
- **Lowest-risk integration:** the website runs on a laptop and sends the azimuth to the UNO Q over USB. Hosting on the UNO Q is optional.
- **Stretch goals only:**
  - Earth libration servo
  - photoresistor power reading
  - lamp-height adjustment for seasons
  - LCD, pot, buttons
  - swappable terrain inserts for more sites
- **One site only for the demo:** South Pole or Shackleton. The model is accurate near the pole, where the Sun's height is nearly constant. Off-pole sites like Malapert would need a moving lamp height.

### Exaggeration formulas (same k for wall and lamp, so blocking is correct)

```
wall_height_above_sensor(az) = r_wall × k × tan(skyline_deg(az))
lamp_height_above_sensor     = r_lamp × k × tan(sun_elevation)
```

Example with r_wall = 70 mm and k = 10:

- A 2° skyline point becomes about 24 mm.
- A 1.5° Sun at r_lamp = 150 mm sits about 39 mm above the sensor.

Because tan is monotonic and the same k is used for both, the lamp clears the wall exactly when the real Sun clears the real ridge. Negative skyline angles (mountaintop sites) need the sensor or site marker raised on a pedestal, for example 15 mm. Gustavo can build the wall parametrically (OpenSCAD or CadQuery) from Angel's CSV.

### Ownership and shared interface numbers

| Gustavo | Darren |
| --- | --- |
| Disc + terrain wall, shaft socket, Earth marker | Stand, stepper mount, lamp tower, disc support, electronics box |

Agree on these first, ideally in one shared CAD skeleton file:

- disc diameter
- wall radius
- lamp distance and height
- shaft fit
- the stepper's position in the stand
- pedestal height (Gustavo picks it; it feeds his formula)

### Rough print list (times are guesses; check in Bambu Studio)

| Part | Owner | Rough time |
| --- | --- | --- |
| Shaft socket coupon | Gustavo | 10–15 min |
| Stepper mount | Darren | 45–90 min |
| Lamp tower | Darren | ~1 h |
| Earth marker | Gustavo | ~15 min |
| Disc + wall (print overnight, 0.28 mm draft layers) | Gustavo | 2–4 h |

Total about 5–7 h on one printer.

---

## 9. Build order (parallel tracks, not website-first)

The website and the hardware are built **in parallel**. They touch twice:

1. **Day 1:** Angel sends Gustavo the skyline CSV. A placeholder profile is fine.
2. **Day 2 morning:** the website drives the disc.

**Day 1**

- **First hour:** agree on the interface numbers and measure the stepper.
- **Morning:**
  - Angel: Sun data for one site, plus a stepper bench test.
  - Gustavo: socket coupon and disc CAD.
  - Darren: motor mount.
- **Afternoon:**
  - Angel: website MVP (the MUST list first).
  - Gustavo: finish the disc and wall.
  - Darren: lamp tower and disc support.
- **Night:** print the disc and wall.
- **Go/no-go check:** at Day 1 midday.

**Day 2**

- **Morning:** assemble, then integrate.
- **Afternoon:** polish, rehearse, and record a backup demo video.

**Angel's own priority order:**

1. data (it unblocks both the website and the wall)
2. website MUST list
3. tiny firmware
4. integration

**Fallback rule:** if the hardware isn't working by Day 2 midday, demo the website alone and turn the model by hand.

**If only 1 day:** cut the Earth marker and the lamp-height slot. Keep the disc, wall, stepper and LED.

---

## 10. Documents and pending work

**Existing documents (claude.ai links; contents summarized above):**

- **Hardware inventory:** https://claude.ai/artifact/QFE3GxpcQ24dqJnTwwpjmE. Also includes the team table and "what the project needs to offer".
- **Website guide and project definition:** https://claude.ai/artifact/9tCNdEFZze6hbFzp5G1ygw
- **Project Plan:** `Project_Plan___Lunar_Landing_Site_Navigator.md` (uploaded). It still describes the **original** hardware: a moving Sun ring and a servo Earth arm.

**Pending (offered but not done yet):**

- Rewrite the Project Plan to the two-day design: sections 1, 3, 4, 5A–5C and 6 change; the goal, MUST list, command format and backup plan stay.
- Fix the timeline "sunlit" bar bug and add Sun-latitude drift to the teaching model.
- Write an OpenSCAD or CadQuery script that turns the skyline CSV into the disc + wall part.

**Open questions:**

- the exact Challenge 11 judging criteria and Resources tab contents
- demo site(s) and published coordinates
- live Horizons calls vs. a cached dataset
- which LOLA data product to use for skylines
- default Earth margin and partial-Sun rule
- whether to buy a lazy susan bearing
- filament type and amount
- USB-C power and a monitor for the UNO Q
