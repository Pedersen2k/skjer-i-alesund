"""Reel «Flimmer og lyset»: 17 sekunder, 1080×1920, 24 bilder/s. Lyslenke, levende lys-maskot, Lysparken,
symfoniorkesteret og adventskransen på kaskjerda.no. Lyd legges på i Instagram.
Kjør: python3 reel.py            (lager advent-reel.mp4)
      python3 reel.py --stills   (lager reel-stills.png med noen nøkkelbilder)"""
import math, random, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
from ukepost import B, F, M, block, logo
import lag
import park as P

W, H, FPS, DUR = 1080, 1920, 24, 17.0
GOLD = (255, 207, 112)
CREAM = (245, 236, 214)
DARK = (14, 12, 34)
BOUNDS = [0, 2.6, 5.2, 8.7, 12.2, 14.6, 17.0]
IGNITE, IGNITE2 = 3.1, 16.0
BG = lag.sky(W, H)
BGD = ImageEnhance.Brightness(BG).enhance(.42)
PAL = [(255, 120, 90), GOLD, (140, 220, 255), (255, 170, 220)]
rr = random.Random(11)
SNOW = [(rr.random() * W, rr.random() * H, rr.uniform(40, 110), rr.uniform(2, 5), rr.random() * 6) for _ in range(90)]
rl = random.Random(5)
LEAVES = [(rl.random() * math.tau, rl.randrange(-26, 26), rl.choice(((24, 96, 56), (30, 120, 70), (18, 76, 46)))) for _ in range(200)]


def clamp(x): return max(0.0, min(1.0, x))
def back(x):
    x = clamp(x); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def scene_of(t):
    for i in range(6):
        if t < BOUNDS[i + 1]: return i
    return 5


