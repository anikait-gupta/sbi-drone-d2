# Phase 1 wiring figures

There are two figures of the same wiring, built from two separate sources. The method comes from `drone-docs/outputs/wiring-pipeline-handoff.md`.

| Figure | For | Source of truth | Output |
| :-- | :-- | :-- | :-- |
| Block diagram | Assembly: what connects to what, colour coded by rail | `phase1_wiring.py`, drawn by `wiring_diagram.py` | `out/phase1-wiring.svg`, `.drawio`, `.png` |
| Schematic | Verification: pin names and named nets | `kicad/sbi_phase1.kicad_sch` and `kicad/sbi_phase1.kicad_sym` | `out/phase1-schematic.pdf`, `.png` |

Both are drawn from `wiring-table.md`, which cites a source for every conductor.

## Rebuild and check

```
pip install playwright pymupdf pillow
playwright install chromium
python build.py
```

`build.py` runs the layout linter, KiCad ERC, and the netlist check against `kicad/expected-nets.txt`, then exports the PDF and PNG. It exits 1 if any check fails. After it passes, look at both PNGs: the checks cover geometry and connectivity, not whether the figure is correct.

## Changing a wiring fact

1. Change it in `wiring-table.md`.
2. Change it in `phase1_wiring.py`.
3. Change it in the schematic (KiCad GUI, or the text file), then the matching line in `kicad/expected-nets.txt`.
4. Run `python build.py`, then grep all of the above for the old value.

`kicad/gen_schematic.py` wrote the first version of the KiCad files. Once anyone edits the schematic in KiCad, do not run it again: it overwrites the schematic, the library and the project file.

The `.drawio` file is for anyone who wants to hand-tweak the layout in diagrams.net. A hand edit is lost the next time `phase1_wiring.py` runs.
