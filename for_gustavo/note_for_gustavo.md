# Note for Gustavo: the horizon wall

From Angel, 2026-11-10. Attached: `skyline_shackleton_rim.csv`.

## What the wall is
The wall is the **horizon** as seen by someone standing at the landing site. It is not a model of the terrain. The disc surface can be flat and plain. Only the top edge of the wall has to be accurate, because that edge decides when the lamp (the Sun) and Earth disappear behind the ridge.

## The CSV
- 360 rows, one per degree of compass direction: `azimuth_deg, skyline_deg`.
- `azimuth_deg`: 0 = north, 90 = east, clockwise when seen from above.
- `skyline_deg`: the angle the ground reaches above (+) or below (−) flat from the observer's eye. Negative means the ridge is below eye level.
- Range: lowest −2.92° at az 293°, highest +1.04° at az 31°, mean −1.24°.
- Site: Shackleton crater rim, working pick −89.781°, 203.743° E. It is **not** an official landing site.
- Source: NASA LRO LOLA LDEM_85S_20M (PDS Geosciences Node), horizon looks out 35 km.

## The formula
The real horizon only varies by about 4°, which would be almost flat on a model. So we exaggerate the vertical by a factor k:

```
wall top height above the disc = pedestal_h + r_wall * k * tan(skyline_deg)
```

- `pedestal_h` is the eye height: the centre post top, measured from the disc surface. The "eye" is where the observer stands.
- `r_wall` is the radius at which the wall's **outer** top edge sits. A ray from the eye has to clear that edge, so the outer edge is the one that blocks.
- `k` is the vertical exaggeration. **The lamp uses the same k**, so the lamp drops behind the wall exactly when the real Sun drops behind the real ridge. If k changes, tell Darren.

Suggested starting values (all adjustable): disc 140 mm diameter, r_wall 60 mm, k = 10, wall 2.4 mm thick. Pick `pedestal_h` so the lowest point (−2.92°) still leaves a wall of at least 2 mm: `pedestal_h >= 2 + 60 * 10 * tan(2.92°) = about 32.6 mm`, so about 33 mm.

With those values the wall runs from about 2 mm to 44 mm tall. Place a north mark (a notch in the rim at az 0) so the stepper home position can be set to it.

## Earth marker (optional)
Earth is nearly always close to the horizon from this site. Its direction averages az 156° and swings about 148° to 164° over a year, elevation about −7.3° to +6.4° (JPL Horizons, one year from 2026-11-10). If you engrave a mean direction line, use az 156°.

## What Darren needs from this
- **Lamp height:** the Sun's elevation stays between −1.75° and +1.74° over a year. Lamp height above the disc = `pedestal_h + r_lamp * k * tan(sun_elevation)`. For a lamp 150 mm away and k = 10, that is about ±46 mm around eye height.
- **Photoresistor:** it should sit at eye height (pedestal top) at the centre, mounted from above on a fixed arm, not on the spinning disc. The disc and wall rotate around it. This is a proposal, so confirm it with Darren.
- **Spin direction:** still to be confirmed against the app. Don't engrave anything that depends on it yet.

## Please check
- Shaft socket size: measure the 28BYJ-48 shaft with calipers. It is a D-shaft, nominally 5 mm diameter and 3 mm across the flats. [verify]
- Print a clearance test piece first, because fit varies by printer.
