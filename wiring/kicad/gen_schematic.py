# -*- coding: utf-8 -*-
"""Write the first version of the Phase 1 KiCad project: symbol library, schematic, project file.

Nets are built from named local labels on short wire stubs; the same name means the same net.
Every pin is either labelled or carries a no-connect flag.

After this has run, sbi_phase1.kicad_sch is the source of truth. If you edit the schematic in
KiCad, do not run this again: it overwrites the schematic, the library and the project file.

Run: python gen_schematic.py
"""
import json, os, uuid

LIB = "sbi_phase1"
NS = uuid.UUID("6f1d9a52-4c3e-4f5e-9a0b-2b7f3d1e5c80")     # fixed, so regenerating gives the same UUIDs
G = 1.27                                                   # KiCad connection grid, mm
FONT = "(effects (font (size 1.27 1.27)))"
FONT_HIDE = "(effects (font (size 1.27 1.27)) (hide yes))"


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(map(str, key))))


def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def q(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---------------------------------------------------------------- symbols
# Each side is a list of rows, top to bottom: ("H", heading) is a heading row drawn inside the
# body, None is an empty row, and (number, name, electrical type) is a pin. Pin numbers are
# hidden; names carry the signal, prefixed with the connector pin where Holybro documents it.
def P(num, name, etype="passive"):
    return (num, name, etype)


SYMBOLS = {
    "Battery": dict(desc="LiPo battery pack", right=[
        P("BATP", "BAT+", "power_out"), P("BATN", "BAT-"), P("BAL", "Balance(JST-XH)")]),

    "PM07": dict(desc="Holybro PM07 power module and PDB", left=[
        ("H", "XT60 lead, 12 AWG"),
        P("XT60P", "XT60+", "power_in"), P("XT60N", "XT60-"),
        ("H", "FMU-PWM-in (10-pin)"),
        P("FIN_V", "VSERVO")] + [P("FIN_CH%d" % i, "CH%d" % i, "input") for i in range(1, 9)] + [
        P("FIN_GND", "GND"),
        ("H", "PWR1 (6-pin), 5.2 V"),
        P("PWR1_VCC", "VCC", "power_out"), P("PWR1_CUR", "CURRENT", "output"),
        P("PWR1_VOLT", "VOLTAGE", "output"), P("PWR1_GND", "GND"),
        ("H", "Unused in Phase 1"),
        P("PWR2", "PWR2"), P("IOIN", "I/O-PWM-in"), P("MHOLES", "M1-M8(holes)"),
        P("CAPIN", "CAP&ADC-in"), P("CAPOUT", "CAP&ADC-out")],
        right=[
        ("H", "ESC pads, all common"),
        P("BP", "B+", "power_out"), P("BN", "GND", "power_out"),
        ("H", "FMU-PWM-out header")] + [P("OUT_S%d" % i, "S%d" % i, "output") for i in range(1, 9)] + [
        P("OUT_GND", "-row"), P("OUT_V", "+row(no_5V)")]),

    "ESC": dict(desc="Brushless ESC, no BEC", left=[
        P("VP", "V+", "power_in"), P("VN", "V-", "power_in"),
        P("SIG", "SIG", "input"), P("SGND", "SIG-GND")],
        right=[P("A", "A", "output"), P("B", "B", "output"), P("C", "C", "output")]),

    "Motor": dict(desc="Brushless motor", left=[P("A", "A"), P("B", "B"), P("C", "C")]),

    "Pixhawk6C": dict(desc="Holybro Pixhawk 6C flight controller", left=[
        ("H", "GPS1 (10-pin GH)"),
        P("GPS1_1", "1:VCC", "power_out"), P("GPS1_2", "2:TX1(out)", "output"),
        P("GPS1_3", "3:RX1(in)", "input"), P("GPS1_4", "4:SCL1", "bidirectional"),
        P("GPS1_5", "5:SDA1", "bidirectional"), P("GPS1_6", "6:SAFETY_SWITCH", "input"),
        P("GPS1_7", "7:SAFETY_SWITCH_LED", "output"), P("GPS1_8", "8:IO_VDD_3V3", "power_out"),
        P("GPS1_9", "9:BUZZER-", "output"), P("GPS1_10", "10:GND"),
        ("H", "TELEM3 (6-pin GH)"),
        P("TELEM3_1", "1:VCC", "power_out"), P("TELEM3_2", "2:USART2_TX(out)", "output"),
        P("TELEM3_3", "3:USART2_RX(in)", "input"), P("TELEM3_4", "4:NC"), P("TELEM3_5", "5:NC"),
        P("TELEM3_6", "6:GND"),
        ("H", "Unused in Phase 1")] + [P(n, n) for n in
        ("POWER2", "TELEM1", "TELEM2", "GPS2", "I2C", "CAN1", "CAN2")],
        right=[
        ("H", "POWER1 (6-pin GH)"),
        P("POWER1_1", "1-2:VDD5V_BRICK", "power_in"), P("POWER1_3", "3:CURRENT", "input"),
        P("POWER1_4", "4:VOLTAGE", "input"), P("POWER1_5", "5-6:GND", "power_in"),
        ("H", "FMU PWM OUT (AUX)"),
        P("FMU_1", "1:VDD_Servo")] + [P("FMU_%d" % (i + 1), "%d:FMU_CH%d" % (i + 1, i), "output")
                                      for i in range(1, 9)] + [
        P("FMU_10", "10:GND"),
        ("H", "Unused in Phase 1")] + [P(n.replace("/", "_"), n) for n in
        ("I/O_PWM_OUT", "PPM/SBUS_RC", "DSM_RC", "SBUS_OUT", "USB", "FMU_DEBUG", "I/O_DEBUG")]),

    "GPS_M10": dict(desc="Holybro M10 GPS, standard 10-pin", right=[
        P("1", "1:VCC_5V", "power_in"), P("2", "2:RX", "input"), P("3", "3:TX", "output"),
        P("4", "4:SCL", "bidirectional"), P("5", "5:SDA", "bidirectional"),
        P("6", "6:SAFETY_SWITCH(V1)"), P("7", "7:SAFETY_SWITCH_LED(V1)"),
        P("8", "8:VDD_3V3(V1)"), P("9", "9:BUZZER-(V1)"), P("10", "10:GND", "power_in")]),

    "ELRS_RX": dict(desc="ExpressLRS receiver, CRSF", right=[
        P("5V", "5V", "power_in"), P("GND", "GND", "power_in"), P("TX", "TX", "output"),
        P("RX", "RX", "input"), P("EXTV", "Ext-V")]),
}
CHAR = 1.12          # mm per character at 1.27 mm text, a deliberately wide estimate


def geometry(sym):
    left, right = sym.get("left", []), sym.get("right", [])
    rows = max(len(left), len(right))
    # headings are bold, so count them wider than pin names
    width = lambda side: max([len(r[1]) * (1.2 if r[0] == "H" else 1.0) for r in side if r] or [0])
    need = (width(left) + width(right)) * CHAR + 8
    w = 2 * int(-(-need // (2 * G)))                       # body width in grid units, even
    w = max(w, 12)
    top = rows + 1                                         # grid units, body is symmetric
    pins = []                                              # (num, name, type, side, x, y) in mm, y up
    for side, rows_ in (("L", left), ("R", right)):
        for k, r in enumerate(rows_):
            if r and r[0] != "H":
                x = (-(w // 2) - 2) * G if side == "L" else ((w // 2) + 2) * G
                pins.append((r[0], r[1], r[2], side, x, (rows - 1 - 2 * k) * G))
    heads = [(side, (rows - 1 - 2 * k) * G, r[1])
             for side, rows_ in (("L", left), ("R", right)) for k, r in enumerate(rows_)
             if r and r[0] == "H"]
    return dict(w=w * G, top=top * G, pins=pins, heads=heads)


def symbol_sexpr(name, sym, prefix=""):
    g = geometry(sym)
    hw, top = g["w"] / 2, g["top"]
    out = ['(symbol %s (pin_numbers hide) (pin_names (offset 1.016)) (exclude_from_sim no) '
           '(in_bom yes) (on_board yes)' % q(prefix + name),
           '  (property "Reference" "J" (at 0 %s 0) %s)' % (f(top + 3.81), FONT),
           '  (property "Value" %s (at 0 %s 0) %s)' % (q(name), f(top + 1.27), FONT),
           '  (property "Footprint" "" (at 0 0 0) %s)' % FONT_HIDE,
           '  (property "Datasheet" "" (at 0 0 0) %s)' % FONT_HIDE,
           '  (property "Description" %s (at 0 0 0) %s)' % (q(sym["desc"]), FONT_HIDE),
           '  (symbol %s' % q("%s_0_1" % name),
           '    (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) '
           '(fill (type background)))' % (f(-hw), f(top), f(hw), f(-top))]
    for side, y, s in g["heads"]:
        x, just = (-hw + 1.27, "left") if side == "L" else (hw - 2.54, "right")
        out.append('    (text %s (at %s %s 0) (effects (font (size 1.27 1.27) (bold yes)) (justify %s)))'
                   % (q(s), f(x), f(y), just))
    out.append('  )')
    out.append('  (symbol %s' % q("%s_1_1" % name))
    for num, pname, etype, side, x, y in g["pins"]:
        out.append('    (pin %s line (at %s %s %d) (length 2.54) (name %s %s) (number %s %s))'
                   % (etype, f(x), f(y), 0 if side == "L" else 180, q(pname), FONT, q(num), FONT))
    out.append('  )')
    out.append(')')
    return "\n".join(out)


# ---------------------------------------------------------------- placement and nets
# (ref, symbol, value, x, y, {pin number: net name or None for a no-connect})
NC = None
PARTS = [
    ("J1", "Battery", "Battery: OVONIC 6S 5000 mAh 130C, XT60", 50.8, 60.96,
     {"BATP": "BAT_P", "BATN": "BAT_N", "BAL": NC}),
    ("J2", "PM07", "PM07 power module + PDB (Holybro SKU 15008)", 142.24, 88.9, dict(
        [("XT60P", "BAT_P"), ("XT60N", "BAT_N"), ("FIN_V", "SERVO_RAIL"), ("FIN_GND", "GND"),
         ("PWR1_VCC", "FC_5V"), ("PWR1_CUR", "BATT_CURR"), ("PWR1_VOLT", "BATT_VOLT"), ("PWR1_GND", "GND"),
         ("PWR2", NC), ("IOIN", NC), ("MHOLES", NC), ("CAPIN", NC), ("CAPOUT", NC),
         ("BP", "VBAT_ESC"), ("BN", "GND"), ("OUT_GND", "GND"), ("OUT_V", NC)]
        + [("FIN_CH%d" % i, "AUX%d_PWM" % i) for i in range(1, 9)]
        + [("OUT_S%d" % i, "MOT%d_PWM" % i if i <= 4 else NC) for i in range(1, 9)])),
    ("J11", "Pixhawk6C", "Pixhawk 6C, plastic (Holybro SKU 11054), ArduPilot", 154.94, 171.45, dict(
        [("GPS1_1", "GPS_5V"), ("GPS1_2", "GPS_RX"), ("GPS1_3", "GPS_TX"), ("GPS1_4", "MAG_SCL"),
         ("GPS1_5", "MAG_SDA"), ("GPS1_6", "SAFETY_SW"), ("GPS1_7", "SAFETY_LED"),
         ("GPS1_8", "SAFETY_3V3"), ("GPS1_9", "BUZZER"), ("GPS1_10", "GND"),
         ("TELEM3_1", "ELRS_5V"), ("TELEM3_2", "ELRS_RX"), ("TELEM3_3", "ELRS_TX"),
         ("TELEM3_4", NC), ("TELEM3_5", NC), ("TELEM3_6", "GND"),
         ("POWER1_1", "FC_5V"), ("POWER1_3", "BATT_CURR"), ("POWER1_4", "BATT_VOLT"), ("POWER1_5", "GND"),
         ("FMU_1", "SERVO_RAIL"), ("FMU_10", "GND")]
        + [("FMU_%d" % (i + 1), "AUX%d_PWM" % i) for i in range(1, 9)]
        + [(n, NC) for n in ("POWER2", "TELEM1", "TELEM2", "GPS2", "I2C", "CAN1", "CAN2", "I_O_PWM_OUT",
                             "PPM_SBUS_RC", "DSM_RC", "SBUS_OUT", "USB", "FMU_DEBUG", "I_O_DEBUG")])),
    ("J12", "GPS_M10", "GPS + compass: Holybro M10, IST8310, 10-pin (SKU 12040)", 50.8, 152.4,
     {"1": "GPS_5V", "2": "GPS_RX", "3": "GPS_TX", "4": "MAG_SCL", "5": "MAG_SDA", "6": "SAFETY_SW",
      "7": "SAFETY_LED", "8": "SAFETY_3V3", "9": "BUZZER", "10": "GND"}),
    ("J13", "ELRS_RX", "ELRS receiver: RadioMaster RP3-H (on TELEM3)", 50.8, 190.5,
     {"5V": "ELRS_5V", "GND": "GND", "TX": "ELRS_TX", "RX": "ELRS_RX", "EXTV": NC}),
]
# ArduPilot Quad X, confirmed only by a props-off motor test
QUADX = [("front-right", "CCW"), ("rear-left", "CCW"), ("front-left", "CW"), ("rear-right", "CW")]
for i, (pos, spin) in enumerate(QUADX):
    n, y = i + 1, 43.18 + i * 30.48
    PARTS.append(("J%d" % (2 + n), "ESC", "ESC %d / AUX %d / %s: XRotor PRO 50A" % (n, n, spin), 236.22, y,
                  {"VP": "VBAT_ESC", "VN": "GND", "SIG": "MOT%d_PWM" % n, "SGND": "GND",
                   "A": "M%d_A" % n, "B": "M%d_B" % n, "C": "M%d_C" % n}))
    PARTS.append(("J%d" % (6 + n), "Motor", "Motor %d %s %s: Avenger 3110 730KV" % (n, pos, spin), 307.34, y,
                  {"A": "M%d_A" % n, "B": "M%d_B" % n, "C": "M%d_C" % n}))

NOTES = [
    (20.32, 17.78, 2.54, True, "SBI drone, Phase 1: wiring schematic"),
    (20.32, 22.86, 1.5, False, "Battery disconnected for all assembly and continuity checks.  "
                               "As of 2026-09-30.  Ground truth: wiring/wiring-table.md"),
    (210.82, 152.4, 1.27, False, "\n".join([
        "NET GLOSSARY",
        "BAT_P, BAT_N: battery + and - to the PM07 XT60 lead (XT60 plug).",
        "VBAT_ESC, GND: PM07 B+ and GND pads to each ESC (soldered). The PM07 joins its",
        "    input to these inside the board, through its current sensor.",
        "Mn_A, Mn_B, Mn_C: ESC n to motor n phase leads (3.5 mm bullets). Phase order is arbitrary.",
        "AUXn_PWM: 6C FMU PWM OUT channel n to PM07 FMU-PWM-in (10-pin cable).",
        "MOTn_PWM: PM07 FMU-PWM-out Sn to ESC n signal lead (plug-in).",
        "SERVO_RAIL: VDD_Servo in the 10-pin cable. Unpowered: PM07 supplies no 5 V there.",
        "FC_5V, BATT_CURR, BATT_VOLT: PM07 PWR1 to 6C POWER1 (6-pin cable).",
        "GPS_5V, GPS_TX, GPS_RX, MAG_SCL, MAG_SDA, SAFETY_*, BUZZER: M10 to 6C GPS1 (10-pin cable).",
        "ELRS_5V, ELRS_TX, ELRS_RX: RP3-H to 6C TELEM3 (custom cable).",
        "    xxx_TX is sent by the peripheral; xxx_RX is received by it.",
        "",
        "MOTOR MAP (ArduPilot Quad X; confirm with a props-off motor test)",
        "1 front-right CCW, AUX 1 (SERVO9)      2 rear-left CCW, AUX 2 (SERVO10)",
        "3 front-left CW, AUX 3 (SERVO11)       4 rear-right CW, AUX 4 (SERVO12)",
        "Spin direction is set by each ESC's DIP switch.",
        "",
        "NO-CONNECT FLAGS",
        "6C: each unused port is one pin. TELEM1 is kept for a SiK radio, TELEM2 for the",
        "    Phase 2 companion computer. I/O PWM OUT (MAIN) is unused: motors are on AUX.",
        "6C TELEM3 pins 4-5: not connected on the 6C.",
        "PM07: PWR2, I/O PWM-in, M1-M8 holes, CAP&ADC unused. FMU-PWM-out S5-S8: four ESCs only.",
        "M10 GPS pins 6-9 are NC on the V2 unit (no safety switch, buzzer or LED).",
        "Battery balance lead: charger only. RP3-H Ext-V: unused.",
        "",
        "ArduPilot: SERVO9-12_FUNCTION = 33-36, SERVO1-4_FUNCTION = 0, SERIAL5_PROTOCOL = 23.",
        "ESC power lead gauge: TBD."])),
]


# ---------------------------------------------------------------- schematic
def schematic(root):
    geo = {name: geometry(sym) for name, sym in SYMBOLS.items()}
    out = ['(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")',
           '  (uuid %s)' % q(root), '  (paper "A3")', '  (lib_symbols']
    for name, sym in SYMBOLS.items():
        out.append("\n".join("    " + line for line in symbol_sexpr(name, sym, LIB + ":").splitlines()))
    out.append('  )')
    stub = 5.08
    for ref, sname, value, X, Y, nets in PARTS:
        g = geo[sname]
        pins = {p[0]: p for p in g["pins"]}
        missing = set(pins) - set(nets)
        extra = set(nets) - set(pins)
        if missing or extra:
            raise ValueError("%s: pins without a net or NC %s, unknown pins %s" % (ref, missing, extra))
        for num, net in nets.items():
            _, _, _, side, px, py = pins[num]
            ax, ay = X + px, Y - py                    # symbol y is up, schematic y is down
            if net is None:
                out.append('  (no_connect (at %s %s) (uuid %s))' % (f(ax), f(ay), q(uid(ref, num, "nc"))))
                continue
            ex = ax - stub if side == "L" else ax + stub
            out.append('  (wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))'
                       % (f(ax), f(ay), f(ex), f(ay), q(uid(ref, num, "w"))))
            angle, just = (180, "right") if side == "L" else (0, "left")
            out.append('  (label %s (at %s %s %d) (fields_autoplaced yes) '
                       '(effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))'
                       % (q(net), f(ex), f(ay), angle, just, q(uid(ref, num, "l"))))
    for i, (x, y, size, bold, s) in enumerate(NOTES):
        out.append('  (text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) '
                   '(justify left top)) (uuid %s))'
                   % (q(s), f(x), f(y), f(size), f(size), " (bold yes)" if bold else "", q(uid("note", i))))
    for ref, sname, value, X, Y, nets in PARTS:
        g = geo[sname]
        out.append('  (symbol (lib_id %s) (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom yes) '
                   '(on_board yes) (dnp no) (uuid %s)' % (q(LIB + ":" + sname), f(X), f(Y), q(uid(ref))))
        out.append('    (property "Reference" %s (at %s %s 0) %s)' % (q(ref), f(X), f(Y - g["top"] - 3.81), FONT))
        out.append('    (property "Value" %s (at %s %s 0) %s)' % (q(value), f(X), f(Y - g["top"] - 1.27), FONT))
        for prop in ("Footprint", "Datasheet"):
            out.append('    (property "%s" "" (at %s %s 0) %s)' % (prop, f(X), f(Y), FONT_HIDE))
        out.append('    (property "Description" %s (at %s %s 0) %s)'
                   % (q(SYMBOLS[sname]["desc"]), f(X), f(Y), FONT_HIDE))
        for p in g["pins"]:
            out.append('    (pin %s (uuid %s))' % (q(p[0]), q(uid(ref, p[0], "pin"))))
        out.append('    (instances (project %s (path %s (reference %s) (unit 1))))'
                   % (q(LIB), q("/" + root), q(ref)))
        out.append('  )')
    out.append('  (sheet_instances (path "/" (page "1")))')
    out.append(')')
    return "\n".join(out) + "\n"


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    root = uid("root")
    lib = ['(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")']
    for name, sym in SYMBOLS.items():
        lib.append("\n".join("  " + line for line in symbol_sexpr(name, sym).splitlines()))
    lib.append(")")
    write(os.path.join(here, LIB + ".kicad_sym"), "\n".join(lib) + "\n")
    write(os.path.join(here, LIB + ".kicad_sch"), schematic(root))
    write(os.path.join(here, "sym-lib-table"),
          '(sym_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")'
          '(options "")(descr "SBI drone system-level blocks"))\n)\n' % (LIB, LIB))
    write(os.path.join(here, LIB + ".kicad_pro"), json.dumps(
        {"meta": {"filename": LIB + ".kicad_pro", "version": 1},
         "sheets": [[root, "Root"]], "boards": [], "libraries": {"pinned_symbol_libs": []}},
        indent=2) + "\n")
    n_labels = sum(1 for p in PARTS for v in p[5].values() if v)
    n_nc = sum(1 for p in PARTS for v in p[5].values() if v is None)
    print("symbols %d  labels %d  no-connects %d" % (len(PARTS), n_labels, n_nc))
