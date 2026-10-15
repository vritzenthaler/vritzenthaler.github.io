"""Generate the home page drawing: a pencil-style atlas of a manifold.

Math symbols are converted to SVG paths from the KaTeX fonts bundled with the `katex` gem,
so the browser downloads no extra font.

Usage: python3 tools/hero_atlas.py  (after `bundle install`)
"""

import glob
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
KATEX_FONTS = Path(glob.glob(str(ROOT / "vendor/bundle/ruby/*/gems/katex-*/vendor/katex/fonts"))[0])
OUT = ROOT / "assets" / "images" / "hero-atlas.svg"

BLUE = "#2455D6"
TERRE = "#B85F3D"
BRUME = "#A9BBC5"

FONT_FILES = {
    "it": "KaTeX_Math-Italic",
    "rm": "KaTeX_Main-Regular",
    "bb": "KaTeX_AMS-Regular",
    "cal": "KaTeX_Caligraphic-Regular",
    "big": "KaTeX_Size1-Regular",
}
FONTS = {k: TTFont(KATEX_FONTS / f"{v}.ttf") for k, v in FONT_FILES.items()}

SPACED = {"=", "∘"}


def glyph(font, char, x, y, size):
    f = FONTS[font]
    name = f.getBestCmap()[ord(char)]
    glyphs = f.getGlyphSet()
    scale = size / f["head"].unitsPerEm
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
    return pen.getCommands(), f["hmtx"][name][0] * scale


def formula(x, y, size, tokens, anchor="start"):
    """tokens: (text, font, level) with level 0 = base, -1 = subscript, 1 = superscript, "lim" = integral limit,
    or ("subsup", sub, sup) for a stacked subscript and superscript."""
    def layout(x0):
        paths, cx = [], x0
        for tok in tokens:
            if tok[0] == "subsup":
                widths = []
                for text, font, dy in [(tok[1], "it", 0.26), (tok[2], "rm", -0.42)]:
                    tx = cx
                    for ch in text:
                        d, adv = glyph(font, ch, tx, y + dy * size, size * 0.7)
                        paths.append(d)
                        tx += adv
                    widths.append(tx - cx)
                cx += max(widths) + 0.08 * size
                continue
            text, font, level = tok
            s = size * (1 if level == 0 else 0.68)
            dy = {0: 0, -1: 0.26 * size, 1: -0.42 * size, "lim": 0.62 * size}[level]
            if level == "lim":
                cx -= 0.12 * size
            for ch in text:
                if ch in SPACED:
                    cx += 0.26 * size
                d, adv = glyph(font, ch, cx, y + dy, s)
                paths.append(d)
                cx += adv + (0.26 * size if ch in SPACED else 0)
            if level == "lim":
                cx += 0.14 * size
        return paths, cx - x0

    _, width = layout(0)
    start = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]
    paths, _ = layout(start)
    return f'<path d="{" ".join(paths)}"/>'


def arrowhead(x, y, angle, size=12):
    a1, a2 = angle + math.radians(155), angle - math.radians(155)
    return (f'M {x + size * math.cos(a1):.1f} {y + size * math.sin(a1):.1f} L {x:.1f} {y:.1f} '
            f'L {x + size * math.cos(a2):.1f} {y + size * math.sin(a2):.1f}')


def hatch(x0, y0, x1, y1, spacing, angle_deg):
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = math.hypot(x1 - x0, y1 - y0)
    lines = []
    k = -r
    while k <= r:
        px, py = cx + nx * k, cy + ny * k
        lines.append(f"M {px - dx * r:.1f} {py - dy * r:.1f} L {px + dx * r:.1f} {py + dy * r:.1f}")
        k += spacing
    return " ".join(lines)


MANIFOLD = ("M 44 196 C 30 132, 118 74, 214 86 C 296 96, 338 52, 432 60 "
            "C 520 68, 584 118, 566 186 C 552 238, 474 250, 392 240 "
            "C 304 230, 254 262, 162 256 C 84 250, 52 230, 44 196 Z")
