"""Generate the blog illustrations and the default social image in the site's art direction.

Usage: python3 tools/illustrations.py  (requires google-chrome and ImageMagick `convert`)
"""

import math
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / "assets" / "images"

PAPER = "#F5F0E6"
PAPER_DEEP = "#ECE5D7"
INK = "#252B2A"
INK_SOFT = "#545C5A"
BLUE = "#2455D6"
TERRE = "#B85F3D"
BRUME = "#A9BBC5"


def frame(w, h, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <filter id="grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
    <feColorMatrix values="0 0 0 0 0.15  0 0 0 0 0.17  0 0 0 0 0.16  0 0 0 0.55 0"/>
  </filter>
  <pattern id="dots" width="40" height="40" patternUnits="userSpaceOnUse">
    <circle cx="20" cy="20" r="1.1" fill="{INK}" opacity="0.13"/>
  </pattern>
</defs>
<rect width="{w}" height="{h}" fill="{PAPER}"/>
<rect width="{w}" height="{h}" fill="url(#dots)"/>
{body}
<rect width="{w}" height="{h}" filter="url(#grain)" opacity="0.07"/>
</svg>"""


def mono(x, y, text, size=19, color=INK_SOFT, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="DejaVu Sans Mono, monospace" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}" letter-spacing="1" {extra}>{text}</text>')


def hand(x, y, text, size=44, rotate=-6, color=BLUE):
    return (f'<text x="{x}" y="{y}" font-family="Caveat" font-size="{size}" fill="{color}" '
            f'transform="rotate({rotate} {x} {y})">{text}</text>')


def poly(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def two_simulations():
    x0, x1, base, amp = 150, 1050, 620, 400

    def sx(t):
        return x0 + (x1 - x0) * t

    def u(t):
        return 4 * t * (1 - t)

    exact = [(sx(i / 200), base - amp * u(i / 200)) for i in range(201)]
    m1 = [i / 5 for i in range(6)]
    m2 = [0.1 + i / 5 for i in range(5)]
    p1 = [(sx(t), base - amp * u(t) * (0.9 if 0 < t < 1 else 1)) for t in m1]
    p2 = [(sx(t), base - amp * u(t) * 1.07) for t in m2]
    b = []
    b.append(f'<line x1="110" y1="{base}" x2="1110" y2="{base}" stroke="{INK}" stroke-width="1.4"/>')
    b.append(f'<polyline points="{poly(exact)}" fill="none" stroke="{INK}" stroke-width="1.3" stroke-dasharray="3 7" opacity="0.6"/>')
    b.append(f'<polyline points="{poly(p1)}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    b.append(f'<polyline points="{poly(p2)}" fill="none" stroke="{TERRE}" stroke-width="1.6" stroke-dasharray="8 7"/>')
    for (x, y), t in zip(p1, m1):
        b.append(f'<line x1="{x}" y1="{base - 14}" x2="{x}" y2="{base}" stroke="{BLUE}" stroke-width="2"/>')
        b.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{base}" stroke="{BLUE}" stroke-width="1" stroke-dasharray="2 6" opacity="0.5"/>')
        b.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{BLUE}"/>')
    for (x, y), t in zip(p2, m2):
        b.append(f'<line x1="{x}" y1="{base}" x2="{x}" y2="{base + 14}" stroke="{TERRE}" stroke-width="2"/>')
        b.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{PAPER}" stroke="{TERRE}" stroke-width="2"/>')
    b.append(mono(1060, base - 18, "x"))
    b.append(mono(sx(0.66) + 22, base - amp * u(0.66) - 14, "u(x)", color=INK))
    b.append(f'<line x1="150" y1="700" x2="190" y2="700" stroke="{BLUE}" stroke-width="2"/>')
    b.append(mono(205, 707, "M₁  · h"))
    b.append(f'<line x1="380" y1="700" x2="420" y2="700" stroke="{TERRE}" stroke-width="2" stroke-dasharray="8 6"/>')
    b.append(mono(435, 707, "M₂  · h"))
    b.append(mono(1050, 707, "‖u − u_h‖ = O(h)", anchor="end"))
    b.append(hand(800, 150, "M₁ ∪ M₂ → ?", rotate=-5))
    b.append(f'<path d="M 812 168 q 60 -8 120 -16" stroke="{BLUE}" stroke-width="1.6" fill="none"/>')
    b.append(mono(150, 90, "01 — TOPOLOGIE / TOPOLOGY", size=17))
    return frame(1200, 800, "\n".join(b))


def measuring_time():
    b = []
    px, py, length = 300, 170, 400
    b.append(f'<line x1="200" y1="{py}" x2="400" y2="{py}" stroke="{INK}" stroke-width="1.6"/>')
    for i in range(9):
        x = 210 + i * 22
        b.append(f'<line x1="{x}" y1="{py}" x2="{x + 14}" y2="{py - 16}" stroke="{INK}" stroke-width="1.1"/>')
    span = math.radians(26)
    arc_pts = [(px + length * math.sin(a), py + length * math.cos(a))
               for a in [-span + 2 * span * i / 80 for i in range(81)]]
    b.append(f'<polyline points="{poly(arc_pts)}" fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="3 8" opacity="0.6"/>')
    for a, op in [(-span, 0.25), (-span / 2, 0.4), (span, 0.25)]:
        bx, by = px + length * math.sin(a), py + length * math.cos(a)
        b.append(f'<line x1="{px}" y1="{py}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{BLUE}" stroke-width="1.2" opacity="{op}"/>')
        b.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="22" fill="none" stroke="{BLUE}" stroke-width="1.2" opacity="{op}"/>')
    a = span * 0.55
    bx, by = px + length * math.sin(a), py + length * math.cos(a)
    b.append(f'<line x1="{px}" y1="{py}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{BLUE}" stroke-width="2"/>')
    b.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="24" fill="{BLUE}"/>')
    b.append(f'<circle cx="{px}" cy="{py}" r="5" fill="{INK}"/>')
    b.append(f'<path d="M {px} {py + 120} A 120 120 0 0 0 {px + 120 * math.sin(a):.1f} {py + 120 * math.cos(a):.1f}" fill="none" stroke="{INK}" stroke-width="1.1"/>')
    b.append(mono(px + 28, py + 150, "θ"))
    x0, x1, mid, amp = 580, 1110, 400, 150
    wave = [(x0 + (x1 - x0) * i / 400, mid - amp * math.cos(2 * math.pi * 3.5 * i / 400)) for i in range(401)]
    b.append(f'<line x1="{x0 - 10}" y1="{mid}" x2="{x1 + 20}" y2="{mid}" stroke="{INK}" stroke-width="1" stroke-dasharray="4 7" opacity="0.6"/>')
    b.append(f'<polyline points="{poly(wave)}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    period = (x1 - x0) / 3.5
    for k in range(4):
        x = x0 + k * period
        b.append(f'<circle cx="{x:.1f}" cy="{mid - amp}" r="6" fill="{BLUE}"/>')
        for j in range(k + 1):
            tx = x - 3 * k + j * 7
            b.append(f'<line x1="{tx:.1f}" y1="{mid + amp + 40}" x2="{tx:.1f}" y2="{mid + amp + 68}" stroke="{INK}" stroke-width="1.6"/>')
        b.append(mono(x, mid + amp + 100, str(k + 1), anchor="middle"))
    b.append(f'<circle cx="{x0 + 2 * period:.1f}" cy="{mid - amp}" r="16" fill="none" stroke="{TERRE}" stroke-width="2"/>')
    b.append(mono(x1 + 20, mid - 12, "t", anchor="end"))
    b.append(mono(x0, 120, "θ(t) ~ cos(ωt)", color=INK))
    b.append(hand(860, 150, "t = ?", rotate=-6))
    b.append(mono(80, 740, "02 — COMPTER / COUNT", size=17))
    return frame(1200, 800, "\n".join(b))


def nothing_to_hide():
    b = []
    coast = "M 760 800 C 820 700, 900 640, 980 600 S 1120 520, 1200 470 L 1200 800 Z"
    b.append(f'<path d="{coast}" fill="{BRUME}" opacity="0.35"/>')
    b.append(f'<path d="M 760 800 C 820 700, 900 640, 980 600 S 1120 520, 1200 470" fill="none" stroke="{INK}" stroke-width="1.2" opacity="0.5"/>')
    for i in range(-6, 16):
        x = i * 90
        b.append(f'<line x1="{x}" y1="0" x2="{x + 420}" y2="800" stroke="{INK}" stroke-width="1" opacity="0.10"/>')
    for i in range(-2, 14):
        y = i * 80
        b.append(f'<line x1="0" y1="{y + 300}" x2="1200" y2="{y - 200}" stroke="{INK}" stroke-width="1" opacity="0.10"/>')
    b.append(f'<line x1="0" y1="560" x2="1200" y2="60" stroke="{INK}" stroke-width="2.4" opacity="0.18"/>')
    pts = [(230, 560, "01", "08:12"), (520, 300, "02", "09:03"), (850, 390, "03", "18:40"), (640, 620, "04", "SAT 10:30")]
    path = f"M {pts[0][0]} {pts[0][1]} C 300 420, 420 330, {pts[1][0]} {pts[1][1]} S 760 330, {pts[2][0]} {pts[2][1]} S 760 620, {pts[3][0]} {pts[3][1]} S 300 640, {pts[0][0]} {pts[0][1]}"
    b.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-dasharray="2 9" stroke-linecap="round"/>')
    for x, y, n, t in pts:
        b.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{BLUE}"/>')
        b.append(f'<circle cx="{x}" cy="{y}" r="22" fill="none" stroke="{BLUE}" stroke-width="1" opacity="0.5"/>')
        b.append(mono(x + 50, y - 10, n, color=INK))
        b.append(mono(x + 50, y + 16, t))
    b.append(f'<path d="M 500 266 C 474 276, 478 326, 512 334 C 548 342, 562 300, 548 280 C 536 262, 512 258, 494 272" fill="none" stroke="{TERRE}" stroke-width="2.4" stroke-linecap="round"/>')
    b.append(hand(860, 170, "4 → 95 %", rotate=-6))
    b.append(f'<path d="M 872 188 q 70 -10 140 -20" stroke="{BLUE}" stroke-width="1.6" fill="none"/>')
    b.append(mono(80, 90, "03 — MÉTADONNÉES / METADATA", size=17))
    return frame(1200, 800, "\n".join(b))


def og_default():
    b = []
    b.append(f'<text x="90" y="300" font-family="Newsreader" font-size="92" fill="{INK}" letter-spacing="-2">Valentin Ritzenthaler</text>')
    b.append(f'<text x="94" y="372" font-family="&apos;Source Sans 3&apos;" font-size="34" fill="{INK_SOFT}">Applied mathematics · AI · Writing</text>')
    b.append(f'<line x1="94" y1="440" x2="174" y2="440" stroke="{INK}" stroke-width="1.5"/>')
    b.append(mono(194, 447, "BARCELONA", size=20))
    b.append(f'<path d="M 760 560 C 790 470, 860 420, 960 400 S 1060 360, 1110 300" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')
    b.append(f'<path d="M 640 560 C 800 540, 930 470, 1010 380 S 1100 240, 1130 200" fill="none" stroke="{BLUE}" stroke-width="1.4" stroke-dasharray="3 9" opacity="0.6"/>')
    b.append(f'<line x1="600" y1="560" x2="1150" y2="560" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 8" opacity="0.5"/>')
    for x, y, r in [(760, 560, 8), (960, 400, 8)]:
        b.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{BLUE}"/>')
    b.append(f'<circle cx="1110" cy="300" r="10" fill="{PAPER}" stroke="{BLUE}" stroke-width="2.4"/>')
    b.append(f'<circle cx="94" cy="160" r="8" fill="{TERRE}"/>')
    return frame(1200, 630, "\n".join(b))


def render(svg, w, h, target):
    fonts = "\n".join(
        f'@font-face {{ font-family: "{fam}"; src: url("{(FONTS / f).as_uri()}") format("woff2"); font-weight: 200 900; }}'
        for fam, f in [("Newsreader", "newsreader-latin-wght-normal.woff2"),
                       ("Source Sans 3", "source-sans-3-latin-wght-normal.woff2"),
                       ("Caveat", "caveat-latin-wght-normal.woff2")])
    html = f"<!doctype html><html><head><style>{fonts} html,body{{margin:0;background:{PAPER}}} svg{{display:block}}</style></head><body>{svg}</body></html>"
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        png = Path(tmp) / "shot.png"
        page.write_text(html, encoding="utf-8")
        subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", f"--window-size={w},{h}",
                        "--virtual-time-budget=3000", f"--screenshot={png}", page.as_uri()],
                       check=True, capture_output=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix == ".webp":
            subprocess.run(["convert", str(png), "-quality", "84", "-define", "webp:method=6", str(target)], check=True)
        else:
            subprocess.run(["convert", str(png), "-strip", "-quality", "86", str(target)], check=True)
    print(target.relative_to(ROOT), target.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    render(two_simulations(), 1200, 800, OUT / "blog" / "two-simulations.webp")
    render(measuring_time(), 1200, 800, OUT / "blog" / "measuring-time.webp")
    render(nothing_to_hide(), 1200, 800, OUT / "blog" / "nothing-to-hide.webp")
    render(og_default(), 1200, 630, OUT / "og-default.jpg")
