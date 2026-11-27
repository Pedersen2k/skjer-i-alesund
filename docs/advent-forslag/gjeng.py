"""Forslag: Flimmer-gjengen. Seks lysfigurer i samme stil som Flimmer (kropp, store øyne, rosa kinn).
Kjør: python3 gjeng.py   (lager gjeng.png, 1600 × 1600)"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from ukepost import B, F, M
import lag

W, H = 1600, 1000
CREAM = (245, 236, 214); GOLD = (255, 207, 112)
EYE = (30, 20, 50); MOUTH = (60, 30, 60); CHEEK = (255, 170, 170)


STATE = 0        # 0 normal, 1 blunk, 2 snakker (åpen munn)
NOFLAME = False  # reelen tegner flammen selv


def face(d, cx, ey, gap=28, r=22, smile=True, cheeks=True, look=0):
    for s in (-gap, gap):
        if STATE == 1:
            d.line((cx + s - r + 4, ey, cx + s + r - 4, ey), fill=MOUTH, width=6)
            continue
        d.ellipse((cx + s - r, ey - r - 2, cx + s + r, ey + r + 2), fill=(255, 255, 255))
        d.ellipse((cx + s + look - r // 2, ey - r // 2 - 1, cx + s + look + r // 2, ey + r // 2 + 3), fill=EYE)
        d.ellipse((cx + s + look - 2, ey - 9, cx + s + look + 4, ey - 3), fill=(255, 255, 255))
    if smile and STATE == 2:
        d.ellipse((cx - 17, ey + 26, cx + 17, ey + 62), fill=MOUTH)
        d.ellipse((cx - 10, ey + 46, cx + 10, ey + 62), fill=(220, 100, 110))
    elif smile:
        d.arc((cx - 24, ey + 22, cx + 24, ey + 66), 15, 165, fill=MOUTH, width=6)
    if cheeks:
        for s in (-gap - 26, gap + 26):
            d.ellipse((cx + s - 13, ey + 28, cx + s + 13, ey + 46), fill=CHEEK)


def glow(g, x, y, r, col, k=.8):
    for f, kk in ((1.0, .3), (.62, .6), (.3, 1.0)):
        c = tuple(int(v * k * kk) for v in col)
        g.ellipse((x - r * f, y - r * f, x + r * f, y + r * f), fill=c)


def flame(d, x, y, s):
    d.ellipse((x - 15 * s, y - 32 * s, x + 15 * s, y), fill=(255, 150, 40))
    d.polygon([(x - 14 * s, y - 20 * s), (x + 14 * s, y - 20 * s), (x, y - 62 * s)], fill=(255, 150, 40))
    d.ellipse((x - 8 * s, y - 24 * s, x + 8 * s, y - 2 * s), fill=(255, 232, 150))
    d.polygon([(x - 7 * s, y - 14 * s), (x + 7 * s, y - 14 * s), (x, y - 40 * s)], fill=(255, 232, 150))


def flimmer(d, g, cx, by):
    d.rounded_rectangle((cx - 75, by - 250, cx + 75, by), 30, fill=CREAM)
    d.rounded_rectangle((cx + 38, by - 240, cx + 75, by - 6), 30, fill=(224, 212, 186))
    d.ellipse((cx - 77, by - 266, cx + 77, by - 234), fill=(255, 250, 238))
    d.line((cx, by - 262, cx, by - 288), fill=(50, 40, 40), width=6)
    if not NOFLAME: flame(d, cx, by - 288, 1.5)
    glow(g, cx, by - 330, 120, (180, 110, 30))
    face(d, cx, by - 170, look=7)


def lykt(d, g, cx, by):
    """Lykta: gammel gatelykt som holder øye med byen. Rolig og litt streng."""
    d.rectangle((cx - 9, by - 200, cx + 9, by), fill=(36, 34, 56))
    d.rectangle((cx - 34, by - 14, cx + 34, by), fill=(36, 34, 56))
    d.rounded_rectangle((cx - 62, by - 330, cx + 62, by - 190), 18, fill=(255, 214, 130), outline=(36, 34, 56), width=8)
    d.polygon([(cx - 80, by - 328), (cx + 80, by - 328), (cx, by - 392)], fill=(36, 34, 56))
    d.ellipse((cx - 8, by - 410, cx + 8, by - 394), fill=(36, 34, 56))
    glow(g, cx, by - 260, 170, (200, 140, 40))
    face(d, cx, by - 270, gap=26, r=19, look=-5)
    d.line((cx - 50, by - 305, cx - 14, by - 298), fill=(90, 60, 40), width=5)   # strengt øyebryn
    d.line((cx + 50, by - 305, cx + 14, by - 298), fill=(90, 60, 40), width=5)


def gnist(d, g, cx, by):
    """Gnist: nyttårsrakett i miniatyr. Altfor ivrig. Holder fyrverkeri og alt som smeller."""
    d.polygon([(cx - 52, by - 70), (cx - 90, by), (cx - 40, by - 24)], fill=(214, 60, 80))
    d.polygon([(cx + 52, by - 70), (cx + 90, by), (cx + 40, by - 24)], fill=(214, 60, 80))
    d.rounded_rectangle((cx - 54, by - 250, cx + 54, by), 26, fill=(236, 70, 90))
    d.rectangle((cx - 54, by - 130, cx + 54, by - 100), fill=GOLD)
    d.polygon([(cx - 54, by - 240), (cx + 54, by - 240), (cx, by - 340)], fill=(250, 240, 220))
    for i, a in enumerate(range(0, 360, 45)):
        x = cx + 74 * math.cos(math.radians(a)); y = by - 410 + 74 * math.sin(math.radians(a))
        d.line((cx, by - 410, x, y), fill=(255, 226, 140), width=5)
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=[GOLD, (255, 140, 110), (140, 220, 255), (255, 170, 220)][i % 4])
    d.ellipse((cx - 10, by - 420, cx + 10, by - 400), fill=(255, 250, 238))
    glow(g, cx, by - 410, 130, (170, 110, 40))
    face(d, cx, by - 190, gap=22, r=20)
    d.ellipse((cx - 16, by - 152, cx + 16, by - 120), fill=MOUTH)          # «åååå!»


def stjerne(d, g, cx, by):
    """Stjerna: julestjerna fra toppen av treet. Drømmende, vet alt om det som skjer i kirkene."""
    pts = []
    for i in range(10):
        r = 150 if i % 2 == 0 else 68
        a = math.radians(-90 + i * 36)
        pts.append((cx + r * math.cos(a), by - 190 + r * math.sin(a)))
    d.polygon(pts, fill=(255, 214, 110))
    inner = [(cx + (p[0] - cx) * .7, by - 190 + (p[1] - (by - 190)) * .7) for p in pts]
    d.polygon(inner, fill=(255, 232, 160))
    glow(g, cx, by - 190, 190, (200, 150, 40))
    face(d, cx, by - 180, gap=24, r=19, look=0)
    d.arc((cx - 40, by - 190, cx - 14, by - 176), 200, 340, fill=MOUTH, width=4)   # lukkede, drømmende
    d.arc((cx + 14, by - 190, cx + 40, by - 176), 200, 340, fill=MOUTH, width=4)


def pepper(d, g, cx, by):
    """Pepperkake-Per: kjeks som elsker gratis. Passer på «Under hundrelappen»."""
    brown = (176, 106, 58); dark = (132, 76, 40)
    d.ellipse((cx - 70, by - 380, cx + 70, by - 250), fill=brown)                    # hode
    d.rounded_rectangle((cx - 100, by - 270, cx + 100, by - 110), 40, fill=brown)    # kropp
    for s in (-1, 1):
        d.rounded_rectangle((cx + s * 130 - 30, by - 262, cx + s * 130 + 30, by - 150), 28, fill=brown)
        d.rounded_rectangle((cx + s * 56 - 32, by - 150, cx + s * 56 + 32, by), 28, fill=brown)
    for y in (-215, -170):                                                           # knapper
        d.ellipse((cx - 10, by + y - 10, cx + 10, by + y + 10), fill=(255, 250, 238))
    d.arc((cx - 66, by - 250, cx + 66, by - 218), 20, 160, fill=(255, 250, 238), width=7)  # glasurkrage
    for s in (-1, 1):
        d.arc((cx + s * 130 - 24, by - 190, cx + s * 130 + 24, by - 150), 200, 340, fill=(255, 250, 238), width=7)
    face(d, cx, by - 320, gap=24, r=17)
    d.text((cx, by - 60), "0 kr", font=B(40), fill=(255, 250, 238), anchor="mm")
    d.arc((cx - 76, by - 388, cx + 76, by - 244), 205, 335, fill=dark, width=3)


def pare(d, g, cx, by):
    """Lysa: pæra fra lyslenka. Liten, glad og pratsom. Sier fra om det som er nytt."""
    d.rounded_rectangle((cx - 28, by - 150, cx + 28, by - 100), 10, fill=(60, 56, 74))
    for y in (-136, -124, -112): d.line((cx - 28, by + y, cx + 28, by + y), fill=(40, 36, 56), width=4)
    d.ellipse((cx - 85, by - 330, cx + 85, by - 140), fill=(255, 170, 220))
    d.ellipse((cx - 60, by - 310, cx - 28, by - 262), fill=(255, 215, 240))          # blank
    d.line((cx, by - 100, cx, by - 20), fill=(30, 26, 40), width=5)                   # ledning
    d.line((cx, by - 20, cx + 60, by), fill=(30, 26, 40), width=5)
    glow(g, cx, by - 235, 170, (190, 80, 140))
    face(d, cx, by - 235, gap=24, r=19, look=6)
    d.ellipse((cx - 14, by - 202, cx + 14, by - 172), fill=MOUTH)
    d.ellipse((cx - 9, by - 190, cx + 9, by - 174), fill=(220, 100, 110))
    if not NOFLAME: d.text((cx + 84, by - 345), "NYTT!", font=B(28), fill=GOLD, anchor="mm")


def fnugg(d, g, cx, by):
    """Snøfrid: snøfnugg. Kjølig, rolig, kommer med vinteren. Brukes når det snør i programmet."""
    cy = by - 190
    for a in range(0, 180, 60):
        x = 150 * math.cos(math.radians(a)); y = 150 * math.sin(math.radians(a))
        d.line((cx - x, cy - y, cx + x, cy + y), fill=(200, 232, 255), width=16)
    for a in range(0, 360, 60):
        for k in (.55, .8):
            x = cx + 150 * k * math.cos(math.radians(a)); y = cy + 150 * k * math.sin(math.radians(a))
            for s in (-35, 35):
                x2 = x + 38 * math.cos(math.radians(a + s)); y2 = y + 38 * math.sin(math.radians(a + s))
                d.line((x, y, x2, y2), fill=(200, 232, 255), width=9)
    d.ellipse((cx - 62, cy - 62, cx + 62, cy + 62), fill=(225, 244, 255))
    glow(g, cx, cy, 190, (60, 100, 150), .7)
    face(d, cx, cy - 6, gap=22, r=16)


GJENG = [
    (flimmer, "Flimmer", "Stearinlyset", "Sier fra om det som skjer. Gjør alt ved hovedkaren."),
    (lykt, "Lykta", "Gatelykta", "Vokter byen om kvelden. Bruker «I kveld»."),
    (gnist, "Gnist", "Raketten", "Fyrverkeri, nyttår og alt som smeller. Altfor ivrig."),
    (stjerne, "Stjerna", "Julestjerna", "Kirker, konserter og det stille. Litt drømmende."),
    (pepper, "Per", "Pepperkaka", "Gratis og billig. Hovedperson i «Under hundrelappen»."),
    (pare, "Lysa", "Pæra", "Nytt i programmet. Kan ikke holde noe for seg selv."),
]


def figur(fn, boks=(470, 540)):
    """Tegner én figur på eget lag, med tykk mørk kontur, beskjæres og skaleres til boksen."""
    LW, LH = 700, 760
    lag_ = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    gl = Image.new("RGB", (LW, LH), (0, 0, 0))
    fn(ImageDraw.Draw(lag_), ImageDraw.Draw(gl), LW // 2, 640)
    kontur = lag_.split()[3].filter(ImageFilter.MaxFilter(25))
    ut = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    ut.paste(Image.new("RGBA", (LW, LH), (14, 12, 34, 255)), mask=kontur)
    ut.alpha_composite(lag_)
    bb = ut.getbbox()
    k = min(boks[0] / (bb[2] - bb[0]), boks[1] / (bb[3] - bb[1]))
    sz = (int(LW * k), int(LH * k))
    ut = ut.resize(sz, Image.LANCZOS)
    g = gl.filter(ImageFilter.GaussianBlur(26)).resize(sz)
    return ut, g, sz, (int(bb[0] * k), int(bb[1] * k), int(bb[2] * k), int(bb[3] * k))


def main(ut="gjeng.png"):
    W, H = 1600, 2000
    im = lag.sky(W, H)
    glow_layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 90), "FLIMMER-GJENGEN", font=B(84), fill=GOLD, anchor="mm")
    d.text((W // 2, 170), "Seks små lys som viser deg Ålesund i advent", font=F(34), fill=(235, 228, 245), anchor="mm")
    cw = W // 3
    pos = []
    for i, (fn, navn, rolle, tekst) in enumerate(GJENG):
        col, row = i % 3, i // 3
        fig, g, sz, bb = figur(fn)
        yb = 790 + row * 760                       # underkant av figuren
        x0 = cw * col + cw // 2 - (bb[0] + bb[2]) // 2
        y0 = yb - bb[3]
        box = (x0, y0, x0 + sz[0], y0 + sz[1])
        glow_layer = ImageChops.screen(glow_layer, Image.new("RGB", (W, H), (0, 0, 0)).copy()) if False else glow_layer
        tmp = Image.new("RGB", (W, H), (0, 0, 0)); tmp.paste(g.convert("RGB"), (x0, y0))
        glow_layer = ImageChops.screen(glow_layer, tmp)
        im.paste(fig, (x0, y0), fig)
        pos.append((col, row, yb))
    im = ImageChops.screen(im, glow_layer)
    d = ImageDraw.Draw(im)
    for (fn, navn, rolle, tekst), (col, row, yb) in zip(GJENG, pos):
        cx = cw * col + cw // 2
        d.text((cx, yb + 40), navn, font=B(72), fill=(255, 255, 255), anchor="mm")
        d.text((cx, yb + 98), rolle.upper(), font=M(28), fill=GOLD, anchor="mm")
        lines, cur = [], ""
        for w_ in tekst.split():
            t = (cur + " " + w_).strip()
            if d.textlength(t, font=F(27)) > cw - 70 and cur: lines.append(cur); cur = w_
            else: cur = t
        lines.append(cur)
        for j, l in enumerate(lines):
            d.text((cx, yb + 140 + j * 34), l, font=F(27), fill=(215, 208, 235), anchor="mm")
    im.save(ut)
    print("lagret", ut)


if __name__ == "__main__":
    main(*sys.argv[1:2])
