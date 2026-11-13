# How the Calculations Work (a learning guide)

Written 2026-11-13 for Angel, Gustavo and Darren. **Nothing here is code to copy.** It explains what each calculation does and why, using real numbers from our own data, so you can design the dashboard and check what anyone's tools or AI agents produce.

All numbers are for the working Shackleton rim pick (-89.781, 203.743 E), which is **not** an official landing site [verify].
Companion: `software-architecture.md` (the stack and the plan).

---

## 0. The big picture in four sentences

1. Stand at a spot on the Moon. NASA tells us *which direction* the Sun and Earth are in (two angles each).
2. NASA's terrain data tells us *how high the land blocks the view* in every direction (the skyline).
3. A body is visible when it sits **above the skyline** in its direction.
4. Sunset or Earthset is the moment it sinks below the skyline, and we find that moment by looking for a sign change.

Everything else (percentages, compare, timeline, 3D) is built from those four ideas.

---

## 1. Vocabulary (the only words you need)

| Word | Meaning | Example from our data |
|---|---|---|
| **Azimuth (az)** | Compass direction you look. 0° = north, 90° = east, 180° = south, 270° = west. Wraps around: 359° and 1° are 2° apart. | Sun az 331.66° (north-west) |
| **Elevation (el)** | Angle above the flat horizon. 0° = level, 90° = straight up, negative = below level. | Sun el +1.737° |
| **Flat horizon** | The imaginary level plane at the site, ignoring hills. Horizons measures against this. | |
| **Skyline** | In each azimuth, the highest elevation reached by terrain. A body must be higher than this to be seen. | Skyline at az 331.66° is -1.219° |
| **Margin** | body elevation minus skyline at the body's azimuth. Positive = visible. | Sun margin = 1.737 - (-1.219) = **+2.956°** |
| **Libration** | The Moon's slight rocking, which makes Earth drift a few degrees up and down in the sky. | Earth el ranges about -7.3° to +6.4° over a year |
| **Ephemeris** | A table of where a body is over time. | Horizons output |
| **Interpolation** | Estimating a value *between* two table rows by blending them. | See Step 2 and Step 4 |

---

## 2. Where each input comes from

**From NASA Horizons** (we do not compute this; see `fetch_horizons.py`): for each hour, `sun_az, sun_el, earth_az, earth_el`. Horizons did the heavy frame maths: Sun/Earth positions in space, the Moon's orientation including libration, and conversion to this spot's local east/north/up. We just ask it as "an observer standing on the Moon at these coordinates."

**From NASA LOLA** (terrain heights): a height map of the south pole at 20 m per pixel. From it we build the skyline, below.

---

## 3. Building the skyline (what `make_skyline.py` does)

Goal: one number per compass direction: the highest elevation angle at which land blocks the view.

**Plain-language recipe**, repeated for each azimuth 0°, 1°, ... 359°:
1. Start at the site. Walk outward in that compass direction in 40 m steps, up to 35 km.
2. At each step, look up the ground height there from the height map. (Heights between pixels are blended; this is called bilinear interpolation.)
3. For each step, work out the **angle you would have to look up** from the site to see that ground point.
4. Keep the **largest** angle over all steps. That is the skyline for this azimuth. Why the largest: the biggest hill in the way is the one that hides everything behind it.

**Step 3 is the interesting part, because the Moon is a ball.** Land far away curves downward. The script puts the Moon's centre at the origin and treats the site and the target point as two points on or above a sphere of radius R = 1,737,400 m:
- The far point is `d / R` radians around the Moon from the site (call that angle θ).
- Measured from the site: how far *outward* is it, and how far *up* is it?
  - out = (R + height_there) × sin θ
  - up  = (R + height_there) × cos θ − (R + height_at_site)
- The look-up angle is the angle whose "rise over run" is up / out.

**Check you can do in your head:** flat land at the same height as the site, 35 km away. θ = 35,000 / 1,737,400 = 0.0201 rad. Curvature alone makes that ground sit about d/(2R) = 0.0101 rad = **0.58° below** the flat horizon. So even featureless land shows as negative at long range, and a hill must rise more than that to count. This is why our rim pick has a **negative** skyline in 344 of 360 directions: we stand high and the ground curves and falls away.

