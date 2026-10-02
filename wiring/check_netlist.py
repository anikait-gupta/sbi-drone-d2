# -*- coding: utf-8 -*-
"""Compare a KiCad schematic's nets with an expected net list, so the schematic cannot drift silently.

  kicad-cli sch export netlist --format kicadxml -o net.xml design.kicad_sch
  python check_netlist.py net.xml --dump > expected-nets.txt    # bootstrap once, then review by hand
  python check_netlist.py net.xml expected-nets.txt             # exit 1 on any difference

expected-nets.txt holds one net per line, "NET_NAME: REF.PIN REF.PIN ...". '#' starts a comment.
Pins match on reference designator and pin number; --dump writes value and pin name as a trailing
comment so the file can be reviewed against the wiring table by a human.
"""
import re, sys, xml.etree.ElementTree as ET

def natural(s):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", s)]

def read_netlist(path):
    root = ET.parse(path).getroot()
    values = {c.get("ref"): (c.findtext("value") or "") for c in root.iter("comp")}
    nets, unnamed = {}, []
    for n in root.iter("net"):
        name = n.get("name").lstrip("/")
        if name.startswith("unconnected-"):
            continue                              # a single pin with nothing on it
        members = sorted(((nd.get("ref"), nd.get("pin"), nd.get("pinfunction") or "")
                          for nd in n.iter("node")), key=lambda m: (natural(m[0]), natural(m[1])))
        if name.startswith("Net-("):
            unnamed.append(name)                  # joined by wire but never labelled
        nets[name] = members
    return nets, values, unnamed

def read_expected(path):
    exp = {}
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if line:
            name, _, pins = line.partition(":")
            exp[name.strip()] = set(pins.split())
    return exp

def main(argv):
    nets, values, unnamed = read_netlist(argv[1])
    if len(argv) > 2 and argv[2] == "--dump":
        for name in sorted(nets, key=natural):
            print("%s: %s" % (name, " ".join("%s.%s" % (r, p) for r, p, _ in nets[name])))
            print("  # " + ", ".join("%s %s %s" % (r, values.get(r, ""), f) for r, _, f in nets[name]))
        return 0
    exp = read_expected(argv[2])
    act = {k: {"%s.%s" % (r, p) for r, p, _ in v} for k, v in nets.items()}
    problems = ["net missing from schematic: %s" % k for k in sorted(set(exp) - set(act), key=natural)]
    problems += ["net not in expected list: %s" % k for k in sorted(set(act) - set(exp), key=natural)]
    for k in sorted(set(exp) & set(act), key=natural):
        for p in sorted(exp[k] - act[k], key=natural):
            problems.append("%s: expected %s, not connected" % (k, p))
        for p in sorted(act[k] - exp[k], key=natural):
            problems.append("%s: %s connected, not expected" % (k, p))
    problems += ["unlabelled net, give it a name: %s" % u for u in unnamed]
    print("\n".join("  " + p for p in problems) if problems else "  netlist matches")
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
