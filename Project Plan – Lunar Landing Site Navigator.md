# Project Plan: Lunar Landing Site Navigator (Challenge 11), with a Challenge 3 Backup

Nov 6, 2026 · Team: Angel, Gustavo, Darren

This document explains what we are building and why, then gives each person their own section. Read sections 1 to 4 together as a team. Then each person reads their own section in section 5.

Companion file: `SpaceApps Hackathon – Hardware Inventory.md` (what we own).
Challenge texts: `NasaSpaceApps-Challenges/nasachall11.pdf` (primary) and `nasachall3.pdf` (backup).

Honesty note: facts taken from the challenge PDFs are marked as such. Everything else (part dimensions, pin numbers, links outside the PDFs, orbital numbers) is from general knowledge and must be verified before we depend on it. Those items are tagged **[verify]**.

---

## 1. The big picture

### What NASA is asking for (Challenge 11)

Missions to the Moon's south pole have a hard planning problem. Before landing, engineers must pick a **place** and a **date**. That choice decides two things:

1. **Power:** How much sunlight will the solar panels get? At the south pole the Sun sits very low on the horizon, so this changes a lot from site to site and day to day.
2. **Communication:** Can the lander talk directly to Earth? That depends on whether Earth is above the local horizon.

NASA tools that answer this already exist (Quickmap, Moon Trek, JPL Horizons), but the challenge says they are "difficult for non-specialists to use effectively for rapid scenario comparison." Our job is to build an **intuitive tool** where someone can:

- Pick a landing site (a list of known sites, or custom coordinates).
- Pick a date and time.
- See where the **Sun and Earth are relative to the horizon**.
- See key numbers: Sun elevation (power), sunlight duration, Earth visibility windows, and time left before sunset or Earthset.
- **Compare** several sites or dates quickly.

### What we are building

A two-part system:

| Part | What it is | Why |
| --- | --- | --- |
| **Software core** (web app) | A website that computes and shows the Sun and Earth positions for a chosen site and date, and compares scenarios. | This is what actually answers the challenge. Judges will score this first. |
| **Physical companion** (hardware) | A tabletop model of a south pole site. A lamp on a rotating ring is the Sun. A pointer on a small arc is Earth. The model moves in sync with the app. | This gives the mechanical engineers real design work and gives Angel real hardware work. It also makes the demo memorable. |

**Rule: the software must work without the hardware.** If the model breaks during judging, the web app alone still has to be a complete answer. The hardware is a companion that makes the data tangible. It is not a replacement for the tool.

### Why the hardware fits this challenge

At the lunar south pole the Sun never climbs far above the horizon. The Moon's axis is tilted only about 1.5 degrees **[verify]**, so the Sun mostly circles around the horizon instead of rising and setting like on Earth. That means:

