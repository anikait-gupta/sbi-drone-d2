# -*- coding: utf-8 -*-
"""SBI drone, Phase 1: power and signal wiring block diagram.

Every label traces to wiring-table.md, which cites the parts list (SBI_Drone_Phase1_Parts.xlsx),
the Holybro and ArduPilot pages, or a team decision. Unrecorded values say TBD.
Run: python phase1_wiring.py  ->  out/phase1-wiring.svg, .drawio, .png; exits 1 if the linter finds issues
"""
import os, sys
from wiring_diagram import Diagram, rasterise, PWR, FIVE, SIG

d = Diagram(1540, 1060)
NOTE_INK = "#4E342E"

# ---------------- battery -> PM07: power spine on one centreline ----------------
PY = 290
d.node("bat", 40, 245, 220, 90, "Battery", ["OVONIC 6S 5000 mAh 130C", "XT60"], "pwr")

d.node("pm07", 400, 220, 440, 470, kind="pwr", container=True)
d.text(420, 246, "PM07 power module + PDB", 14, "bold", PWR)
d.text(420, 263, u"Holybro SKU 15008 · 2–12S in", 10.5, "normal", "#607D8B")
d.node("pm_xt60", 412, PY - 14, 120, 28, "XT60 lead", (), "pwr", rx=4, tsize=11)
d.edge([(260, PY), (412, PY)], PWR, 3, label="XT60", lx=336, ly=PY - 6)
for i, s in enumerate([u"Lead: 12 AWG, 30 A cont. / 60 A < 1 min",
                       u"PCB: 90 A cont. / 140 A burst (< 60 s)",
                       u"5.2 V / 3 A regulator feeds PWR1"]):
    d.text(420, 336 + i * 16, s, 10, "normal", "#607D8B")

# unused PM07 ports, drawn dashed: empty on purpose, not forgotten
d.node("pm_pwr2", 412, 420, 100, 28, "PWR2", (), "mech", rx=4, dash=True, tsize=11)
d.node("pm_iopwm", 412, 460, 230, 28, u"I/O PWM-in + M1–M8 holes", (), "mech", rx=4, dash=True, tsize=11)
d.node("pm_cap", 412, 500, 150, 28, "CAP&ADC in / out", (), "mech", rx=4, dash=True, tsize=11)
d.node("pm_ch58", 412, 540, 150, 28, u"PWM-out ch 5–8", (), "mech", rx=4, dash=True, tsize=11)

# ---------------- ESCs and motors, one row each ----------------
# ArduPilot Quad X, from ArduPilot's motor-order image. Confirm with a props-off motor test.
MOTORS = [("front-right", "CCW", "10x4.5 (CCW)"), ("rear-left", "CCW", "10x4.5 (CCW)"),
          ("front-left", "CW", "10x4.5R (CW)"), ("rear-right", "CW", "10x4.5R (CW)")]
ESC_Y = [250, 350, 450, 550]
for i, (y, (pos, spin, prop)) in enumerate(zip(ESC_Y, MOTORS)):
    n = i + 1
    pw, sg = y + 24, y + 56                 # ESC power and signal entry centrelines
    # PM07 stubs interleaved so each run is one straight line. Pads sit at the board's
    # four corners and the header is one block on the board; see the notes panel.
    d.node("pm_pad%d" % n, 700, pw - 12, 130, 24, "M%d-corner pads" % n, (), "pwr", rx=4, tsize=11)
    d.node("pm_ch%d" % n, 700, sg - 12, 130, 24, "PWM-out ch %d" % n, (), "sig", rx=4, tsize=11)
    d.node("esc%d" % n, 960, y, 200, 80, "ESC %d" % n, ["XRotor PRO 50A", u"4–6S · no BEC"], "pwr")
    d.node("mot%d" % n, 1290, y, 220, 80, u"Motor %d · %s" % (n, pos),
           ["Avenger 3110 730KV", u"%s · prop %s" % (spin, prop)], "mech")
    d.edge([(830, pw), (960, pw)], PWR, 3,
           label=("B+ / GND, solder" if n == 1 else None), lx=895, ly=pw - 6)
    d.edge([(830, sg), (960, sg)], SIG, 2,
           label=("signal + GND" if n == 1 else None), lx=895, ly=sg - 6)
    d.edge([(1160, y + 40), (1290, y + 40)], PWR, 3,
           label=("3 phase leads" if n == 1 else None), lx=1225, ly=y + 34)

# PM07 bottom ports: PWR1 feeds the FC; FMU-PWM-in takes the FC's AUX outputs
d.node("pm_pwr1", 412, 640, 100, 28, "PWR1", (), "five", rx=4, tsize=11)
d.node("pm_fmuin", 530, 640, 120, 28, "FMU PWM-in", (), "sig", rx=4, tsize=11)

# ---------------- flight controller with port stubs ----------------
d.node("fc", 380, 740, 600, 290, kind="sig", container=True)
d.text(680, 772, "Flight controller: Pixhawk 6C", 14, "bold", SIG)
d.text(680, 790, u"Plastic · SKU 11054 · ArduPilot", 10.5, "normal", "#607D8B")
d.node("p_POWER1", 412, 780, 100, 28, "POWER1", (), "five", rx=4, tsize=11)
d.node("p_FMU", 530, 780, 120, 28, "FMU PWM OUT", (), "sig", rx=4, tsize=11)