**What you get for our pick:** highest +1.04° (az 31°), lowest -2.92° (az 293°), mean -1.24°.

**Limits to remember** (they matter for the dashboard):
- Range is 35 km, so farther peaks are ignored.
- Azimuth step is 1°, so thin spikes between directions can be missed.
- The terrain map's resolution is 20 m.

---

## 4. Looking up the skyline at any azimuth (Step 2)

The Sun's azimuth is a decimal like 331.6598°, but the skyline table has whole degrees. Blend the two neighbours:

```
a  = az mod 360            # wrap into 0..360 (so 361 becomes 1)
i  = whole part of a       # 331
f  = a - i                 # how far toward the next row: 0.6598
skyline(a) = row[i] × (1 - f)  +  row[i+1 mod 360] × f
```
Line by line: `mod 360` handles wrap-around; `i` is the row just below; `f` is the blending weight (0 means use row `i`, 1 means use row `i+1`); the last line mixes them; `mod 360` on `i+1` makes row 359 blend with row 0.

**Real numbers:** row 331 = -1.240, row 332 = -1.208, f = 0.6598.
-1.240 × 0.3402 + (-1.208) × 0.6598 = **-1.2189°**. Matches the value used in the margin example.

---

## 5. The visibility test

```
margin = body_elevation - skyline(body_azimuth)
visible = margin > 0
```
That is the whole test. Two real rows from the cache (2026-11-10 00:00 UTC):

| Body | az | el | skyline there | margin | visible |
|---|---|---|---|---|---|
| Sun | 331.66° | +1.737° | -1.219° | **+2.956°** | yes |
| Earth | 159.69° | -7.019° | -0.928° | **-6.091°** | no |

Margin is the number a dashboard should be built around: its **sign** says visible or not, and its **size** says how safely.

---

## 6. Finding sunset or Earthset (the sign-change search)

The table is hourly but events happen between rows. The method:

1. Compute the margin for every row.
2. Scan forward from "now" and find the first pair of neighbouring rows where the margin **changes sign**: positive then negative is a *set*, negative then positive is a *rise*.
3. The event is somewhere between those two rows. Assume the margin changes in a straight line over that hour (reasonable, since it is slow) and find where the line crosses zero:

```
m0 = margin at the earlier row      m1 = margin at the later row
fraction = m0 / (m0 - m1)           # 0 = at the earlier row, 1 = at the later row
event_time = earlier_time + fraction × (time step)
```
Why this works: the line from m0 to m1 reaches zero after `m0 / (m0 − m1)` of the way across.

**Real event: Earthrise at our pick, found in the 30-day cache.**

| Time (UTC) | Earth az | Earth el | skyline | margin |
|---|---|---|---|---|
| 2026-11-17 00:00 | 151.040° | -1.158° | -1.128° | **-0.031°** |
| 2026-11-17 01:00 | 150.993° | -1.101° | -1.129° | **+0.029°** |

Sign changed from − to +, so Earth **rises**. fraction = -0.031 / (-0.031 - 0.029) ≈ 0.52, so about **31 minutes** after midnight: Earthrise ≈ **2026-11-17 00:31 UTC**.

**Sunset** is the same procedure with the Sun's margin. In the 30-day cache the Sun never drops below the skyline (no sign change). Over the 365-day cache it does, with 60 sign changes. The first sunset falls on 2027-02-01 (6-hour sampling, so only roughly).

### 6b. The most important lesson for dashboard design: sensitivity

Look at that table: Earth's margin changes by only **about 0.06° per hour**. So:
- An error of **0.1°** in the skyline shifts Earthrise by about **1.7 hours**.
- An error of **1°** would shift it by about **17 hours**.

Our skyline has a 1° azimuth step, 20 m terrain and a 35 km range, so event times for slow-moving bodies at the pole are only as good as those limits. The Sun is treated as a point, but the real Sun is a half-degree disc, which moves sunset later still. **A dashboard should therefore show event times as "about" values or as a range, not as exact minutes.** The skyline, not the ephemeris, is the weak link in accuracy.

---

## 7. Times between table rows (Step 4)

