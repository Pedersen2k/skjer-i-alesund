"""Lysparken i Spjelkavika: liten skog/park som slynger seg rundt Lillevatnet, med sti og liten bro.
park(d, dot, cx, cy, sc, t, t0): tegner med d (ImageDraw); dot(x, y, r, farge, styrke) legger glød. t=None: alt tent."""
import math, random

GOLD = (255, 207, 112)
PAL = [(255, 207, 112), (255, 140, 110), (140, 220, 255), (255, 170, 220)]


def park(d, dot, cx, cy, sc=1.0, t=None, t0=5.5):
    rx, ry = 270 * sc, 130 * sc
    def lit(i, step):
        return t is None or t > t0 + i * step
    def tw(i):
        return 1.0 if t is None else .78 + .22 * math.sin(t * 5 + i * 1.3)
    r = random.Random(4)
    trees = []
    for i in range(18):
        a = math.tau * (i + r.uniform(-.25, .25)) / 18
        k = r.uniform(1.30, 1.48)
        trees.append((cx + rx * k * math.cos(a) * 1.02, cy + ry * 1.5 * k / 1.4 * math.sin(a), r.uniform(92, 132) * sc, i))
    trees.sort(key=lambda p: p[1])
    def tree(x, y, h, i):
        w = h * .62
        for j in range(3):
            top = y - h + j * h * .26; bot = y - h * .5 + j * h * .27
            d.polygon([(x, top), (x - w * (.5 + j * .17), bot + h * .2), (x + w * (.5 + j * .17), bot + h * .2)], fill=(14, 46, 44))
        d.rectangle((x - 4, y - h * .06, x + 4, y + 4), fill=(40, 28, 30))
        for j in range(6):
            u = (j + 1) / 7
            ly = y - h * .9 + u * h * .72
            lx = x + ((j * 53 + i * 31) % 100 / 100 - .5) * w * (.35 + u * .9)
            if lit(i + j, .05):
                col = tuple(int(c * tw(i + j)) for c in PAL[(i + j) % 4])
                dot(lx, ly, 26 * sc, col, .8); d.ellipse((lx - 5 * sc, ly - 5 * sc, lx + 5 * sc, ly + 5 * sc), fill=col)
            else:
                d.ellipse((lx - 4 * sc, ly - 4 * sc, lx + 4 * sc, ly + 4 * sc), fill=(60, 80, 80))
    back = [p for p in trees if p[1] < cy]; front = [p for p in trees if p[1] >= cy]
    for p in back: tree(*p)
    # vannet (litt uregelmessig) med speiling av lysene
    pts = []
    for q in range(72):
        a = math.tau * q / 72
        s = 1 + .08 * math.sin(3 * a + 1) + .05 * math.sin(5 * a)
        pts.append((cx + rx * s * math.cos(a), cy + ry * s * math.sin(a)))
    d.polygon(pts, fill=(18, 30, 74), outline=(50, 70, 130))
    # sti som slynger seg rundt vannet
    for i in range(64):
        a = math.tau * i / 64
        s = 1.13 + .06 * math.sin(4 * a)
        x, y = cx + rx * s * math.cos(a), cy + ry * s * 1.1 * math.sin(a)
        if lit(i, .03):
            col = tuple(int(c * tw(i)) for c in ((255, 214, 140), (255, 190, 110))[i % 2])
            dot(x, y, 22 * sc, col, .6); d.ellipse((x - 4 * sc, y - 4 * sc, x + 4 * sc, y + 4 * sc), fill=col)
            if y > cy: d.line((x, y + 14 * sc, x, y + 14 * sc + 12 * sc), fill=tuple(int(c * .35) for c in col), width=3)  # speiling
    # den lille broa
    bx0, bx1, by = cx - 105 * sc, cx + 105 * sc, cy + 18 * sc
    arch = [(bx0 + (bx1 - bx0) * u / 20, by - 40 * sc * math.sin(math.pi * u / 20)) for u in range(21)]
    d.line(arch, fill=(120, 84, 64), width=int(12 * sc))
    d.line([(x, y + 8 * sc) for x, y in arch], fill=(70, 48, 44), width=int(5 * sc))
    for u in range(1, 20, 2):
        x, y = arch[u]
        if lit(u, .06):
            col = tuple(int(c * tw(u)) for c in GOLD); dot(x, y - 14 * sc, 24 * sc, col, .8)
            d.ellipse((x - 5 * sc, y - 19 * sc, x + 5 * sc, y - 9 * sc), fill=col)
    for p in front: tree(*p)