# the PM07 FEEDS the FC, so this arrow points into POWER1
d.edge([(462, 668), (462, 780)], FIVE, 3, label="5 V + V/I sense", lx=400, ly=719)
# AUX 1-4 drive the ESCs, so this arrow points into the PM07
d.edge([(590, 780), (590, 668)], SIG, 2, label=u"AUX 1–4, 10-pin", lx=668, ly=719)

d.node("p_GPS1", 392, 840, 100, 28, "GPS1", (), "sig", rx=4, tsize=11)
d.node("p_TELEM3", 392, 930, 100, 28, "TELEM3", (), "sig", rx=4, tsize=11)

EMPTY = [["POWER2", "TELEM1", "TELEM2"],
         ["GPS2", "I2C", "CAN1"],
         ["CAN2", "I/O PWM OUT", "PPM/SBUS RC"],
         ["DSM RC", "SBUS OUT", "USB"]]
for r, row in enumerate(EMPTY):
    for c, name in enumerate(row):
        d.node("p_" + name, 520 + c * 150, 840 + r * 40, 140, 28, name, (), "mech",
               rx=4, dash=True, tsize=11)
d.text(680, 1014, "Dashed: empty in Phase 1. Debug ports not used.", 10, "italic", "#455A64", "middle")

# ---------------- GPS and receiver ----------------
d.node("gps", 40, 824, 220, 60, "GPS + compass", [u"Holybro M10 · IST8310"], "sig")
d.node("rx", 40, 914, 220, 60, "ELRS receiver", [u"RadioMaster RP3-H · CRSF"], "sig")
d.edge([(260, 854), (392, 854)], SIG, 2, label="10-pin cable", lx=326, ly=848)
d.edge([(260, 944), (392, 944)], SIG, 2, label="custom cable", lx=326, ly=938)

# ---------------- title, legend, notes ----------------
d.text(500, 56, "SBI drone, Phase 1: power and signal wiring", 20, "bold")
d.text(500, 80, "Battery disconnected for all assembly and continuity checks.", 11.5, "italic", "#607D8B")
d.text(500, 100, u"Pixhawk 6C + PM07 · 6S · ArduPilot Quad X · as of 2026-09-30", 11, "normal", "#607D8B")

d.node("legend", 40, 30, 420, 180, kind="note", container=True)
d.text(60, 56, "Legend", 13, "bold", "#5D4037")
for i, (c, w, lab) in enumerate([(PWR, 3, "battery voltage, + / - pair"),
                                 (FIVE, 3, "regulated 5 V + battery sense"),
                                 (SIG, 2, "signal: PWM, serial, I2C")]):
    yy = 82 + i * 24
    d.edge([(62, yy), (112, yy)], c, w, arrow=False, hop=False)
    d.text(124, yy + 4, lab, 11, "normal", NOTE_INK)
d.node("lg_dash", 62, 144, 50, 20, kind="mech", rx=4, dash=True)
d.text(124, 158, "port intentionally empty", 11, "normal", NOTE_INK)
d.text(62, 192, "Grounds omitted. Arrow = direction of supply or signal.", 10, "italic", "#795548")

# top-view motor map: the same Quad X positions as the motor boxes, laid out as fitted
d.node("map", 1180, 30, 330, 180, kind="note", container=True)
d.text(1200, 54, "Motor map, top view", 13, "bold", "#5D4037")
for n, x, y, spin in [(3, 1200, 72, "CW"), (1, 1400, 72, "CCW"), (2, 1200, 158, "CCW"), (4, 1400, 158, "CW")]:
    d.node("map%d" % n, x, y, 90, 36, u"M%d · %s" % (n, spin), (), "mech", rx=18, tsize=11)
d.text(1345, 120, u"▲ FRONT", 11, "bold", "#455A64", "middle")
d.text(1345, 138, "Quad X", 10, "italic", "#455A64", "middle")

d.node("notes", 1020, 690, 490, 320, kind="note", container=True)
d.text(1040, 716, "Checked against", 13, "bold", "#5D4037")
for i, s in enumerate([
        "Labels: SBI_Drone_Phase1_Parts.xlsx (2026-09-30).",
        "Ports: Holybro Pixhawk 6C ports page, PM07 guide.",
        u"ESCs on AUX 1–4: SERVO9–12_FUNCTION = 33–36.",
        "RC on TELEM3 = SERIAL5, SERIAL5_PROTOCOL = 23.",
        "Motor map: ArduPilot Quad X. Confirm props-off.",
        "Spin direction: each ESC's DIP switch.",
        "PM07 pads sit at the board corners, not by the header.",
        "ESC power lead gauge: TBD.",
        "PM07 XT60 lead: 30 A cont. (Holybro). Check logs.",
        "M10 V2 has no safety switch or buzzer: check unit.",
        "Phase 2: TELEM2 companion computer.",
        "TELEM1 kept for an optional SiK radio."]):
    d.text(1040, 744 + i * 22, u"•  " + s, 10, "normal", NOTE_INK)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    issues = d.check()
    print("\n".join("  " + s for s in issues) if issues else "  layout clean")
    os.makedirs("out", exist_ok=True)
    d.write("out/phase1-wiring.svg", "out/phase1-wiring.drawio")
    rasterise("out/phase1-wiring.svg", "out/phase1-wiring.png", scale=2)
    print("nodes %d  edges %d  texts %d" % (len(d.nodes), len(d.edges), len(d.texts)))
    sys.exit(1 if issues else 0)
