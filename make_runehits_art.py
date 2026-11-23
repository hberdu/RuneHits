"""Draws RuneHits' hitsplats and builds its digit font: original pixel art in the Old School RuneScape style, no game
files. A splat is a blood splash about 24x23: a bright core, darker toward the edge, ragged rays and a few drops
around, no outline. Red: a hit; blue: a miss (0); red with gold-tipped rays: a crit (OSRS' "max hit" look). The
shape is generated (seeded noise), not traced. Digits: 1-pixel strokes, about 6x9, white with a black shadow (the
shadow is the font string's), measured on an in-game max hit the user sent.
Writes art/*.tga and RuneHitsDigits.ttf. Needs: py -m pip install pillow fonttools.
Run: py make_runehits_art.py"""
import math
import random
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

ADDON = Path(__file__).parent
G, UP = 32, 4      # the cell in art pixels; saved 4x with hard edges (128x128)
C = 15.5           # the splat's middle (a 24-pixel splat on pixels 4..27)


def splash(seed, body_r=8.4, rays_n=26, ray_len=(2.0, 5.0), square=2.0):
    """the splash: {(x, y): depth}, depth 0 at the middle to 1 at the ragged edge; it fills most of its 24x23 box"""
    rnd = random.Random(seed)
    rays = [(i * 2 * math.pi / rays_n + rnd.uniform(-0.1, 0.1), rnd.uniform(*ray_len), rnd.uniform(0.06, 0.14))
            for i in range(rays_n)]                     # angle, extra length, half width (radians)
    wob = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]

    def reach(t):
        body = body_r + 0.6 * math.sin(3 * t + wob[0]) + 0.4 * math.sin(5 * t + wob[1]) + 0.3 * math.sin(7 * t + wob[2])
        ray = 0
        for a, length, w in rays:
            d = abs((t - a + math.pi) % (2 * math.pi) - math.pi)
            if d < w:
                ray = max(ray, length * (1 - d / w) ** 1.4)
        return body + ray

    out = {}
    for x in range(G):
        for y in range(G):
            dx, dy = x - C, (y - C) * 1.04              # a touch wider than tall: 24x23
            r, t = (abs(dx) ** square + abs(dy) ** square) ** (1 / square), math.atan2(dy, dx)  # square > 2: boxier
            rr = reach(t)
            if r <= rr and abs(dx) <= 12 and abs(y - C) <= 11.5:
                out[(x, y)] = r / rr
    for _ in range(10):                                 # drops flung past the rays (-1: a drop)
        a = rnd.uniform(0, 2 * math.pi)
        rr = reach(a) + rnd.uniform(1.0, 2.0)
        p = (round(C + rr * math.cos(a)), round(C + rr * math.sin(a) / 1.04))
        if p not in out and 4 <= p[0] <= 27 and 4 <= p[1] <= 27:
            out[p] = -1
    return out


def paint(shape, bands, drop, seed, name):
    """bands: (depth up to which, colors) from the core out: a flat core, a ring, then the rays darkening to the
    tips, each band's colors mixed at random, the borders a little ragged; drops in their own colors"""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (G, G), (0, 0, 0, 0))
    for (x, y), d in shape.items():
        if d < 0:
            c = rnd.choice(drop)
        else:
            d += rnd.uniform(-0.06, 0.06)
            c = rnd.choice(next((cs for top, cs in bands if d <= top), bands[-1][1]))
        im.putpixel((x, y), c + (255,))
    im.resize((G * UP, G * UP), Image.NEAREST).save(ADDON / "art" / f"{name}.tga")


# OSRS' look, by eye at 12x next to mine: few shades, a big flat core
RED = [(0.55, [(204, 0, 0)]), (0.66, [(168, 0, 0)]), (0.82, [(128, 0, 0), (118, 0, 0)]),
       (9, [(96, 0, 0), (76, 0, 0)])]
