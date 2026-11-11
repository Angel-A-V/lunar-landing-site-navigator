# Horizon wall (Shackleton rim)

Just the horizon wall ring, made from `for_gustavo/skyline_shackleton_rim.csv`. I'm designing the disc, pedestal, shaft socket and north notch around it in SolidWorks.

Wall top height above the disc = `pedestal_h + r_wall * k * tan(skyline_deg)`, with r_wall = 60 mm (outer edge), k = 10 and pedestal_h = 33 mm. The wall is 2.4 mm thick (57.6 to 60 mm radius) and runs from 2.38 mm (az 293°) to 43.85 mm (az 31°) above the disc.

| File | Use |
| --- | --- |
| `sw_terrain_wall_only_shackleton_rim.stl` | SolidWorks (Y up, east = +X, north = −Z). Open as Solid Body, units mm. |
| `terrain_wall_only_shackleton_rim.stl` | Slicers (Z up, east = +X, north = +Y). |
| `sw_wall_top_outer_shackleton_rim.txt`, `sw_wall_top_inner_shackleton_rim.txt` | Wall-top curves for SolidWorks Curve Through XYZ Points (X, Y, Z in mm, 1° steps, first point repeated to close the loop). |
| `wall_only_preview.png` | Preview. |

In every file the bottom of the wall is at height 0 (the disc's top face) and centred on the origin. Az 0 (north) is where the north notch and stepper home go.

If k, r_wall or pedestal_h change, these files need regenerating and Darren's lamp height changes too.