- **Sun** = mainly a rotation (azimuth). One stepper motor on a turntable ring does this.
- **Earth** = a slow wobble within a few degrees, caused by libration (the Moon's slight rocking as seen from Earth). One servo on a small arc does this.

This matches the parts we already own: one stepper (28BYJ-48 with ULN2003 driver) and one SG90 servo.

---

## 2. Concepts you need (plain-language glossary)

| Term | Meaning |
| --- | --- |
| **Azimuth** | Compass direction of an object (0° = north, 90° = east). Which way to look. |
| **Elevation** | How high above the horizon an object is, in degrees. 0° = on the horizon, 90° = straight up. Negative = below the horizon, not visible. |
| **Ephemeris** | A table or calculation that says where a celestial body is at a given time. NASA's JPL Horizons system produces these. |
| **Libration** | The Moon's slight rocking, so Earth appears to wobble a few degrees in the lunar sky. It decides whether Earth is visible from places near the pole. |
| **Horizon mask / horizon profile** | The real skyline at a site, including mountains and crater rims. At the south pole terrain can hide the Sun even when the "flat" math says it is up. It comes from LOLA elevation data. |
| **LOLA** | Lunar Orbiter Laser Altimeter. A NASA instrument that measured the Moon's surface heights. Its data is used to build terrain and horizon profiles. |
| **Direct-to-Earth (DTE) communication** | A radio link straight to Earth. It works only when Earth is above the local horizon. Otherwise a relay satellite is needed. |
| **CLPS** | Commercial Lunar Payload Services. NASA's program that buys commercial lunar landers. Many "notable sites" in the challenge come from it. |
| **Solar elevation vs. power** | A flat panel's power is roughly proportional to the sine of the Sun's elevation **[verify]**. Low Sun means low power. Real missions often tilt or stand panels vertically for this reason. |
| **Lunar day** | About 29.5 Earth days from one sunrise to the next. Challenge text: "across different lunar days or seasons". |

---

## 3. What a successful submission contains

From the challenge text, ranked by importance. "Must" items are what we treat as the minimum.

### MUST (minimum viable product)

- [ ] Choose from a **curated list of 3 to 5 sites** (for example Shackleton crater rim, Malapert Mountain, Connecting Ridge, and one Apollo site as a sanity check **[verify names and coordinates]**).
- [ ] Choose a **date and time**.
- [ ] Show **Sun and Earth positions relative to the horizon** (a simple sky/horizon diagram is enough).
- [ ] Show **numbers**: Sun elevation, time to sunset, Earth visible (yes/no), time to Earthset.
- [ ] **Compare** two sites or two dates side by side.
- [ ] Explain the data sources inside the tool.

### SHOULD

- [ ] A **timeline** over one lunar day showing sunlight and Earth-visibility windows.
- [ ] **Custom coordinates** input.
- [ ] A terrain-aware horizon (LOLA) for at least the main demo site.
- [ ] A simple explanation mode for students and the public ("why does the Moon's south pole have such weird lighting?").

### COULD (stretch)

- [ ] 3D surface view.
- [ ] Libration and orbital variation accounted for rigorously.
- [ ] Many sites and automatic "best date" suggestions.

### Physical model deliverables (our own resume outputs)

- [ ] Working model: Sun ring (stepper) and Earth arm (servo) that follow the app.
- [ ] CAD models and drawings of all printed parts.
- [ ] Print iteration log (v1, v2, v3 with photos and what changed).
- [ ] Wiring schematic and a soldered perfboard circuit.
- [ ] A 2 to 3 minute demo script.

---

## 4. Architecture and the contract between us

```
 Browser (web app, Angel)
      │  HTTP / WebSocket over Wi-Fi
      ▼
 ┌─────────────── Arduino UNO Q ───────────────┐
 │ Linux side (Python):                         │
 │   - ephemeris math (Sun/Earth az/el)         │
 │   - serves the web app                       │
 │   - sends motor commands                     │
 │            │ Bridge (Linux ↔ MCU) [verify]    │
 │ MCU side (STM32, Arduino sketch):            │
 │   - drives stepper + servo in real time      │
 │   - reads pot, buttons, photoresistor        │
 └──────────────────────────────────────────────┘
        │ wires                    │ wires
   Stepper (Sun ring)         Servo (Earth arm)
   Lamp + photoresistor       LCD1602 + controls
```

### The interface contract (agree on this in the first hour)

This is the most important thing for a mixed ME and software team. Fill in the blanks together and then do not change it without telling everyone.

| Item | Decision | Owner |
| --- | --- | --- |
| Overall model footprint (max size, must fit on the A1 bed in parts, about 256 × 256 × 256 mm **[verify]**) | ___ | Gustavo and Darren |
| Stepper: 28BYJ-48, 5 V, ~28 mm body. Measure with calipers and record in CAD. | ___ | Gustavo |
| Servo: SG90, record real dimensions and horn spline. | ___ | Darren |
| Sun ring motion: **360° azimuth**, how many degrees per stepper step after gearing | ___ | Gustavo |
| Earth arm motion range: **± ___°** | ___ | Darren |
| Home position for the Sun ring: a push button as a limit switch, location | ___ | Gustavo and Angel |
| Wire exit points and where the electronics bay is | ___ | Darren and Angel |
| Power: the kit's breadboard supply, **not** the UNO Q pins, for the motors | ___ | Angel |
| Command format (see below) | as below | Angel |

### Command format (draft)

Plain text lines over serial or the UNO Q Bridge:

```
SUN <azimuth_deg> <elevation_deg>     e.g.  SUN 215.0 1.2
EARTH <azimuth_deg> <elevation_deg>   e.g.  EARTH 30.0 -2.5
HOME                                  move Sun ring to the home switch, zero position
STATUS                                reply with positions and photoresistor reading
```

Why this helps: the MEs can test their mechanisms with a small sketch that sends fixed `SUN` and `EARTH` commands, with no need to wait for the web app.

---

## 5. Assignments by person

### 5A. Angel (Computer Science and Engineering): electronics, firmware, web app

**Your role:** you own all code, the circuit, and the integration. You are the one connecting the data to the hardware.

**Work packages**

1. **Ephemeris engine (the core of the challenge).**
   - Goal: given site latitude/longitude and a time, output the Sun's and Earth's azimuth and elevation as seen from that spot on the Moon.
   - Approach options: JPL Horizons has a web API that can compute this for a lunar surface observer **[verify]**. Or use a Python library such as Skyfield with a downloaded ephemeris file for offline use **[verify]**.
   - Venue Wi-Fi is unreliable. **Precompute and cache** the results for your demo sites and date ranges so the demo works offline.
2. **Horizon / terrain.**
   - Start with a flat horizon (Sun is up if elevation > 0).
   - Then add real terrain from LOLA-derived data for the main demo site. The challenge specifically calls out LOLA.
   - If time is short, use a precomputed horizon profile (a list of azimuth, skyline elevation pairs) for 2 to 3 sites.
3. **Web app.**
   - Site picker, date/time picker, horizon diagram, metrics panel (Sun elevation, time to sunset, Earth visibility), side-by-side comparison, timeline over a lunar day.
   - Keep it simple and fast. A good-looking compare view beats extra features.
4. **Firmware (MCU side).**
   - Stepper control through the ULN2003 (use a proper stepper library or a simple half-step table).
   - Servo control.
   - Homing routine using a push button as a limit switch.
   - Read the potentiometer (timeline scrub), buttons (site select) and photoresistor.
   - LCD1602: show site name, "Sunset in X h" and "Earth visible: YES/NO".
5. **Circuit.**
   - Breadboard first, then solder to perfboard (the 7×9 cm board is the likely candidate).
   - Add a flyback diode and a transistor if driving the DC motor or relay. Keep motor power separate from logic power.
   - Produce a wiring schematic (a resume output).

**Suggested pin map (draft, use it only after checking the UNO Q pinout [verify])**

| Function | Suggested connection |
| --- | --- |
| Stepper driver IN1 to IN4 | 4 digital pins |
| Servo signal | 1 PWM-capable pin |
| Home switch | 1 digital pin with pull-up |
| Pot (timeline scrub) | 1 analog pin |
| Photoresistor (with resistor divider) | 1 analog pin |
| Site-select buttons (2) | 2 digital pins |
| LCD1602 | 6 digital pins (4-bit mode) or I2C if you add a backpack |

**How to use your agent well:** give it the interface contract (section 4) and ask for small testable pieces first: "stepper moves N degrees," then "reads pot," then "parses `SUN 215 1.2`," before the big app. Commit often.

**Learn first (links):** see section 7 (Resources). Most important: JPL Horizons documentation, UNO Q getting-started page (`arduino.cc/uno-q`, already in the inventory file), and a stepper-with-ULN2003 tutorial.

**Your resume outputs:** wiring schematic, soldered perfboard, working firmware, ephemeris and web app, integration demo.

---

### 5B. Gustavo (Mechanical Engineering): the Sun mechanism

**Your role:** design, print and iterate the part of the model that represents the Sun, plus the terrain ring that shows the real skyline.

**Work packages**

1. **Sun turntable and drive train.**
   - A ring or turntable that carries a lamp (an LED) through 360° of azimuth.
   - Driven by the 28BYJ-48 stepper. That stepper already has an internal gearbox (about 64:1 **[verify]**), so think about whether you need extra gearing. A printed gear stage is a good ME exercise if you want finer motion or a larger ring.
   - Design a **bearing surface**: the ring must rotate smoothly and not wobble. Options: printed roller guides, or a thrust-bearing arrangement. Tolerance and fit matter here.
2. **Home switch mount.**
   - A push-button limit switch the ring touches at its zero position, so the software can find "north" every time it powers up.
3. **Terrain silhouette ring.**
   - A printed ring whose top edge is the **real skyline** (horizon profile) of the demo site, scaled down. Angel will give you the azimuth/elevation list from LOLA data.
   - This is a great resume piece: it turns real data into a physical part. Exaggerate the vertical scale and label it.
4. **Lamp carriage.**
   - Holder for the lamp LED and for wire routing.
5. **Documentation.**
   - Drawings with dimensions and tolerances, an assembly view, and your print iteration log.

**Constraints to design around**

- The stepper has low torque. Keep the ring and lamp **light**. Use thin walls, ribbing, and print in a light infill.
- Print each part to fit the A1 bed (about 256 mm per side **[verify]**). If your ring is larger, split it into segments with locating features.
- Printed fits: allow clearance (for example 0.2 to 0.3 mm **[verify against your A1 and filament]**). Test with small coupons before printing a big part.

**Coordinate with:** Darren (shared base and electronics bay), Angel (home switch wiring, lamp wires, step count).

**Learn first:** see section 7. Focus on printed-part tolerancing, gear design basics, and how the 28BYJ-48 is mounted (its mounting ears and shaft).

---

### 5C. Darren (Mechanical Engineering): the Earth mechanism and the base

**Your role:** design the Earth pointer, the lunar surface base, the electronics bay and the cable routing. You also integrate everything physically.

**Work packages**

1. **Earth arm.**
   - A pointer or small sphere on an arm driven by the SG90 servo through a few degrees of motion, representing Earth's position (libration wobble).
   - Design the linkage or direct mount, the servo bracket, and the arm's range of motion. Include **hard stops** so a software bug cannot break the mechanism.
   - Think about exaggeration: the real motion is small. Pick a scale, add a mechanical advantage if needed (a printed lever or gear), and label it on the model.
2. **Base and lunar surface.**
   - A sturdy base that holds both mechanisms. Surface texture can look like regolith and craters (decorative, but it makes the demo).
   - The base must carry loads and stay stable while the ring turns.
3. **Electronics bay.**
   - A compartment for the UNO Q, perfboard, breadboard power supply, and LCD1602 window. It needs access for USB, power, and reflashing.
   - Vent holes and strain relief for cables.
4. **Cable routing through the rotating Sun ring.**
   - Wires to the lamp must cross a rotating joint. Options: limit rotation to slightly less than 360° and use a coiled/slack wire, or design a slip path. This is a real mechanical challenge and a great resume point.
5. **Photoresistor fixture.**
   - A holder under or beside the model that measures light from the lamp, so the model shows a live "solar power" reading. Shield it from room light.
6. **Documentation.**
   - Drawings, exploded assembly view, and your print iteration log.

**Constraints**

- The SG90 is small and weak. Keep the arm light. Check horn size and mounting-tab geometry with calipers **[verify]**.
- Make every part removable without cutting wires, so Angel can debug.

**Coordinate with:** Gustavo (shared base, mounting points), Angel (wire exits, connector locations, bay size).

---

### Shared MEs: how to use your own agents

Gustavo and Darren said they are fine using their own agents. Good uses:

- Parametric CAD scripting (for example OpenSCAD or CadQuery) for gears, rings, and mounts, so dimensions are easy to change.
- Quick bring-up sketches that move the stepper and servo through test angles. Agree with Angel on where these live so they do not conflict with his main firmware.
- Writing a clean README for your CAD (parts list, print settings, assembly order).

Keep all main code (ephemeris, web app, main firmware) with Angel and his agent to avoid merge problems.

---

## 6. Plan, checkpoints, and when to switch to the backup

Event length is not stated in the files, so these are relative phases. Adjust to the real schedule.

| Phase | Everyone | Angel | Gustavo | Darren |
| --- | --- | --- | --- | --- |
| **0. Kickoff (first hour)** | Read this file. Fill in the interface contract. Measure real parts with calipers. | Check the UNO Q boots and runs a blink. | Measure stepper. Sketch ring concept. | Measure servo. Sketch base and arm concept. |
| **1. Prove the core** | | Get Sun az/el for ONE site and date from the ephemeris. Move the stepper to match. | Print v1 of the turntable. | Print v1 of the arm and a base mock-up. |
| **2. Build the MVP** | | Web app with site/date picker, horizon diagram, metrics. | Iterate ring. Add home switch. | Iterate arm. Build electronics bay. |
| **3. Integrate** | Assemble model, run end to end. | Compare view, LCD, pot, perfboard. | Terrain ring. | Cable routing, photoresistor fixture. |
| **4. Polish and rehearse** | Demo script, submission write-up, attribute data sources. | Fix bugs. Offline cache. | Final prints and drawings. | Final prints and drawings. |

### Go / no-go checkpoint (end of Phase 1)

Ask these questions together. If **two or more** answers are "no", switch to the backup (Challenge 3):

1. Can Angel get correct-looking Sun and Earth azimuth and elevation for one site from the ephemeris?
2. Does the stepper move the ring to a commanded angle reliably?
3. Does everyone understand what the app must show (section 3 MUST list)?
4. Are we on pace for the MUST list, not just the stretch items?

Do not wait until late to decide. Switching late wastes both options.

---

## 7. Resources

### From the challenge PDFs (these are in the files you gave me)

- Challenge 11 page: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/
- Challenge 3 page: https://www.spaceappschallenge.org/2026/challenges/junior-astronaut-mission-trainer/
- Space Apps resources hub: https://www.spaceappschallenge.org/resources/
- **The "Resources" tab on each challenge page.** The PDFs say "For data and resources related to this challenge, refer to the Resources tab," and that more may be added before the hackathon. The PDFs do not contain that tab's contents, so **open it in a browser and check it first**.

Tools and datasets named in the challenge text:

| Name | Used for | Challenge |
| --- | --- | --- |
| JPL Horizons System | Ephemeris: Sun and Earth positions | 11 |
| NASA Quickmap, Moon Trek | Existing tools that show lunar data (study them, then do better) | 11 |
| LOLA (Lunar Orbiter Laser Altimeter) | Lunar terrain and horizon accuracy | 11 |
| DONKI (Space Weather Database) | Solar activity and radiation risk | 3 |
| OSDR (Open Science Data Repository) | Astronaut radiation and biology data | 3 |

### Links I know from general knowledge (verify each before relying on it)

- JPL Horizons: https://ssd.jpl.nasa.gov/horizons/ and its API docs
- LROC QuickMap: https://quickmap.lroc.im-ldi.com/
- NASA Moon Trek: https://trek.nasa.gov/moon/
- DONKI: https://kauai.ccmc.gsfc.nasa.gov/DONKI/ and NASA's open API portal https://api.nasa.gov/
- OSDR: https://osdr.nasa.gov/
- Skyfield (Python astronomy library): https://rhodesmill.org/skyfield/
- Arduino UNO Q: https://arduino.cc/uno-q

### Suggested things to look up (search terms)

- For Angel: "28BYJ-48 ULN2003 Arduino tutorial", "Arduino UNO Q Bridge Python sketch", "JPL Horizons API lunar surface observer", "Skyfield Moon topocentric".
- For the MEs: "printed gear tolerance 3D printing", "turntable bearing 3D printed", "28BYJ-48 mounting dimensions", "SG90 servo dimensions", "Bambu A1 tolerance clearance".
- For everyone: "lunar south pole illumination Shackleton", "Moon libration Earth visibility".

---

## 8. Backup plan: Challenge 3, Build a Junior Astronaut Mission Trainer

### What it asks (from `nasachall3.pdf`)

Build an interactive game or app where **kids ages 7 to 12** run a lunar or Martian outpost. They balance **life support, radiation shielding, power, food production, and communication delay**. Every choice must cost something (no "safe" option). Use **real NASA data** where possible (DONKI for solar activity and radiation risk, OSDR for astronaut biology, Artemis and Mars surface data for conditions). Clearly show data sources inside the tool.

What the challenge says makes a solution stand out:

- Real-world consequences tied to real data (for example, shielding decisions that respond to actual current space weather).
- Replayability (events that change between playthroughs).
- A short explanation of which datasets were used and why.

What it warns against:

- A "safe" choice with no cost.
- Pretty visuals instead of accurate mechanics.
- Too many resources. **Stick to 2 or 3** (power, life support, shielding).

### How we would use the same hardware

| Game element | Physical part | Who builds it |
| --- | --- | --- |
| Solar array | Servo-driven deployable or folding array on the outpost model | Darren |
| Radiation shield | Sliding or raising shield panel (servo or stepper) | Gustavo |
| Life support | Fan (DC motor and fan blade) switched through a transistor or L293D with a diode | Angel (electronics), Darren (housing) |
| Power budget | Pot or joystick lets the player split power between systems | Angel |
| Alerts | Buzzer plus RGB LEDs | Angel |
| Status | LCD1602 shows day and resources | Angel |
| Game logic and NASA data | Web app on UNO Q (DONKI for space weather events) | Angel |

### What carries over from Challenge 11 if we switch

- **All of Angel's electronics work**: UNO Q setup, perfboard, LCD, controls, stepper and servo firmware, web app skeleton.
- **The base and electronics bay** (Darren).
- **Gustavo's stepper mount and bearing/gear design knowledge**, reused for the shield mechanism.

The switch loses the ephemeris engine and the Sun ring and terrain ring. That is why we decide early (section 6).

### Backup MUST list

- [ ] A game where the player manages **2 to 3 resources** over a simulated mission with real trade-offs.
- [ ] At least **one NASA dataset** (for example DONKI) driving an in-game event.
- [ ] Plain language for ages 7 to 12.
- [ ] A short written explanation of the datasets used.
- [ ] A physical outpost model with at least one moving mechanism tied to the game.

---

## 9. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Ephemeris math is harder than expected | Use the web API or a library, not hand-written orbital math. Precompute data for the demo sites. |
| Venue Wi-Fi fails during judging | Cache all data offline. Run the app locally on the UNO Q. |
| Stepper or servo too weak | Keep moving parts light. Test with a dummy load early. |
| Printed parts fail fits | Print small test coupons first. Keep iteration logs (also a resume output). |
| Hardware breaks mid-demo | Software must work alone. Keep a screen-recorded backup demo. |
| Team misunderstands the goal | Everyone reads sections 1 to 3 and can explain them in one minute. |
| Scope creep | Build the MUST list first. Add SHOULD and COULD items only after it works. |

---

## 10. Open questions to settle early

- [ ] Which 3 to 5 sites and exact coordinates **[verify]**
- [ ] Is a USB-C power supply available for the UNO Q? Any monitor or camera?
- [ ] Filament type, colors and amount (from the inventory "To confirm" list)
- [ ] Do we buy 2 to 3 extra SG90 servos and an LED strip? (Optional and cheap. The plan works without them.)
- [ ] Read the Resources tab for Challenge 11 and Challenge 3 and add any links found here.
