# Handoff: Angel → Gustavo and Darren

Nov 13, 2026 · from Angel (code, electronics) · for Gustavo (disc + terrain wall) and Darren (stand, lamp, stepper mount, electronics box)

**Status: DRAFT.** Drafted with Claude's help from the repo files, for Angel to read and correct before sending. Items marked **[verify]** or **[decide]** are not confirmed.
Sources: `docs/handoffs/gustavo-to-angel.md`, `cad/design_notes.md`, `docs/hardware-inventory.md`, `docs/context-handoff.md`, and the cached Horizons data in `data/`.

---

## 1. Answers to Gustavo's four requests

| He asked | Answer |
|---|---|
| **Check the Earth marker** (he engraved az 156.3°, el -0.20°) | **Confirmed.** Over the year of Horizons data (2026-11-10, 6-hour steps), Earth's mean azimuth is **156.23°**. It swings from **148.3° to 163.9°**. The mean elevation is -0.63°, and Earth's elevation swings from **-7.30° to +6.38°**, so the 0.4° difference in the elevation mean does not matter. No need to re-engrave. |
| **Sun elevation range** (for the lamp height) | **-1.746° to +1.738°** over the year. This matches the range already used in `cad/design_notes.md`. Darren can size the lamp slot from his table. |
| **Spin direction** | See section 2. |
| **Confirm az 0 = rim notch = firmware home** | **Yes, az 0 = the rim notch = home position (zero) in the firmware.** [Angel to confirm before sending.] |
| **Review and merge `scripts/make_wall.py` and `tests/test_wall.py`** | **Not possible yet: those files are not in the repo.** Also missing: `cad/terrain_disc_shackleton_rim.stl` (disc with pedestal and shaft socket) and the JSON lamp-height table. Only the wall-only STL, the SolidWorks curve files, and the preview image arrived. **Gustavo: please push those files, or tell me you don't need the script.** |

**Standing request for both:** do not change k = 10, r_wall = 60 mm, or the 33 mm pedestal without telling both Gustavo and Darren. The lamp height and the wall height share k, and the lamp only drops behind the wall at the right moment if they match.

**Adding another site:** send latitude and longitude. The site must be within about 15 km of the pole, because the downloaded terrain band is only ±50 km and the skyline looks 35 km out. Off-pole sites (for example Malapert) also break the fixed-lamp model. Angel adds the site and makes the skyline file; Gustavo reruns his wall script on it.

---

## 2. Spin direction (derived from data, confirm on the real model)

- In the Horizons data the Sun's azimuth **falls about 0.507° per hour**. That equals one full turn in about 29.5 days.
- Azimuth is measured clockwise from north, seen from above. A falling azimuth means the Sun moves **counterclockwise** around the site.
- With a **fixed lamp**, the disc must therefore turn **clockwise** seen from above.
- Gustavo's external gears (15-tooth pinion into the 90-tooth ring gear) **reverse direction**. So the **stepper shaft turns counterclockwise** seen from above.
- **Confirm with a real test** once the model runs. If the Sun's motion looks backwards, the fix is one sign in the firmware and no mechanical change.

---

## 3. Shared numbers (from `cad/design_notes.md`)

| Item | Value | Status |
|---|---|---|
| Vertical exaggeration k | 10 | fixed |
| Disc | 140 mm diameter, 4 mm thick | fixed |
| Wall | outer radius 60 mm, 2.4 mm thick | fixed |
| Eye height (centre post above disc top) | 33 mm | fixed |
| North (az 0) | rim notch + home flag or magnet | fixed |
| Drive | 28BYJ-48 → 15-tooth pinion → 90-tooth ring gear (6:1) | fixed |
| Degrees of disc per motor step | about 0.029° (about 12,288 steps per disc turn) | **[verify]** assumes 2048 steps per motor turn; Angel will bench-measure |
| Lamp distance from rotation axis, r_lamp | 120 to 150 mm | **[decide]** |
| Home sensor type, and its angle to the lamp | Hall (0°) or light gate (180°) | **[decide]** |
| Lamp height | `33 + r_lamp × 10 × tan(sun_elevation)` | see Gustavo's table |

---

## 4. Decisions still open (owner and what they block)

| # | Decision | Owner | Blocks |
|---|---|---|---|
| 1 | Final r_lamp (120 to 150 mm) | Gustavo + Darren | Lamp tower, lamp-height table, firmware |
| 2 | Home sensor: Hall + magnet, light gate, or slotted module | Gustavo + Darren, Angel buys | Parts order, disc magnet pocket or flag, firmware homing |
| 3 | Lamp angle relative to the home sensor (0° or 180°) | Gustavo + Darren | Firmware mapping of Sun azimuth to disc angle |
| 4 | Photoresistor on a fixed arm at eye height on the centre post (stretch goal) | Darren confirms | Whether an arm is designed at all |
| 5 | Disc support: hold-down clips (in `assembly_wip.png`) vs lazy susan bearing vs printed skid pads | Darren | Stand design |
| 6 | Electronics base: foam board / box vs printed | Darren | Box design |
| 7 | Lamp type: small bare LED aimed at the centre post, and a 0 to 80 mm height slot | Angel confirms | Lamp tower, LED wiring |

---

## 5. What Angel owes each of you

**To Gustavo**
- [ ] Confirm az 0 / notch / home (section 1).
- [ ] Confirm spin direction (section 2) once the model turns.
- [ ] Bench-measure the real steps per motor turn, then report the true degrees per disc step.
- [ ] Skyline file for any new site, on request.