U_A = "M 168 170 C 166 136, 214 118, 262 124 C 306 130, 324 158, 316 184 C 306 214, 254 222, 214 214 C 180 207, 170 192, 168 170 Z"
U_B = "M 276 150 C 288 122, 346 112, 386 126 C 424 140, 430 180, 410 202 C 388 226, 330 228, 298 212 C 274 200, 268 172, 276 150 Z"
IMG_A = "M 92 384 C 88 352, 120 334, 162 336 C 204 338, 226 356, 224 384 C 222 414, 192 428, 154 426 C 116 424, 94 410, 92 384 Z"
IMG_A_CAP = "M 176 337 C 196 360, 196 404, 180 427 L 260 440 L 260 320 Z"
IMG_B = "M 390 386 C 384 354, 416 334, 458 336 C 500 338, 522 360, 518 390 C 514 418, 482 430, 446 428 C 410 426, 394 412, 390 386 Z"
IMG_B_CAP = "M 340 320 L 340 440 L 432 428 C 414 404, 410 360, 428 337 Z"

STROKE = f'fill="none" stroke="{BLUE}" stroke-linecap="round" stroke-linejoin="round"'


def build():
    p = []
    p.append(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 484" width="600" height="484">
<defs>
  <filter id="pencil" x="-4%" y="-4%" width="108%" height="108%" color-interpolation-filters="sRGB">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="wobble"/>
    <feDisplacementMap in="SourceGraphic" in2="wobble" scale="2.8" xChannelSelector="R" yChannelSelector="G" result="shaky"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="11" result="grain"/>
    <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.5 1.45" result="grainmask"/>
    <feComposite in="shaky" in2="grainmask" operator="in"/>
  </filter>
  <clipPath id="ua"><path d="{U_A}"/></clipPath>
  <clipPath id="ub"><path d="{U_B}"/></clipPath>
  <clipPath id="ia"><path d="{IMG_A}"/></clipPath>
  <clipPath id="ib"><path d="{IMG_B}"/></clipPath>
  <clipPath id="iacap"><path d="{IMG_A_CAP}"/></clipPath>
  <clipPath id="ibcap"><path d="{IMG_B_CAP}"/></clipPath>
</defs>
""")

    # light washes, kept outside the pencil filter
    p.append(f'<path d="{U_A}" fill="{BLUE}" opacity="0.035"/>')
    p.append(f'<path d="{U_B}" fill="{BLUE}" opacity="0.035"/>')
    p.append(f'<path d="{IMG_A}" fill="{BLUE}" opacity="0.035"/>')
    p.append(f'<path d="{IMG_B}" fill="{BLUE}" opacity="0.035"/>')
    p.append('<g filter="url(#pencil)">')

    # hatching of the overlaps
    p.append(f'<g clip-path="url(#ua)"><g clip-path="url(#ub)"><path d="{hatch(260, 110, 330, 230, 5, -55)}" {STROKE} stroke-width="1.2" opacity="0.7"/></g></g>')
    p.append(f'<g clip-path="url(#ia)"><g clip-path="url(#iacap)"><path d="{hatch(170, 330, 230, 430, 5, 90)}" {STROKE} stroke-width="1.2" opacity="0.65"/></g></g>')
    p.append(f'<g clip-path="url(#ib)"><g clip-path="url(#ibcap)"><path d="{hatch(380, 330, 440, 430, 5, 0)}" {STROKE} stroke-width="1.2" opacity="0.65"/></g></g>')

    # outlines, traced twice like a pencil sketch
    for d, w in [(MANIFOLD, 2.5), (U_A, 2.1), (U_B, 2.1), (IMG_A, 2.1), (IMG_B, 2.1)]:
        p.append(f'<path d="{d}" {STROKE} stroke-width="{w}" opacity="0.88"/>')
        p.append(f'<path d="{d}" {STROKE} stroke-width="1.1" opacity="0.38" transform="translate(1.2 -0.8) rotate(0.4 300 230)"/>')
    p.append(f'<path d="M 176 337 C 196 360, 196 404, 180 427" {STROKE} stroke-width="1.5" opacity="0.75"/>')
    p.append(f'<path d="M 428 337 C 410 360, 414 404, 432 428" {STROKE} stroke-width="1.5" opacity="0.75"/>')

    # coordinate frames
    for ox in (60, 352):
        p.append(f'<path d="M {ox} 446 L {ox + 196} 446 M {ox + 12} 456 L {ox + 12} 318" {STROKE} stroke-width="1.6" opacity="0.85"/>')
        p.append(f'<path d="{arrowhead(ox + 196, 446, 0, 7)} {arrowhead(ox + 12, 318, -math.pi / 2, 7)}" {STROKE} stroke-width="1.6" opacity="0.85"/>')

    # charts and transition maps
    arrows = [
        ("M 212 214 C 196 252, 176 284, 160 330", 160, 330),
        ("M 380 222 C 404 258, 438 292, 452 330", 452, 330),
        ("M 214 348 C 262 300, 344 300, 392 348", 392, 348),
        ("M 392 414 C 344 456, 262 456, 214 414", 214, 414),
    ]
    for d, ex, ey in arrows:
        p.append(f'<path d="{d}" {STROKE} stroke-width="1.7" stroke-dasharray="2.5 5" opacity="0.85"/>')
    p.append(f'<path d="{arrowhead(160, 330, math.atan2(330 - 284, 160 - 176))}" {STROKE} stroke-width="1.7"/>')
    p.append(f'<path d="{arrowhead(452, 330, math.atan2(330 - 292, 452 - 438))}" {STROKE} stroke-width="1.7"/>')
    p.append(f'<path d="{arrowhead(392, 348, math.atan2(348 - 300, 392 - 344))}" {STROKE} stroke-width="1.7"/>')
    p.append(f'<path d="{arrowhead(214, 414, math.atan2(414 - 456, 214 - 262))}" {STROKE} stroke-width="1.7"/>')

    # boundary leader
    p.append(f'<path d="M 556 214 C 566 230, 572 246, 574 262" {STROKE} stroke-width="1.4" opacity="0.75"/>')

    p.append("</g>")

    # point p (terracotta accent) and its images
    p.append(f'<g filter="url(#pencil)" fill="{TERRE}">'
             f'<circle cx="293" cy="168" r="5"/><circle cx="200" cy="392" r="4.4"/><circle cx="404" cy="372" r="4.4"/></g>')

    # labels
    labels = [
        formula(78, 152, 38, [("M", "cal", 0)]),
        formula(572, 288, 24, [("∂", "rm", 0), ("M", "cal", 0)], anchor="middle"),
        formula(184, 164, 26, [("U", "it", 0), ("α", "it", -1)]),
        formula(348, 164, 26, [("U", "it", 0), ("β", "it", -1)]),
        formula(300, 190, 21, [("p", "it", 0)]),
        formula(178, 272, 25, [("φ", "it", 0), ("α", "it", -1)], anchor="end"),
        formula(436, 272, 25, [("φ", "it", 0), ("β", "it", -1)]),
        formula(303, 294, 22, [("τ", "it", 0), ("αβ", "it", -1), ("=", "rm", 0), ("φ", "it", 0), ("β", "it", -1),
                               ("∘", "rm", 0), ("φ", "it", 0), ("subsup", "α", "−1")], anchor="middle"),
        formula(303, 476, 22, [("τ", "it", 0), ("βα", "it", -1)], anchor="middle"),
        formula(256, 476, 23, [("R", "bb", 0), ("n", "it", 1)], anchor="end"),
        formula(548, 476, 23, [("R", "bb", 0), ("n", "it", 1)], anchor="end"),
        formula(590, 40, 26, [("∫", "big", 0), ("M", "cal", "lim"), ("d", "rm", 0), ("ω", "it", 0), ("=", "rm", 0),
                              ("∫", "big", 0), ("∂", "rm", "lim"), ("M", "cal", "lim"), ("ω", "it", 0)], anchor="end"),
    ]
    p.append(f'<g filter="url(#pencil)" fill="{BLUE}" opacity="0.95" stroke="#F5F0E6" stroke-width="4" stroke-linejoin="round" paint-order="stroke">')
    p.extend(labels)
    p.append("</g>")
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    svg = build()
    OUT.write_text(svg, encoding="utf-8")
    print(OUT.relative_to(ROOT), len(svg.encode()) // 1024, "KB")
