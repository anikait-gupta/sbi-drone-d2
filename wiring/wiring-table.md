# Phase 1 wiring table

Ground truth for both wiring figures (`out/phase1-wiring.*` and `kicad/sbi_phase1.kicad_sch`). If a wiring fact changes, change it here first, then in `phase1_wiring.py`, then in the schematic, and run the netlist check.

As of 2026-09-30. Battery disconnected for all assembly and continuity checks.

## Sources

| Key | Source |
| :-- | :-- |
| BOM | `SBI_Drone_Phase1_Parts.xlsx`, prices and stock verified 2026-09-30 |
| 6C | Holybro, [Pixhawk 6C Ports](https://docs.holybro.com/autopilot/pixhawk-6c/pixhawk-6c-ports) |
| PM07 | Holybro, [PM07 Quick Start Guide](https://docs.holybro.com/power-module-and-pdb/power-module/pm07-quick-start-guide), including its board-tracing image |
| GPS | Holybro, [Standard M10 GPS overview](https://docs.holybro.com/gps-and-rtk-system/m8n-m9n-m10-gps/standard-m10-m9n-m8n-gps/overview) and [pinout](https://docs.holybro.com/gps-and-rtk-system/m8n-m9n-m10-gps/standard-m10-m9n-m8n-gps/pinout) images |
| AP | ArduPilot, [Holybro Pixhawk 6C](https://ardupilot.org/copter/docs/common-holybro-pixhawk6C.html) and [Connect ESCs and motors](https://ardupilot.org/copter/docs/connect-escs-and-motors.html) (Quad X image `m_01_01_quad_x1.svg`) |
| HW | Hobbywing, [XRotor PRO 50A dual pack](https://www.hobbywingdirect.com/products/xrotor-pro-50a-esc-dual-pack) |
| RM | RadioMaster, [RP3-H](https://radiomasterrc.com/products/rp3-h-expresslrs-2-4ghz-nano-receiver) |
| TEAM | Decisions made 2026-09-30: OVONIC battery approved, ELRS on TELEM3, ArduPilot Quad X map, ESC signals through the PM07 AUX header |

## Components

| Ref | Component | Label source |
| :-- | :-- | :-- |
| J1 | Battery: OVONIC 6S 5000 mAh 130C, XT60 | BOM #8, TEAM |
| J2 | PM07 power module + PDB (Holybro SKU 15008) | BOM #1 |
| J3 to J6 | ESC 1 to 4: Hobbywing XRotor PRO 50A, 4 to 6S, no BEC | BOM #4, HW |
| J7 to J10 | Motor 1 to 4: BrotherHobby Avenger 3110 730KV | BOM #3 |
| J11 | Pixhawk 6C, plastic (Holybro SKU 11054), ArduPilot | BOM #1 |
| J12 | GPS + compass: Holybro M10, IST8310, standard 10-pin (SKU 12040) | BOM #2, GPS |
| J13 | ELRS receiver: RadioMaster RP3-H | BOM #13, RM |

## Conductors

### Battery voltage

| ID | From | To | Carries | Connector or joint | Gauge | Source |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| P1 | J1 battery lead | J2 PM07 XT60 lead | BAT+ / BAT- | XT60 plug | PM07 lead 12 AWG; battery lead not recorded | BOM, PM07 |
| P2 | J2 B+ / GND pads | J3 ESC 1 power leads | V+ / V- | Solder to pads | TBD (not on the Hobbywing page) | BOM, PM07 |
| P3 | J2 B+ / GND pads | J4 ESC 2 power leads | V+ / V- | Solder to pads | TBD | BOM, PM07 |
| P4 | J2 B+ / GND pads | J5 ESC 3 power leads | V+ / V- | Solder to pads | TBD | BOM, PM07 |
| P5 | J2 B+ / GND pads | J6 ESC 4 power leads | V+ / V- | Solder to pads | TBD | BOM, PM07 |
| P6 to P9 | ESC n motor output, 3 leads | Motor n phase leads, 3 | Phase A, B, C | ESC side has 3.5 mm bullets fitted; solder JFtech 3.5 mm male bullets onto the bare motor leads | Not recorded | BOM #3, #4, #7, HW |

- The PM07 has four corner pad groups, each `GND B+ B+ GND`, so each group serves two ESCs. All B+ pads are common and all GND pads are common. Suggested: put ESC n on the group at the corner marked `Mn`. Seen from above, those corners match the Quad X map if the XT60 edge of the PM07 faces the rear (inferred from the PM07 silkscreen, not stated by Holybro).
- Holybro rates the PM07's XT60 and 12 AWG lead at 30 A continuous and 60 A for under 1 minute. The PCB is rated 90 A continuous and 140 A burst (under 60 s). See open item 3.
- Motor phase order is arbitrary. Each ESC's DIP switch sets spin direction.

### Regulated 5 V and battery sense

| ID | From | To | Carries | Connector | Source |
| :-- | :-- | :-- | :-- | :-- | :-- |
| F1 | J2 PWR1 | J11 POWER1 | Pins 1-2 VCC 5 V, 3 CURRENT, 4 VOLTAGE, 5-6 GND | 6-pin JST-GH cable (supplied with PM07) | PM07, 6C |

- The PM07 supplies regulated 5.2 V at up to 3 A. ArduPilot defaults for POWER1: `BATT_MONITOR=4`, `BATT_VOLT_PIN=8`, `BATT_CURR_PIN=4`, `BATT_VOLT_MULT=18.182`, `BATT_AMP_PERVLT=36.364` (AP).

### Signal

| ID | From | To | Carries | Connector | Source |
| :-- | :-- | :-- | :-- | :-- | :-- |
| S1 | J11 FMU PWM OUT (AUX) | J2 FMU-PWM-in | Pin 1 VDD_Servo, 2-9 FMU_CH1-8, 10 GND | 10-pin JST-GH cable | 6C, PM07, TEAM |
| S2 | J2 FMU-PWM-out channel 1 (S and -) | J3 ESC 1 signal lead | AUX 1 PWM + signal ground | ESC signal plug onto the 3-pin header | PM07, TEAM |
| S3 | J2 FMU-PWM-out channel 2 | J4 ESC 2 signal lead | AUX 2 PWM | as S2 | PM07, TEAM |
| S4 | J2 FMU-PWM-out channel 3 | J5 ESC 3 signal lead | AUX 3 PWM | as S2 | PM07, TEAM |
| S5 | J2 FMU-PWM-out channel 4 | J6 ESC 4 signal lead | AUX 4 PWM | as S2 | PM07, TEAM |
| S6 | J12 GPS 10-pin | J11 GPS1 | 1 VCC, 2 RX, 3 TX, 4 SCL, 5 SDA, 6 SAFETY_SWITCH, 7 SAFETY_SWITCH_LED, 8 VDD_3V3, 9 BUZZER-, 10 GND (GPS-side names, V1) | 10-pin JST-GH cable, 26 cm, supplied | GPS, 6C |
| S7 | J13 RP3-H | J11 TELEM3 | 5V to pin 1 VCC; receiver TX to pin 3 USART2_RX; receiver RX to pin 2 USART2_TX; GND to pin 6. Pins 4-5 empty | Custom cable: RP3-H 4-pin JST-GH lead joined to a 6-pin JST-GH from the elechawk kit | BOM #13, #14, 6C, TEAM |

- The PM07's FMU-PWM-out `+` row carries no 5 V (Holybro). The XRotor PRO has no BEC and needs none, so this is fine.
- ArduPilot: `SERVO9_FUNCTION=33`, `SERVO10_FUNCTION=34`, `SERVO11_FUNCTION=35`, `SERVO12_FUNCTION=36` (Motor 1 to 4 on AUX 1 to 4). Set `SERVO1_FUNCTION` to `SERVO4_FUNCTION` to 0 so the unused MAIN outputs carry no motor signal.
- ArduPilot: TELEM3 is `SERIAL5`. Set `SERIAL5_PROTOCOL=23` (RCIN) for CRSF. ArduPilot says ELRS needs a full UART, so the RC IN port cannot be used (AP).
- RP3-H working voltage is 4.5 to 8.4 V (RM), so TELEM3's 5 V supply is in range.

## Motor map (ArduPilot Quad X)

| Motor | Position | Spin | Prop | ESC | Output |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | front-right | CCW | HQProp MR 10x4.5 (CCW) | ESC 1 | AUX 1 (SERVO9) |
| 2 | rear-left | CCW | HQProp MR 10x4.5 (CCW) | ESC 2 | AUX 2 (SERVO10) |
| 3 | front-left | CW | HQProp MR 10x4.5R (CW) | ESC 3 | AUX 3 (SERVO11) |
| 4 | rear-right | CW | HQProp MR 10x4.5R (CW) | ESC 4 | AUX 4 (SERVO12) |

Not yet confirmed on hardware. Confirm with a props-off motor test in Mission Planner before fitting props.

## Ports left empty in Phase 1

Every port is accounted for. These are empty on purpose.

| Board | Port | Why empty |
| :-- | :-- | :-- |
| 6C | POWER2 | One power module only |
| 6C | TELEM1 | Kept for an optional SiK telemetry radio |
| 6C | TELEM2 | Kept for the Phase 2 companion computer |
| 6C | GPS2, I2C, CAN1, CAN2 | No second GPS or other sensors in Phase 1 |
| 6C | I/O PWM OUT (MAIN) | Motors are on AUX |
| 6C | PPM/SBUS RC, DSM RC, SBUS OUT | ELRS uses TELEM3 |
| 6C | USB | Laptop link for setup only, not wired on the aircraft |
| 6C | FMU DEBUG, I/O DEBUG | Not used |
| PM07 | PWR2 | One flight controller power port in use |
| PM07 | I/O PWM-in and the M1-M8 solder holes | Motors are on AUX |
| PM07 | FMU-PWM-out channels 5-8 | Only four ESCs |
| PM07 | CAP&ADC-in, CAP&ADC-out | The 6C has no CAP&ADC port |
| PM07 | Second B+ / GND pair at each corner | Only four ESCs |
| J1 | Balance lead (JST-XH) | Charger only |
| J13 | Ext-V input | Not used |

Not wiring, but on the list: the microSD card goes in the 6C's slot. The charger, the Pocket transmitter and the 100 W USB-C supply stay on the ground.

## Open items

1. **ESC power lead gauge.** The Hobbywing page does not state it. Retailer listings say 14 AWG; check on arrival and record it here.
2. **ESC signal plug.** Confirm on arrival that the XRotor PRO signal lead ends in a plug that fits the PM07's 2.54 mm 3-pin header, with signal on S and ground on -.
3. **PM07 input lead rating.** 30 A continuous, 60 A for under 1 minute (Holybro), against four 50 A ESCs and motors listed at 37.6 A max each. Fine for hover; check measured current in the first flight logs before aggressive flying. Holybro says to change the plug and wire for higher current.
4. **GPS version.** M10 V2 has no safety switch, buzzer or safety LED (pins 6-9 are NC). The 6C has no safety switch of its own. If a V2 unit arrives, disable the safety switch in ArduPilot (`BRD_SAFETY_DEFLT=0`) and expect no buzzer.
5. **Motor map** confirmed only by a props-off motor test.
6. **Frame layout.** Wire lengths and PM07 orientation depend on the CNC frame CAD.
