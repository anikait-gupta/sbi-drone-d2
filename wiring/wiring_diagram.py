# -*- coding: utf-8 -*-
"""Wiring block diagram engine: one geometry model -> SVG and draw.io, plus a layout linter.

Importing this module has no side effects. Nothing is written until write() is called.

Layout rules the model is built to:
  - every edge is orthogonal; a diagonal segment raises
  - collinear runs share an exact centreline, so no run has a 2 or 3 px kink
  - fan-outs use evenly spaced buses and symmetric jogs
  - where a horizontal run crosses a vertical run of another edge, the horizontal hops it
"""
import html, os, xml.sax.saxutils as su

# Colour means rail. Keep this mapping identical across every figure in the document.
PWR, FIVE, SIG, DATA, GREY = "#C62828", "#EF6C00", "#1565C0", "#6A1B9A", "#546E7A"
FILL = {"pwr": ("#FDECEA", PWR), "five": ("#FFF3E0", FIVE), "sig": ("#E8F1FC", SIG),
        "data": ("#F5EAF9", DATA), "mech": ("#ECEFF1", GREY), "note": ("#FFFDF2", "#B08D00")}
FONT = "Helvetica,Arial,sans-serif"
HOP_R = 5.0


class Diagram:
    def __init__(self, width, height):
        self.W, self.H = width, height
        self.nodes, self.edges, self.texts = [], [], []
        self.containers = set()      # boxes other things sit inside: legend, notes, the FC body

    # ---------------- model ----------------
    def node(self, nid, x, y, w, h, title="", sub=(), kind="sig", rx=8, dash=False,
             tsize=13, ssize=10.5, container=False):
        """A box. kind picks the colour from FILL. dash=True marks an intentionally empty port."""
        self.nodes.append(dict(id=nid, x=x, y=y, w=w, h=h, title=title, sub=list(sub), kind=kind,
                               rx=rx, dash=dash, tsize=tsize, ssize=ssize))
        if container:
            self.containers.add(nid)

    def edge(self, pts, color=SIG, width=2, dash=False, label=None, lx=None, ly=None,
             arrow=True, hop=True):
        """A wire through orthogonal waypoints. The arrow sits on the last point."""
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if x1 != x2 and y1 != y2:
                raise ValueError("segment is not orthogonal: %r -> %r" % ((x1, y1), (x2, y2)))
        self.edges.append(dict(pts=pts, color=color, width=width, dash=dash, label=label,
                               lx=lx, ly=ly, arrow=arrow, hop=hop))

    def text(self, x, y, s, size=13, weight="normal", color="#263238", anchor="start"):
        """Free text. weight is normal, bold or italic. anchor is start, middle or end."""
        self.texts.append(dict(x=x, y=y, s=s, size=size, weight=weight, color=color, anchor=anchor))

    # ---------------- line hops ----------------
    def _verticals(self):
        out = []
        for idx, e in enumerate(self.edges):
            for (x1, y1), (x2, y2) in zip(e["pts"], e["pts"][1:]):
                if x1 == x2 and y1 != y2:
                    out.append((idx, x1, min(y1, y2), max(y1, y2)))
        return out

    def _hops(self, verts, idx, x1, y, x2):
        lo, hi = min(x1, x2), max(x1, x2)
        out = [vx for (vi, vx, vy1, vy2) in verts
               if vi != idx and lo + 6 < vx < hi - 6 and vy1 + 2 < y < vy2 - 2]
        return sorted(out, reverse=(x2 < x1))

    @staticmethod
    def _head(e):
        """Arrowhead size and final direction. Heads are plain filled paths, not <marker>:
        PyMuPDF and some other rasterisers drop markers without warning."""
        (x1, y1), (x2, y2) = e["pts"][-2], e["pts"][-1]
        ux, uy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
        return max(9.0, 4.5 * e["width"]), max(4.0, 2.2 * e["width"]), ux, uy

    def _arrow(self, e):
        L, hw, ux, uy = self._head(e)
        x2, y2 = e["pts"][-1]
        bx, by = x2 - ux * L, y2 - uy * L
        return ('<path d="M %g %g L %g %g L %g %g z" fill="%s"/>'
                % (x2, y2, bx - uy * hw, by + ux * hw, bx + uy * hw, by - ux * hw, e["color"]))

    def _svg_path(self, verts, e, idx):
        pts = list(e["pts"])
        if e["arrow"]:                    # stop the line under the head so the round cap cannot poke out
            L, _, ux, uy = self._head(e)
            pts[-1] = (pts[-1][0] - ux * L * 0.6, pts[-1][1] - uy * L * 0.6)
        sx, sy = pts[0]
        d = ["M %g %g" % (sx, sy)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if e["hop"] and y1 == y2:
                fwd = x2 > x1
                for hx in self._hops(verts, idx, x1, y1, x2):
                    d.append("L %g %g" % (hx - HOP_R if fwd else hx + HOP_R, y1))
                    d.append("A %g %g 0 0 %d %g %g" % (HOP_R, HOP_R, 1 if fwd else 0,
                                                       hx + HOP_R if fwd else hx - HOP_R, y1))
            d.append("L %g %g" % (x2, y2))
        return " ".join(d)

    # ---------------- SVG ----------------
    def svg(self):
        verts = self._verticals()
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
               % (self.W, self.H, self.W, self.H)]
        out.append('<rect width="%d" height="%d" fill="#FFFFFF"/>' % (self.W, self.H))
        for n in self.nodes:
            fill, stroke = FILL[n["kind"]]
            dd = ' stroke-dasharray="6 4"' if n["dash"] else ""
            out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" '
                       'stroke-width="1.6"%s/>' % (n["x"], n["y"], n["w"], n["h"], n["rx"], fill, stroke, dd))
            if n["title"]:
                cx = n["x"] + n["w"] / 2.0
                ty = n["y"] + 22 if n["sub"] else n["y"] + n["h"] / 2.0 + n["tsize"] * 0.36
                out.append('<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="bold" '
                           'fill="%s" text-anchor="middle">%s</text>'
                           % (cx, ty, FONT, n["tsize"], stroke, su.escape(n["title"])))
                for i, s in enumerate(n["sub"]):
                    out.append('<text x="%g" y="%g" font-family="%s" font-size="%g" fill="#546E7A" '
                               'text-anchor="middle">%s</text>'
                               % (cx, ty + 17 + i * 13.5, FONT, n["ssize"], su.escape(s)))
        for idx, e in enumerate(self.edges):
            dd = ' stroke-dasharray="7 5"' if e["dash"] else ""
            out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round" '
                       'stroke-linecap="round"%s/>'
                       % (self._svg_path(verts, e, idx), e["color"], e["width"], dd))
            if e["arrow"]:
                out.append(self._arrow(e))
            if e["label"]:
                out.append('<text x="%g" y="%g" font-family="%s" font-size="10" fill="%s" '
                           'text-anchor="middle">%s</text>'
                           % (e["lx"], e["ly"], FONT, e["color"], su.escape(e["label"])))
        for t in self.texts:
            style = ' font-style="italic"' if t["weight"] == "italic" else ""
            weight = "bold" if t["weight"] == "bold" else "normal"
            out.append('<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="%s"%s '
                       'fill="%s" text-anchor="%s">%s</text>'
                       % (t["x"], t["y"], FONT, t["size"], weight, style, t["color"], t["anchor"],
                          su.escape(t["s"])))
        out.append("</svg>")
        return "\n".join(out)

    # ---------------- draw.io ----------------
    def drawio(self, name="Wiring"):
        """Same geometry as svg(). Edge labels are placed by draw.io at the edge midpoint, not at lx, ly."""
        cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
        for n in self.nodes:
            fill, stroke = FILL[n["kind"]]
            st = ("rounded=1;arcSize=%d;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;fontColor=%s;"
                  "align=center;verticalAlign=middle;fontSize=%g;spacing=4;%s"
                  % (18 if n["rx"] > 6 else 30, fill, stroke, stroke, n["tsize"],
                     "dashed=1;" if n["dash"] else ""))
            lab = ""
            if n["title"]:
                lab = "<b>%s</b>" % html.escape(n["title"]) + "".join(
                    '<br><font style="font-size:%gpx" color="#546E7A">%s</font>' % (n["ssize"], html.escape(s))
                    for s in n["sub"])
            cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">'
                         '<mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/></mxCell>'
                         % (n["id"], html.escape(lab), st, n["x"], n["y"], n["w"], n["h"]))
        for i, t in enumerate(self.texts):
            align = {"start": "left", "middle": "center", "end": "right"}[t["anchor"]]
            v = html.escape(t["s"])
            v = {"bold": "<b>%s</b>", "italic": "<i>%s</i>"}.get(t["weight"], "%s") % v
            ww = 700 if t["anchor"] == "start" else 500
            xx = {"start": t["x"], "middle": t["x"] - ww / 2.0, "end": t["x"] - ww}[t["anchor"]]
            cells.append('<mxCell id="t%d" value="%s" style="text;html=1;align=%s;verticalAlign=middle;'
                         'fontSize=%g;fontColor=%s;" vertex="1" parent="1"><mxGeometry x="%g" y="%g" '
                         'width="%g" height="18" as="geometry"/></mxCell>'
                         % (i, html.escape(v), align, t["size"], t["color"], xx, t["y"] - 12, ww))
        for i, e in enumerate(self.edges):
            st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=%s;strokeWidth=%g;endArrow=%s;"
                  "endFill=1;fontSize=10;fontColor=%s;%s%s"
                  % (e["color"], e["width"], "block" if e["arrow"] else "none", e["color"],
                     "jumpStyle=arc;jumpSize=8;" if e["hop"] else "", "dashed=1;" if e["dash"] else ""))
            p0, p1 = e["pts"][0], e["pts"][-1]
            mid = "".join('<mxPoint x="%g" y="%g"/>' % p for p in e["pts"][1:-1])
            cells.append('<mxCell id="e%d" value="%s" style="%s" edge="1" parent="1">'
                         '<mxGeometry relative="1" as="geometry"><mxPoint x="%g" y="%g" as="sourcePoint"/>'
                         '<mxPoint x="%g" y="%g" as="targetPoint"/><Array as="points">%s</Array>'
                         '</mxGeometry></mxCell>'
                         % (i, html.escape(e["label"] or ""), st, p0[0], p0[1], p1[0], p1[1], mid))
        return ('<mxfile host="app.diagrams.net" type="device"><diagram name="%s">'
                '<mxGraphModel grid="1" gridSize="10" guides="1" connect="1" arrows="1" page="1" '
                'pageWidth="%d" pageHeight="%d"><root>%s</root></mxGraphModel></diagram></mxfile>'
                % (html.escape(name), self.W + 20, self.H + 10, "".join(cells)))

    def write(self, svg_path, drawio_path=None):
        # newline="\n" so output is byte-identical across Windows, macOS and Linux
        with open(svg_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.svg())
        if drawio_path:
            with open(drawio_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.drawio(os.path.splitext(os.path.basename(drawio_path))[0]))

    # ---------------- layout linter ----------------
    def check(self, em=0.60, pad=3):
        """Box overlap, text clipped by its box, a wire through text, jogs under 10 px.
        Deliberately conservative: em=0.60 assumes a wider face than Helvetica, because the
        rasteriser may substitute one. A flagged clip can be a false positive; confirm on the render."""
        wid = lambda s, size: len(s) * size * em
        def tbox(t):
            w = wid(t["s"], t["size"])
            x1 = {"start": t["x"], "middle": t["x"] - w / 2, "end": t["x"] - w}[t["anchor"]]
            return (x1 - pad, t["y"] - t["size"] * 0.80 - pad, x1 + w + pad, t["y"] + t["size"] * 0.25 + pad)
        nbox = lambda n: (n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"])
        issues = []
        for i, a in enumerate(self.nodes):
            for b in self.nodes[i + 1:]:
                if a["id"] in self.containers or b["id"] in self.containers:
                    continue
                ax1, ay1, ax2, ay2 = nbox(a); bx1, by1, bx2, by2 = nbox(b)
                if min(ax2, bx2) > max(ax1, bx1) and min(ay2, by2) > max(ay1, by1):
                    issues.append("box overlap: %s / %s" % (a["id"], b["id"]))
        for n in self.nodes:
            for s, sz in ([(n["title"], n["tsize"])] if n["title"] else []) + [(x, n["ssize"]) for x in n["sub"]]:
                if wid(s, sz) > n["w"] - 12:
                    issues.append("text clipped by %s: %r" % (n["id"], s))
        labels = list(self.texts) + [dict(s=e["label"], x=e["lx"], y=e["ly"], size=10, anchor="middle", _edge=e)
                                     for e in self.edges if e["label"]]
        for t in labels:
            tx1, ty1, tx2, ty2 = tbox(t)
            for c in self.nodes:
                if c["id"] not in self.containers:
                    continue
                x1, y1, x2, y2 = nbox(c)
                if y1 <= t["y"] <= y2 and (x1 - 30) < tx1 < x2 and (tx1 < x1 + 6 or tx2 > x2 - 6):
                    issues.append("text clipped by %s: %r" % (c["id"], t["s"]))
            for e in self.edges:
                if e is t.get("_edge"):
                    continue                      # a label may sit beside its own wire
                for (x1, y1), (x2, y2) in zip(e["pts"], e["pts"][1:]):
                    if min(x1, x2) <= tx2 and max(x1, x2) >= tx1 and min(y1, y2) <= ty2 and max(y1, y2) >= ty1:
                        issues.append("wire crosses text %r at (%g,%g)-(%g,%g)" % (t["s"], x1, y1, x2, y2))
        for e in self.edges:
            (ax, ay), (bx, by) = e["pts"][-2], e["pts"][-1]
            if e["arrow"] and abs(bx - ax) + abs(by - ay) < self._head(e)[0] + 6:
                issues.append("final segment at (%g,%g) too short for its arrowhead" % (bx, by))
            for (x1, y1), (x2, y2) in zip(e["pts"], e["pts"][1:]):
                d = abs(x2 - x1) + abs(y2 - y1)
                if d == 0:
                    issues.append("zero-length segment at (%g,%g)" % (x1, y1))
                elif d < 10:
                    issues.append("%g px jog at (%g,%g) reads as misalignment" % (d, x1, y1))
        return sorted(set(issues))


def rasterise(svg_path, png_path, scale=2.0, crop_margin=None):
    """SVG to PNG in headless Chromium: pip install playwright, then playwright install chromium.
    Do not use PyMuPDF for this. It silently drops stroke-dasharray, so dashed boxes and dashed
    runs come out solid, and it drops <marker>. crop_margin (px) trims white space, needs Pillow."""
    import re
    from playwright.sync_api import sync_playwright
    svg = open(svg_path, encoding="utf-8").read()
    svg = svg[svg.index("<svg"):]
    w, h = [int(float(v)) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups()]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        page.set_content('<html><body style="margin:0"><style>svg{display:block}</style>%s</body></html>' % svg)
        page.screenshot(path=png_path, clip={"x": 0, "y": 0, "width": w, "height": h})
        browser.close()
    if crop_margin is not None:
        from PIL import Image, ImageChops
        im = Image.open(png_path).convert("RGB")
        box = ImageChops.difference(im, Image.new("RGB", im.size, im.getpixel((0, 0)))).getbbox()
        if box:
            m = crop_margin
            im.crop((max(box[0] - m, 0), max(box[1] - m, 0),
                     min(box[2] + m, im.width), min(box[3] + m, im.height))).save(png_path)