RED_DROPS = [(96, 0, 0)] * 5 + [(230, 0, 0)]
BLUE = [(0.55, [(68, 68, 255)]), (0.66, [(34, 34, 214)]), (0.82, [(12, 12, 166), (6, 6, 150)]),
        (9, [(0, 0, 112), (0, 0, 84)])]
BLUE_DROPS = [(0, 0, 112)] * 5 + [(68, 68, 255)]
MAX = [(0.58, [(238, 6, 0)]), (0.7, [(196, 0, 0), (176, 0, 0)]), (0.84, [(150, 0, 0), (196, 0, 0), (255, 136, 0)]),
       (9, [(255, 204, 0), (255, 170, 0), (255, 136, 0)])]
MAX_DROPS = [(255, 204, 0), (255, 136, 0), (210, 0, 0)]

# 1-pixel strokes; "1" is narrow (a proportional font, as OSRS' is)
DIGITS = {
    "0": [".####.", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", "#....#", ".####."],
    "1": [".#.", "##.", ".#.", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "2": [".####.", "#....#", ".....#", "....#.", "...#..", "..#...", ".#....", "#.....", "######"],
    "3": [".####.", "#....#", ".....#", ".....#", "..###.", ".....#", ".....#", "#....#", ".####."],
    "4": ["....#.", "...##.", "..#.#.", ".#..#.", "#...#.", "######", "....#.", "....#.", "....#."],
    "5": ["######", "#.....", "#.....", "#####.", ".....#", ".....#", ".....#", "#....#", ".####."],
    "6": [".####.", "#.....", "#.....", "#####.", "#....#", "#....#", "#....#", "#....#", ".####."],
    "7": ["######", ".....#", "....#.", "....#.", "...#..", "..#...", "..#...", ".#....", ".#...."],
    "8": [".####.", "#....#", "#....#", "#....#", ".####.", "#....#", "#....#", "#....#", ".####."],
    "9": [".####.", "#....#", "#....#", "#....#", ".#####", ".....#", ".....#", "#....#", ".####."],
}
U = 100  # font units per pixel (1000 per em: a pixel is a tenth of the font size)


def font():
    order = [".notdef", "space"] + ["d" + d for d in DIGITS]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(d): "d" + d for d in DIGITS}})
    glyphs, metrics = {}, {}
    for name in order:
        pen = TTGlyphPen(None)
        rows = DIGITS.get(name[1:]) if name.startswith("d") else None
        width = len(rows[0]) if rows else 4
        for r, row in enumerate(rows or []):
            x = 0
            while x < len(row):
                if row[x] != "#":
                    x += 1
                    continue
                e = x
                while e < len(row) and row[e] == "#":
                    e += 1
                y0, y1 = (8 - r) * U, (9 - r) * U       # clockwise: an outer contour
                pen.moveTo((x * U, y0)); pen.lineTo((x * U, y1)); pen.lineTo((e * U, y1)); pen.lineTo((e * U, y0))
                pen.closePath()
                x = e
        glyphs[name] = pen.glyph()
        xmin = min(row.index("#") for row in rows) * U if rows else 0
        metrics[name] = ((width + 1) * U, xmin)         # a pixel of space after each digit
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900, descent=0)
    fb.setupNameTable({"familyName": "RuneHits Digits", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=900, sTypoDescender=0, sTypoLineGap=0, usWinAscent=900, usWinDescent=0)
    fb.setupPost()
    fb.save(ADDON / "RuneHitsDigits.ttf")


if __name__ == "__main__":
    (ADDON / "art").mkdir(parents=True, exist_ok=True)
    for old in (ADDON / "art").glob("*_*.tga"):         # the earlier two-layer art
        old.unlink()
    paint(splash(7), RED, RED_DROPS, 1, "red")
    paint(splash(11), BLUE, BLUE_DROPS, 2, "blue")
    paint(splash(5, body_r=9.4, rays_n=30, ray_len=(0.8, 2.6), square=3.2), MAX, MAX_DROPS, 3, "max")  # squarer, rimmed in gold
    font()
    print("ok")
