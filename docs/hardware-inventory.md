# SpaceApps Hackathon – Hardware Inventory

Nov 5, 2026 · @Angel

## Team

The project must give the two ME majors real mechanical design work for their resumes, and give Angel a hardware-heavy challenge; the MEs will not write code.

| Member | Major | Strengths | Wants from the project |
| --- | --- | --- | --- |
| Gustavo | Mechanical Engineering | CAD; no coding experience | Resume experience in his own field (mechanical design) |
| Darren | Mechanical Engineering | CAD; no coding experience | Resume experience in his own field (mechanical design) |
| Angel | Computer Science and Engineering | Software and coding | A hardware-focused challenge: electronics, embedded, integration |

## What the project needs to offer

- **Substantial mechanical design**: a moving mechanism or load-bearing structure the MEs design in CAD and iterate on the A1, not just an enclosure. Examples: gearing, linkages, pan-tilt mounts, deployable or folding parts, tolerancing for printed fits.
- **Hardware-heavy work for Angel**: sensor integration, motor and servo control, soldered perfboard circuits, and the UNO Q's Linux + real-time MCU split.
- **Clean ownership split**: MEs own the physical system, Angel owns electronics and code, and the team agrees early on the interface (mounting points, motor and sensor sizes, wire routing, power).
- **Resume-ready outputs**: CAD models and drawings, print iterations, a wiring schematic, and a working demo.

## At a glance

We have three controller boards (one Linux + AI capable), a full ELEGOO starter kit of sensors and actuators, perfboards for permanent builds, a soldering kit, two multimeters and a Bambu Lab A1 for enclosures and mounts.

| Category | What we have |
| --- | --- |
| Compute | Arduino UNO Q, ELEGOO UNO R3, "Tiny" mini board |
| Sensing | Ultrasonic, DHT11 temp/humidity, thermistor, photoresistors, IR receiver, joystick, tilt switch, buttons, potentiometer |
| Actuation | SG90 servo, stepper + ULN2003 driver, DC motor + fan blade, 5V relay, buzzers |
| Display | LCD1602, 1-digit and 4-digit 7-segment, LEDs, RGB LEDs, UNO Q LED matrix |
| Build | 830-point breadboard, perfboards (5 sizes), jumper and Dupont wires |
| Tools | Soldering iron kit, 2 multimeters |
| Fabrication | Bambu Lab A1 3D printer + filament |

## Controller and compute boards

The UNO Q is the main brain: it runs Linux on a Qualcomm chip for AI and camera work, with a separate STM32 for real-time I/O.

| Board | Qty | Key specs | Best use |
| --- | --- | --- | --- |
| Arduino UNO Q | 1 | MPU: Qualcomm Dragonwing QRB2210 (Linux). MCU: STM32U585. 4 GB LPDDR4, 32 GB eMMC. Wi-Fi + Bluetooth LE. USB camera + 2x MIPI CSI camera, monitor, keyboard, mouse, Modulino connectors. On-board LED matrix. | Vision/AI, Wi-Fi dashboards, running Python + Arduino sketches together |
| ELEGOO UNO R3 | 1 | Classic Arduino Uno (ATmega328P class), USB cable included | Quick sensor tests, second controller |
| "Tiny" mini board | 1 | Micro USB, 16 MHz crystal, 78L05 regulator, ISP header, reset button, pins 0–16, 25, A0–A7, I2C (SDA/SCL). Headers not soldered yet. | Small embedded node inside a printed part |