When the user picks 13:47, blend the two hourly rows around it the same way as the skyline lookup in section 4:
```
f = (picked_time - earlier_row_time) / (later_row_time - earlier_row_time)
value = earlier × (1 - f) + later × f
```
For **azimuth** be careful at the wrap: between 359° and 1°, blend through 360°, not backwards through 180°. (Common bug: averaging 359 and 1 gives 180.) Elevation has no wrap.

---

## 8. Percentages and windows

- **Sunlit percentage** = rows with margin > 0, divided by all rows.
- **Both up** = rows where Sun margin > 0 **and** Earth margin > 0 at the same time (power and a radio link).
- **Longest dark stretch** = longest run of consecutive rows with Sun margin ≤ 0.

Rough yearly results for the pick (Sun as a point, Earth with no safety margin): Sun about **80%** (54% on a flat horizon), Earth about **51%**, both about **41%**. In the same cache, the longest Sun-dark run came out around **414 hours (about 17 days, at 6-hour sampling)**, ending 2027-05-06.

**Flag to investigate, not a conclusion:** published work reports a best Shackleton-area spot with only about 1.5 days of darkness at its longest (Mazarico et al. 2011). That is a different, better-chosen spot, so it need not disagree with ours, but we should check our 17-day figure against NASA's maps before trusting it. This is exactly the sort of number the verification step must test.

---

## 9. Compare two sites or dates

Run the same steps for A and B and put the results side by side. Nothing new to calculate; the dashboard job is showing differences clearly.

---

## 10. What a dashboard can show (the full list of quantities)

| Quantity | Type | Range / values | What it means to a user |
|---|---|---|---|
| Sun / Earth azimuth | angle | 0 to 360° | Which way to look |
| Sun / Earth elevation | angle | about -7° to +7° here | How high above level |
| Skyline at that azimuth | angle | about -3° to +1° here | How high the land blocks |
| **Margin** | angle | negative to positive | Safely visible? (sign and size) |
| Visible | yes/no | | Sun or Earth in view |
| Time to sunset / Earthset (or rise) | duration | minutes to days | How long until it goes |
| Sunlit % / Earth % / both % | percent | 0 to 100 | Overall usefulness of the site |
| Longest dark run | duration | | Battery planning |
| Event uncertainty | duration | hours at the pole | Honest "about" |

Four states a diagram should make obvious: **Sun up / down** and **Earth up / down**, plus "both up" (best) and "neither" (worst).

---

## 11. Reviewing what the AI agents produce (checklist for the team)

If someone prompts an agent to write this, check these before trusting it:

1. **Azimuth wrap-around:** does 359.9° vs 0.1° work? Is blending done through 360?
2. **Degrees vs radians:** trig functions use radians; data is in degrees. A mixed-up unit gives smooth but wrong numbers.
3. **Convention:** azimuth 0 = north, 90 = east (clockwise from north). Not math-class convention.
4. **Sign of margin and direction of events:** positive → negative is a set, negative → positive is a rise.
5. **Skyline is "highest angle", not "average".**
6. **Time zone:** everything is UTC.
7. **Interpolating at the table edges** (first and last row) does not crash.
8. **Does it show NASA's raw numbers next to its own result?**
9. **Test with made-up data first:** flat skyline at 0°, a Sun that climbs from -1° to +1°; the sunset must land at the exact crossing time.

---

## 12. Try it by hand (to be sure you understand)

Use a calculator and the table in section 6.
1. **Margin:** Earth at 02:00 on 2026-11-17 has el -1.043° and skyline -1.131°. What is the margin, and is Earth visible? (Answer: +0.088°, yes.)
2. **Crossing fraction:** with margins -0.031° and +0.029°, confirm the fraction is about 0.52.
3. **Sensitivity:** if the skyline were 0.2° higher in that direction, would Earthrise be earlier or later, and by roughly how much at 0.06° per hour? (Answer: later, by about 3.3 hours.)
4. **Skyline blend:** az 331.2° with rows 331 = -1.240 and 332 = -1.208. (Answer: -1.2336°.)
5. **Curvature:** flat land 10 km away at the site's height. Roughly how far below level does it appear? (Answer: d/(2R) = 10,000 / 3,474,800 ≈ 0.0029 rad ≈ 0.16°.)
