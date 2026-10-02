# -*- coding: utf-8 -*-
"""Rebuild both wiring figures and run every check. Exits 1 if anything fails.

  1. Block diagram: phase1_wiring.py -> out/phase1-wiring.svg, .drawio, .png (layout linter)
  2. Schematic: ERC, netlist check against kicad/expected-nets.txt, PDF and PNG export

Needs: pip install playwright pymupdf pillow; playwright install chromium; KiCad 9 or 10.
Run: python build.py
"""
import glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join("kicad", "sbi_phase1.kicad_sch")


def kicad_cli():
    found = shutil.which("kicad-cli")
    if found:
        return found
    hits = sorted(glob.glob(r"C:\Program Files\KiCad\*\bin\kicad-cli.exe"))
    if not hits:
        sys.exit("kicad-cli not found: install KiCad 9 or 10, or put kicad-cli on PATH")
    return hits[-1]


def run(*cmd):
    print("$ " + " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)), flush=True)
    return subprocess.run(cmd).returncode


def rasterise_pdf(pdf, png, margin=60):
    """PyMuPDF renders PDF completely (unlike its SVG support), so rasterise from the PDF."""
    import pymupdf
    from PIL import Image, ImageChops
    page = pymupdf.open(pdf)[0]
    zoom = 4590 / page.rect.width                      # about 4600 px wide for the page
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False).save(png)
    im = Image.open(png).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, im.getpixel((0, 0)))).getbbox()
    im.crop((max(box[0] - margin, 0), max(box[1] - margin, 0),
             min(box[2] + margin, im.width), min(box[3] + margin, im.height))).save(png)


def main():
    os.chdir(HERE)
    os.makedirs("out", exist_ok=True)
    cli, failed = kicad_cli(), []

    if run(sys.executable, "phase1_wiring.py"):
        failed.append("block diagram linter")

    run(cli, "sch", "erc", "--format", "json", "-o", "out/erc.json", SCH)
    erc = json.load(open("out/erc.json", encoding="utf-8"))
    violations = [v for s in erc["sheets"] for v in s["violations"]]
    for v in violations:
        print("  ERC %s %s: %s" % (v["severity"], v["type"],
                                   "; ".join(i["description"] for i in v["items"])))
    print("  ERC: %d violations" % len(violations))
    if violations:
        failed.append("ERC")

    run(cli, "sch", "export", "netlist", "--format", "kicadxml", "-o", "out/net.xml", SCH)
    if run(sys.executable, "check_netlist.py", "out/net.xml", "kicad/expected-nets.txt"):
        failed.append("netlist check")

    if run(cli, "sch", "export", "pdf", "-e", "-n", "-o", "out/phase1-schematic.pdf", SCH):
        failed.append("PDF export")
    else:
        rasterise_pdf("out/phase1-schematic.pdf", "out/phase1-schematic.png")

    print("\nFAILED: " + ", ".join(failed) if failed else "\nall checks passed. Now look at both PNGs.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