Specs for the UNO Q are from its box; get-started page: [arduino.cc/uno-q](https://arduino.cc/uno-q).

## ELEGOO UNO starter kit contents

Quantities are from the kit's lid card; recount anything you plan to rely on.

| Type | Item | Qty |
| --- | --- | --- |
| Sensor | Ultrasonic distance sensor (HC-SR04) | 1 |
| Sensor | DHT11 temperature and humidity module | 1 |
| Sensor | Thermistor | 1 |
| Sensor | Photoresistor (photocell) | 2 |
| Sensor | IR receiver module + remote control | 1 each |
| Input | Joystick module | 1 |
| Input | Push button | 5 |
| Input | Potentiometer, 10k | 1 |
| Input | Tilt ball switch | 1 |
| Actuator | Servo motor SG90 | 1 |
| Actuator | Stepper motor + ULN2003 driver module | 1 each |
| Actuator | DC motor (3–6 V) + fan blade | 1 |
| Actuator | 5V relay | 1 |
| Actuator | Active buzzer / passive buzzer | 1 each |
| Display | LCD1602 module (with pin header) | 1 |
| Display | 1-digit 7-segment display | 1 |
| Display | 4-digit 7-segment display | 1 |
| Display | LED (assorted colors) | 25 |
| Display | RGB LED | 2 |
| IC | 74HC595 shift register | 1 |
| IC | L293D motor driver | 1 |
| Passive | Resistors (assorted) | 120 |
| Passive | Diode rectifier | 2 |
| Passive | NPN transistor PN2222 | 2 |
| Power | Breadboard power supply module | 1 |
| Power | 9V battery with snap-on connector | 1 |
| Prototyping | Prototype expansion shield | 1 |
| Prototyping | 830 tie-point breadboard | 1 |
| Wiring | Breadboard jumper wires | 65 |
| Wiring | Female-to-male Dupont wires | 10 |
| Cable | USB cable | 1 |

## Prototyping boards

Breadboard first, then move the final circuit to perfboard so it survives the demo.

| Item | Sizes (approx.) | Qty |
| --- | --- | --- |
| Double-sided perfboard (prototype PCB) | 7x9 cm, 5x7 cm, 4x6 cm, 3x7 cm, 2x8 cm | Several stacks per size; count TBD |
| 830 tie-point breadboard | Full size | 1 (from ELEGOO kit) |
| Prototype expansion shield | Uno form factor | 1 (from ELEGOO kit) |

## Tools and consumables

We can solder, desolder and debug circuits on site.

| Item | Details | Qty |
| --- | --- | --- |
| Soldering iron | Adjustable temperature, plug-in, in red zip case | 1 |
| Soldering iron stand + tip sponge | Metal stand, cleaning sponge | 1 |
| Desoldering pump | Spring-loaded solder sucker | 1 |
| Solder wire | 63/37 rosin core, 1.0 mm, 50 g | 1 roll |
| Tweezers | Fine tip | 1 |
| Wire cutter/stripper | Small, yellow handle | 1 |
| Heat shrink tubing | Assorted sizes; red, black, yellow | 1 bag |
| Cable ties | Assorted colors | 1 bundle |
| Component assortment | Bag of small parts in the soldering kit | Contents TBD |
| Multimeter: Jameco ReliaPro | DC/AC volts, amps (10 A), resistance, diode, hFE transistor test, temperature, backlight | 1 |
| Multimeter: Plusivo | DC/AC volts, amps (10 A), resistance, continuity, battery test, hold | 1 |
| Test leads | Red/black probe sets | 2+ |
| Automotive blade fuse assortment | Stored in multimeter bag | 1 box |

## Fabrication

The A1 lets us print enclosures, sensor mounts and brackets during the event.

| Item | Details | Qty |
| --- | --- | --- |
| Bambu Lab A1 3D printer | Bed-slinger FDM; build volume about 256 x 256 x 256 mm (approximate, from memory) | 1 |
| Filament | Material, colors and amount TBD | TBD |

## To confirm

No camera, battery pack for portable power, or wireless module beyond the UNO Q's built-in Wi-Fi/BLE is listed yet.

- [ ] Read the chip marking on the "Tiny" board (likely an ATtiny88-based MH-Tiny clone) and confirm the board package to install
- [ ] Count perfboards per size
- [ ] List filament types, colors and remaining amount
- [ ] Check what's in the soldering kit's component bag
- [ ] Note any USB camera, USB-C power supply or monitor we can bring for the UNO Q
- [ ] Add hardware from other teammates
