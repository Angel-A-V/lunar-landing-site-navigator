# Mechanical design notes

Updated Nov 13, 2026 · Gustavo. Items marked **[verify]** are not confirmed yet.

## Shared numbers (change only after telling everyone)

| Item | Value | Used by |
| --- | --- | --- |
| Vertical exaggeration k | 10 | wall, lamp |
| Eye height (centre post top above the disc top) | 33 mm | wall, lamp, photoresistor |
| Wall outer radius r_wall | 60 mm (2.4 mm thick) | wall |
| North (az 0) | rim notch + home flag/magnet on the disc | firmware zero |
| Drive | 28BYJ-48 → 15-tooth pinion → 90-tooth ring gear on the disc | firmware |
| Lamp distance from rotation axis r_lamp | 120–150 mm, final value **[decide]** | lamp, firmware |
| Angle from home sensor to lamp | 0° (Hall sensor) or 180° (light gate) **[decide]** | firmware |

## Drive (Gustavo → Angel)

- Gear ratio 15/90 = 6:1. The motor turns 6 times per disc turn.
- Disc degrees per step = (360 / 2048) × (15 / 90) ≈ 0.029°, about 12,288 steps per disc turn. 2048 steps per motor turn is the usual 28BYJ-48 figure **[verify]**. The true internal ratio is not exact, so the disc drifts slightly each turn; homing fixes it.
- External gears reverse direction: **the disc turns opposite to the motor shaft.**

## Home sensor (replaces the push button)

The button needs too much force and a glued peg could wobble or snap. Use a non-contact sensor; the only part on the disc is a magnet or a flag at the north notch.

1. **Hall sensor + magnet (preferred).** ~6 mm magnet glued in a pocket under the disc at north; A3144 / KY-003 module on the base, 2–5 mm below the magnet path. Ignores lamp light. **Not in the ELEGOO kit, needs buying.**
2. **Light gate from kit parts.** LED and photoresistor facing each other across a printed slot; a thin flag on the disc passes through it. Shield it from the lamp; home slowly (photoresistor is slow).
3. **Slotted optical module (KY-010 style).** Same as 2 but cleaner. Needs buying.

Firmware reads it as a simple yes/no input, like the button.

## Sun lamp position

The lamp is fixed and the disc turns under it, so its position around the circle is free. Keep its line of sight to the centre post clear of the stepper, pinion and hold-down clips. Simplest: put the lamp at the same angle as the home sensor (offset 0°, Hall sensor) or directly opposite (offset 180°, light gate).

Lamp height above the **disc top** (measured to the LED centre; Sun elevation range at this site −1.75° to +1.74° over a year, from Angel's Horizons data):

```
lamp height = 33 + r_lamp × 10 × tan(sun_elevation)
```

| Sun elevation | r_lamp = 120 mm | r_lamp = 150 mm |
| --- | --- | --- |
| −1.75° (lowest) | −3.7 mm | −12.8 mm |
| −1.0° | 12.1 mm | 6.8 mm |
| **0° (flat horizon)** | **33 mm** | **33 mm** |
| +1.0° | 53.9 mm | 59.2 mm |
| +1.74° (highest) | 69.5 mm | 78.6 mm |

Use a small bare LED aimed at the centre post (sharp shadows). A fixed height of 33 mm works for the demo; a vertical slot covering about 0–80 mm lets it match any date.

## Darren's part (updated for this design)

The older plan (Sun ring, servo Earth arm, centre-shaft drive) is replaced by the parts below.

- **Stepper mount:** the stepper is now **off-centre**, beside the disc, driving the 90-tooth ring gear through the 15-tooth pinion. The mount must hold the correct gear centre distance (pitch radius of pinion + ring) **[take from Gustavo's CAD]** and be stiff so the gears don't skip.
- **Disc support:** the disc turns on the base with the hold-down clips shown in `assembly_wip.png`. No centre shaft drive.
- **Lamp tower:** fixed, at r_lamp from the rotation axis, with a vertical slot for the LED (table above). Position around the circle per the home-sensor choice.
- **Home sensor mount:** on the fixed base under the magnet/flag path at az 0 (Hall: 2–5 mm gap; light gate: slot straddling the flag).
- **Photoresistor (stretch):** at eye height on the centre post, fixed, not on the spinning disc **[confirm]**.
- **Electronics box:** wires stay on the fixed base; nothing electrical on the disc.

## To tell Angel

1. Gear ratio 15/90 and reversed direction.
2. Home sensor type and its angle to the lamp.
3. Final r_lamp.
