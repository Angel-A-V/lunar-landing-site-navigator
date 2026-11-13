# CAD: physical model (Shackleton rim)

Owners: Gustavo (disc, horizon wall, ring gear, home flag), Darren (stand, stepper mount, lamp tower, sensor mount, electronics box).
Design numbers and decisions are in [`design_notes.md`](design_notes.md).

| Folder / file | What |
| --- | --- |
| `horizon_wall/` | The horizon wall ring, built from `for_gustavo/skyline_shackleton_rim.csv` |
| `horizon_wall/sw_terrain_wall_only_shackleton_rim.stl` | For SolidWorks (Y up, east = +X, north = −Z). Open as Solid Body, units mm |
| `horizon_wall/terrain_wall_only_shackleton_rim.stl` | For slicers (Z up, east = +X, north = +Y) |
| `horizon_wall/sw_wall_top_{outer,inner}_shackleton_rim.txt` | Wall-top curves for SolidWorks Curve Through XYZ Points (mm, 1° steps, first point repeated to close the loop) |
| `horizon_wall/wall_only_preview.png` | Preview of the wall |
| `test_prints/shaft_coupon.stl` | 5 fit-test pucks for the 28BYJ-48 D-shaft (use it for the 15-tooth pinion bore). Rim notches 1–5 = clearance 0.10 / 0.15 / 0.20 / 0.25 / 0.30 mm |
| `assembly_wip.png` | Screenshot of Gustavo's current SolidWorks assembly |

In every wall file, the bottom of the wall is at height 0 (the disc's top face) and centred on the origin. Az 0 (north) is where the north notch, home flag and stepper zero go.

Wall top height above the disc = `pedestal_h + r_wall * k * tan(skyline_deg)`, with r_wall = 60 mm (outer edge), k = 10 and pedestal_h = 33 mm. The wall is 2.4 mm thick (57.6 to 60 mm radius) and runs from 2.38 mm (az 293°) to 43.85 mm (az 31°) above the disc. If k, r_wall or pedestal_h change, these files need regenerating and the lamp height changes too.