class Gl:
    """Glød på kvart oppløsning (billig), blandes inn med «screen»."""
    def __init__(self):
        self.im = Image.new("RGB", (W // 4, H // 4)); self.d = ImageDraw.Draw(self.im)
    def dot(self, x, y, r, col, k=.8):
        for f, kk in ((1.0, .3), (.62, .6), (.3, 1.0)):
            c = tuple(int(v * k * kk) for v in col); rr_ = r * f
            self.d.ellipse(((x - rr_) / 4, (y - rr_) / 4, (x + rr_) / 4, (y + rr_) / 4), fill=c)
    def apply(self, im):
        g = self.im.filter(ImageFilter.GaussianBlur(11)).resize((W, H), Image.BILINEAR)
        return ImageChops.screen(im, g)


def flame(d, g, x, y, s, t, seed=0, k=1.0):
    h = 1 + .12 * math.sin(t * 17 + seed) + .06 * math.sin(t * 29 + seed * 2)
    sw = 4 * s * math.sin(t * 9 + seed)
    tip = (x + sw, y - 62 * s * h)
    d.ellipse((x - 15 * s, y - 32 * s, x + 15 * s, y), fill=(255, 150, 40))
    d.polygon([(x - 14 * s, y - 20 * s), (x + 14 * s, y - 20 * s), tip], fill=(255, 150, 40))
    d.ellipse((x - 8 * s, y - 24 * s, x + 8 * s, y - 2 * s), fill=(255, 232, 150))
    d.polygon([(x - 7 * s, y - 14 * s), (x + 7 * s, y - 14 * s), (x + sw * .6, y - 40 * s * h)], fill=(255, 232, 150))
    g.dot(x, y - 26 * s, 110 * s, (255, 150, 60), .7 * k)


def sparks(d, g, x, y, t0, t):
    a = t - t0
    if not 0 <= a < 1.1: return
    r = random.Random(int(t0 * 10))
    for _ in range(26):
        ang = r.random() * math.tau; sp = r.uniform(60, 230)
        px, py = x + math.cos(ang) * sp * a, y + math.sin(ang) * sp * a + 80 * a * a
        f = 1 - a / 1.1; col = tuple(int(v * f) for v in r.choice((GOLD, (255, 255, 220), (255, 150, 110))))
        s = r.uniform(3, 7) * f + 1
        d.polygon([(px, py - s * 2), (px + s * .6, py - s * .6), (px + s * 2, py), (px + s * .6, py + s * .6), (px, py + s * 2), (px - s * .6, py + s * .6), (px - s * 2, py), (px - s * .6, py - s * .6)], fill=col)
        g.dot(px, py, 22, col, .6)


def snow(d, t):
    for x0, y0, v, r, ph in SNOW:
        x = (x0 + 25 * math.sin(t * .8 + ph)) % W; y = (y0 + v * t) % H
        d.ellipse((x - r, y - r, x + r, y + r), fill=(235, 238, 255))


def strand(d, g, t, all_on=False):
    pts = []
    for i in range(25):
        x = W * i / 24; k = (x % (W / 2)) / (W / 2)
        pts.append((x, 120 + 75 * math.sin(math.pi * k)))
    d.line(pts, fill=(30, 26, 40), width=4)
    for i, (x, y) in enumerate(pts):
        on = t > IGNITE + .35 + i * .055
        y2 = y + 22
        if on:
            b = .8 + .2 * math.sin(t * 4 + i * 1.7); col = tuple(int(c * b) for c in PAL[i % 4])
            g.dot(x, y2, 55, col, .9)
        else: col = (60, 56, 74)
        d.rectangle((x - 4, y2 - 16, x + 4, y2 - 8), fill=(30, 26, 40))
        d.ellipse((x - 10, y2 - 10, x + 10, y2 + 13), fill=col)


def wreath(d, g, t, lit):
    cx, cy, r = W // 2, 960, 330
    for a, off, c in LEAVES:
        x, y = cx + (r + off) * math.cos(a), cy + (r + off) * .55 * math.sin(a)
        d.ellipse((x - 20, y - 15, x + 20, y + 15), fill=c)
    for a in range(0, 360, 24):                           # røde bær
        x, y = cx + r * math.cos(math.radians(a + 7)), cy + r * .55 * math.sin(math.radians(a + 7))
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(200, 40, 50))
    bx, by = cx, cy + r * .55 + 6                          # sløyfe
    d.polygon([(bx, by), (bx - 70, by - 36), (bx - 70, by + 36)], fill=(200, 30, 60))
    d.polygon([(bx, by), (bx + 70, by - 36), (bx + 70, by + 36)], fill=(200, 30, 60))
    d.ellipse((bx - 14, by - 14, bx + 14, by + 14), fill=(150, 20, 45))
    pos = []
    for i in range(4):
        a = math.radians(200 + i * 46)
        x, y = cx + r * math.cos(a) * .95, cy + r * .55 * math.sin(a)
        pos.append((x, y))
        d.rounded_rectangle((x - 20, y - 105, x + 20, y), 6, fill=CREAM)
        d.line((x, y - 105, x, y - 116), fill=(60, 50, 50), width=4)
        if lit[i] is not None and t >= lit[i]:
            flame(d, g, x, y - 112, 1.1, t, i, .9)
    return pos


def lake(d, g, t):
    P.park(d, g.dot, W // 2, 960, 1.0, t, 5.5)
    for t0, fx, fy, col in ((6.9, 190, 760, GOLD), (7.5, 880, 790, (255, 150, 200)), (8.0, 540, 720, (140, 220, 255))):
        a = t - t0
        if 0 <= a < 1.2:
            r = random.Random(int(t0 * 7))
            for _ in range(34):
                ang = r.random() * math.tau; sp = r.uniform(80, 210)
                px, py = fx + math.cos(ang) * sp * a, fy + math.sin(ang) * sp * a + 110 * a * a
                f = 1 - a / 1.2; c = tuple(int(v * f) for v in col)
                d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=c); g.dot(px, py, 26, c, .7)


def church(d, g, t):
    cx, base = W // 2, 1180
    g.dot(cx, 1000, 330, (150, 90, 40), .35 * clamp((t - 8.9) / 1.2))
    d.rectangle((cx - 170, 960, cx + 170, base), fill=DARK)
    d.polygon([(cx - 190, 965), (cx + 190, 965), (cx, 860)], fill=DARK)
    d.rectangle((cx - 40, 790, cx + 40, 965), fill=DARK)
    d.polygon([(cx - 46, 795), (cx + 46, 795), (cx, 690)], fill=DARK)
    for i, wx in enumerate((-120, -20, 80, -20 + 0)):
        if i == 3: continue
        on = clamp((t - (9.0 + i * .3)) / .5)
        col = tuple(int(c * (.35 + .65 * on)) for c in (255, 196, 96))
        d.rounded_rectangle((cx + wx, 1030, cx + wx + 44, 1120), 20, fill=col)
        if on > .5: g.dot(cx + wx + 22, 1075, 70, (255, 170, 70), .5 * on)
    d.ellipse((cx - 18, 845 + 0, cx + 18, 881), fill=(255, 196, 96)) if t > 9.3 else None
    for k in range(7):
        y = 1010 - ((t * 70 + k * 85) % 440)
        if y > 1010 or t < 9.4: continue
        x = cx + (k - 3) * 78 + 26 * math.sin(t * 2 + k)
        f = clamp(1 - abs(y - 800) / 260) if y < 800 else 1.0
        col = tuple(int(v * f) for v in GOLD)
        d.ellipse((x - 14, y - 10, x + 14, y + 10), fill=col); d.line((x + 13, y, x + 13, y - 44), fill=col, width=5)
        d.line((x + 13, y - 44, x + 32, y - 30), fill=col, width=5); g.dot(x, y, 34, col, .5)


def flimmer(d, g, t):
    lit = t >= IGNITE
    cx, by = 215, 1690 + (5 * math.sin(t * 3) if lit else 0)
    if not lit: cx += 2 * math.sin(t * 40)
    d.rounded_rectangle((cx - 75, by - 250, cx + 75, by), 30, fill=CREAM)
    d.rounded_rectangle((cx + 38, by - 240, cx + 75, by - 6), 30, fill=(224, 212, 186))
    d.ellipse((cx - 77, by - 266, cx + 77, by - 234), fill=(255, 250, 238))
    d.ellipse((cx - 60, by - 252, cx - 30, by - 214), fill=(255, 250, 238))        # voksdråpe
    d.line((cx, by - 262, cx, by - 288), fill=(50, 40, 40), width=6)
    if lit: flame(d, g, cx, by - 288, 1.5, t, 7)
    else: g.dot(cx, by - 290, 30, (120, 60, 20), .3)
    gx, gy = (9 * math.sin(t * 2.2), -2) if not lit else (7, -4)
    blink = (t % 3.1) > 2.96
    wink = t > 16.3 and t < 16.9
    for j, ex in enumerate((-28, 28)):
        ey = by - 170
        if blink or (wink and j == 1):
            d.line((cx + ex - 17, ey, cx + ex + 17, ey), fill=(60, 40, 60), width=5)
        else:
            d.ellipse((cx + ex - 22, ey - 24, cx + ex + 22, ey + 24), fill=(255, 255, 255))
            d.ellipse((cx + ex + gx - 11, ey + gy - 12, cx + ex + gx + 11, ey + gy + 12), fill=(30, 20, 50))
            d.ellipse((cx + ex + gx - 5, ey + gy - 9, cx + ex + gx + 1, ey + gy - 3), fill=(255, 255, 255))
    if lit:
        d.arc((cx - 24, by - 148, cx + 24, by - 104), 15, 165, fill=(60, 30, 60), width=6)
        for s in (-52, 52): d.ellipse((cx + s - 13, by - 140, cx + s + 13, by - 122), fill=(255, 170, 170))
    else:
        d.ellipse((cx - 9, by - 128, cx + 9, by - 106), outline=(60, 30, 60), width=5)
        d.ellipse((cx + 62, by - 215, cx + 74, by - 195), fill=(150, 210, 255))       # svettedråpe
    return cx, by


TITLES = [("FØRSTE ADVENT", "Det er mørkt i Ålesund …"), ("29. NOVEMBER", "Nå tenner vi lyset!"),
          ("LØRDAG 28. NOV · GRATIS", "Lysparken i Spjelkavik"), ("SØNDAG 29. NOV · KL. 17", "Adventskonsert i Ålesund kirke"),
          ("OG HOS OSS", "Første lys på kaskjerda.no"), ("NESTE LYS 6. DESEMBER", "Følg oss. Vi lyser opp desember.")]


def bubble_text(sc, t):
    return [("Pssst … er det noen her? Det er så mørkt!"),
            ("Første advent! Er du klar?" if t < IGNITE + .4 else "Der ja! Nå tenner vi Ålesund!"),
            "Fyrverkeri i Spjelkavik kl. 17:45!",
            "Symfoniorkesteret spiller for oss!",
            "Jeg lyser på kaskjerda.no også. Kom innom!",
            "Vi sees, Ålesund!"][sc]


def render(t, sc):
    im = Image.blend(BGD, BG, clamp((t - IGNITE + .2) / 1.0)); d = ImageDraw.Draw(im); g = Gl()
    snow(d, t); strand(d, g, t)
    lit2 = [IGNITE, IGNITE2 if sc == 5 else None, None, None]
    if sc in (0, 1, 4, 5): wreath(d, g, t, lit2)
    elif sc == 2: lake(d, g, t)
    else: church(d, g, t)
    cx, by = flimmer(d, g, t)
    sparks(d, g, cx, by - 300, IGNITE, t)
    if sc == 5: sparks(d, g, 540 + 330 * math.cos(math.radians(246)) * .95, 960 + 330 * .55 * math.sin(math.radians(246)) - 112, IGNITE2, t)
    im = g.apply(im); d = ImageDraw.Draw(im)
    local = t - BOUNDS[sc]; e = back(local / .5); dy = (1 - e) * 70
    lab, title = TITLES[sc]
    d.text((W // 2, 330 + dy), lab, font=M(46), fill=GOLD, anchor="ma")
    f, _, ls = block(d, title, B, (104, 96, 88, 80), W - 120, 2)
    y = 400 + dy
    for l in ls:
        d.text((W // 2, y), l, font=f, fill=(255, 255, 255), anchor="ma"); y += int(f.size * 1.08)
    if sc == 2: d.text((W // 2, 1235), "17:00 konsert · 17:30 lysene tennes · 17:45 fyrverkeri", font=F(36), fill=(230, 220, 255), anchor="ma")
    if sc == 3: d.text((W // 2, 1235), "Nøtteknekkeren og allsang · 105–280 kr", font=M(42), fill=GOLD, anchor="ma")
    if sc == 4: d.text((W // 2, 1250), "Adventskransen på forsiden tennes søndag", font=F(40), fill=(230, 220, 255), anchor="ma")
    if sc == 5:
        lg, mask = logo(120); im.paste(lg, (210, 1205), mask); d = ImageDraw.Draw(im)
        d.text((360, 1215), "kaskjerda.no", font=B(70), fill=(255, 255, 255)); d.text((362, 1295), "lenke i bio", font=F(34), fill=(230, 220, 255))
    bp = back(local / .4) if local > 0 else 0
    by0 = 1370 + (1 - bp) * 40
    f, _, ls = block(d, bubble_text(sc, t), F, (50, 46, 42), 590, 3)
    hh = len(ls) * int(f.size * 1.12) + 56
    d.rounded_rectangle((355, by0, 1020, by0 + hh), 40, fill=(255, 255, 255))
    d.polygon([(358, by0 + hh - 70), (358, by0 + hh - 14), (292, by0 + hh + 18)], fill=(255, 255, 255))
    yy = by0 + 28
    for l in ls:
        d.text((388, yy), l, font=f, fill=(46, 22, 76)); yy += int(f.size * 1.12)
    return im


def frame(t):
    sc = scene_of(t)
    for i in range(1, 6):
        b = BOUNDS[i]
        if abs(t - b) < .18:
            w = (t - (b - .18)) / .36
            return Image.blend(render(t, i - 1), render(t, i), w)
    return render(t, sc)


if __name__ == "__main__":
    if "--stills" in sys.argv:
        ts = (1.2, 3.3, 4.4, 6.4, 7.6, 10.5, 13.0, 16.5)
        sh = Image.new("RGB", (4 * 540, 2 * 960))
        for k, t in enumerate(ts):
            sh.paste(frame(t).resize((540, 960)), ((k % 4) * 540, (k // 4) * 960))
        sh.save("reel-stills.png"); print("stills ok")
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", "advent-reel.mp4"],
                             stdin=subprocess.PIPE)
        for n in range(int(DUR * FPS)):
            p.stdin.write(frame(n / FPS).tobytes())
        p.stdin.close(); p.wait(); print("reel ok")