**To Darren**
- [ ] The electronics box contents list and sizes (section 6, Darren).
- [ ] Wire exit list: what leaves the box, and where.
- [ ] Confirm the lamp type, LED mounting and height slot (decision 7).
- [ ] Parts that must be bought, so the home sensor mount can be sized (section 6).

**To the firmware (Angel's own work, listed so you know it is coming)**
- Home with the non-contact sensor, count steps, and map `SUN <az> <el>` to a disc angle using the notch as zero and the lamp offset.

---

## 6. Hardware each person needs

Counts and sizes come from `docs/hardware-inventory.md` unless marked. Anything marked **BUY** is not in our inventory.

### Gustavo: disc and terrain wall

| Item | Have it? | Notes |
|---|---|---|
| Bambu Lab A1 printer + filament | Printer yes; filament type, colours and amount **TBD** | Disc and wall: about 83 cm³, 2 to 4 h, flat side down, no supports, 0.28 mm draft layers. Also ring gear, pinion, shaft coupon, Earth marker. Build volume about 256 mm, **[verify]**. |
| 28BYJ-48 stepper (physical) | Yes, 1 in the ELEGOO kit | Needed in his hands to measure the D-shaft and fit-test the socket. Nominal 5 mm diameter, 3 mm across flats. **[verify with calipers]** |
| Calipers | **Not in the inventory** | Needed to measure the shaft and the printed fits. **BUY or borrow**, if he does not have his own. |
| Magnet, about 6 mm, for the north notch (Hall option) | **BUY** | Only if the Hall sensor is chosen. Glued in a pocket under the disc. |
| Flag (thin tab) for the light-gate option | Printed | Only if the light gate is chosen. |
| CAD (SolidWorks) | His own | Wall-top curves in `cad/horizon_wall/`. |

### Darren: stand, lamp, stepper mount, electronics box

| Item | Have it? | Notes |
|---|---|---|
| Bambu Lab A1 printer + filament | Printer yes; filament **TBD** | Stepper mount, lamp tower, home sensor mount, disc hold-down clips or skid pads. Rough times: mount 45 to 90 min, tower about 1 h. |
| 28BYJ-48 stepper + ULN2003 driver board (physical) | Yes, 1 each in the ELEGOO kit | Needed in his hands to model the mount and the gear centre distance. Take the centre distance from Gustavo's CAD. |
| Lamp LED + resistor | Yes: 25 assorted LEDs, 120 resistors in the kit | Small bare LED aimed at the centre post. Sharp shadows. Angel wires it. |
| Home sensor | **Depends on decision 2** | **Hall:** A3144 or KY-003 module, **BUY**. **Light gate from kit parts:** LED + photoresistor (the kit has 2 photoresistors and 25 LEDs). **Slotted optical module (KY-010 style):** **BUY**. |
| Photoresistor (stretch) | Yes, 2 in the kit | Eye height on the centre post, fixed arm. |
| Disc support | **Depends on decision 5** | Hold-down clips (printed), 3 printed skid pads (printed), or a lazy susan bearing, about $5 (**BUY**, optional). |
| Electronics base | Foam board or box | Not printed. Needs to fit the items in the next table. |

**What goes in Darren's electronics box** (Angel to confirm and measure; sizes are blank until measured):

| Item | In the box? | Size |
|---|---|---|
| Arduino UNO Q | Yes (the main brain) | **[Angel to measure]** |
| Breadboard power supply module (the stepper and LED run from here, never from UNO Q pins) | Yes | **[Angel to measure]** |
| ULN2003 driver board | Yes | **[Angel to measure]** |
| Breadboard or perfboard with the wiring | Yes | The kit breadboard is 830 tie-points; the perfboards run from 2x8 cm to 7x9 cm |
| ELEGOO UNO R3 | Optional backup | Standard Uno size |
| LCD1602, 10k potentiometer, push buttons | Stretch goals | Kit parts |
| USB-C power supply for the UNO Q | **Open in the inventory** | Angel to confirm what we can bring |

**Wires that leave the box** (a draft for Darren to plan the exits; confirm with the real parts **[verify]**): the stepper cable (through the ULN2003 board), the lamp LED (2 wires), the home sensor (3 wires for a Hall sensor), a USB cable to the laptop, the power input, and the optional photoresistor (2 wires). Nothing electrical goes on the spinning disc.

### Angel: electronics and code (for completeness)
UNO Q, ELEGOO UNO R3, "Tiny" board, breadboard, perfboards, jumper and Dupont wires, supply module, 9V battery, soldering kit, 2 multimeters, USB cable. Open items from the inventory: a USB camera, a monitor for the UNO Q, and a USB-C power supply.

### Not in the inventory and needs a decision or purchase
1. **Home sensor** parts (Hall + magnet, or slotted module), unless the light gate from kit parts is chosen.
2. **Calipers**, if neither of you has them.
3. **Filament**: type, colours, amount.
4. **Lazy susan bearing**, optional.
5. **USB-C power supply** and **monitor** for the UNO Q.

---

## 7. Timeline (from the build plan)

- **Day 1 first hour:** agree on the interface numbers and measure the stepper.
- **Day 1 morning:** Gustavo prints the socket coupon and models the disc; Darren models the motor mount; Angel gets Sun data and runs a stepper bench test.
- **Day 1 afternoon:** Angel builds the website MVP; Gustavo finishes the disc and wall; Darren builds the lamp tower and disc support.
- **Day 1 night:** print the disc and wall. **Go/no-go check at Day 1 midday.**
- **Day 2:** assemble and integrate in the morning, then polish and record a backup demo video.
- **Fallback:** if the hardware is not working by Day 2 midday, demo the website alone and turn the model by hand.
